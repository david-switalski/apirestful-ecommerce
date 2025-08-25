import asyncio
import pytest
import os

from typing import AsyncGenerator
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from alembic.config import Config
from alembic import command

from src.main import app
from src.data_base.dependencies import get_db

load_dotenv()

db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_name = os.getenv("POSTGRES_DB")
db_host = "localhost"
db_port = "5432"

TEST_DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/test_{db_name}"
MAINTENANCE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/postgres"

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    engine = create_async_engine(MAINTENANCE_URL, poolclass=NullPool)

    async with engine.connect() as conn:
        autocommit_conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        
        await autocommit_conn.execute(
            text(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'test_{db_name}'")
        )
        await autocommit_conn.execute(text(f'DROP DATABASE IF EXISTS "test_{db_name}"'))
        await autocommit_conn.execute(text(f'CREATE DATABASE "test_{db_name}"'))

    await engine.dispose()

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,  
        command.upgrade,
        alembic_cfg,
        "head"
    )

    yield

    engine = create_async_engine(MAINTENANCE_URL, poolclass=NullPool)
    async with engine.connect() as conn:
        autocommit_conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        await autocommit_conn.execute(text(f'DROP DATABASE IF EXISTS "test_{db_name}"'))
        
    await engine.dispose()

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]: 
    async with db_engine.connect() as connection:
        trans = await connection.begin()
        SessionTest = async_sessionmaker(bind=connection, expire_on_commit=False)
        session = SessionTest()
        yield session
        await session.close()
        await trans.rollback()
        
@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncSession:
        return db_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()