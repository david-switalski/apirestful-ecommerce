import asyncio  
import pytest  
from typing import AsyncGenerator, Generator 

from fastapi.testclient import TestClient 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool 

from alembic.config import Config
from alembic import command

from src.main import app  
from src.data_base.dependencies import get_db 

import os
from dotenv import load_dotenv

load_dotenv()

db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_name = os.getenv("POSTGRES_DB")

db_host = "localhost"
db_port = "5432"

TEST_DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/test_{db_name}"

MAINTENANCE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/postgres"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an asyncio event loop for the entire test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Creates and destroys the test database for the entire session.
    """
    engine = create_async_engine(MAINTENANCE_URL, poolclass=NullPool)

    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT").execute(
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'test_{db_name}'"
        )
        await conn.execution_options(isolation_level="AUTOCOMMIT").execute(
            f"DROP DATABASE IF EXISTS test_{db_name}"
        )
        await conn.execution_options(isolation_level="AUTOCOMMIT").execute(
            f"CREATE DATABASE test_{db_name}"
        )
    await engine.dispose()

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    
    command.upgrade(alembic_cfg, "head")

    yield
    
    engine = create_async_engine(MAINTENANCE_URL, poolclass=NullPool)
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT").execute(
            f"DROP DATABASE IF EXISTS test_{db_name}"
        )
    await engine.dispose()
    
@pytest.fixture(scope="function")
async def db_session(setup_test_database: None) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a clean test database session for each test.

    Connects to the test database, initiates a transaction, and rolls back at the end to ensure isolation between tests.
    """
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    async with engine.connect() as connection:
        
        trans = await connection.begin()

        SessionTest = async_sessionmaker(bind=connection, expire_on_commit=False)
        session = SessionTest()

        yield session

        await session.close()

        await trans.rollback()

    await engine.dispose()
    
@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI TestClient that uses the test database session.

    This is the main fixture for API testing.
    """
    
    def override_get_db() -> Generator[AsyncSession, None, None]:
        """   
        Fake dependency function.
        Returns the test session prepared by the 'db_session' fixture.
        """
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
       
        yield test_client

    app.dependency_overrides.clear()