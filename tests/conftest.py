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
from src.models.users import User as UserModel
from src.services.authentication.service import get_password_hash

# Load environment variables from .env file
load_dotenv()

db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_name = os.getenv("POSTGRES_DB")
db_host = "localhost"
db_port = "5432"

# URLs for test and maintenance databases
TEST_DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/test_{db_name}"
MAINTENANCE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/postgres"

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Session-scoped fixture to set up and tear down the test database.
    Drops and recreates the test database before the test session starts,
    applies migrations, and drops the database after the session ends.
    """
    engine = create_async_engine(MAINTENANCE_URL, poolclass=NullPool)

    async with engine.connect() as conn:
        autocommit_conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # Terminate all connections to the test database and drop it if exists
        await autocommit_conn.execute(
            text(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'test_{db_name}'")
        )
        await autocommit_conn.execute(text(f'DROP DATABASE IF EXISTS "test_{db_name}"'))
        await autocommit_conn.execute(text(f'CREATE DATABASE "test_{db_name}"'))

    await engine.dispose()

    # Run Alembic migrations on the new test database
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

    # Drop the test database after the session
    engine = create_async_engine(MAINTENANCE_URL, poolclass=NullPool)
    async with engine.connect() as conn:
        autocommit_conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        await autocommit_conn.execute(text(f'DROP DATABASE IF EXISTS "test_{db_name}"'))
        
    await engine.dispose()

@pytest.fixture(scope="session")
async def db_engine():
    """
    Session-scoped fixture to provide an async SQLAlchemy engine for the test database.
    """
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]: 
    """
    Function-scoped fixture to provide a transactional async database session.
    Rolls back the transaction after each test for isolation.
    """
    async with db_engine.connect() as connection:
        trans = await connection.begin()
        SessionTest = async_sessionmaker(bind=connection, expire_on_commit=False)
        session = SessionTest()
        yield session
        await session.close()
        await trans.rollback()
        
@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Function-scoped fixture to provide an HTTPX AsyncClient with the test app and overridden DB dependency.
    """
    async def override_get_db() -> AsyncSession:
        return db_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()
    

@pytest.fixture(scope="function")
def test_user_credentials() -> dict:
    """
    Fixture that returns credentials for a test user.
    """
    return {"username": "testuser", "password": "Password123$"}  # pragma: allowlist secret

@pytest.fixture(scope="function")
async def created_test_user(client: AsyncClient, test_user_credentials: dict) -> dict:
    """
    Fixture that creates a test user using the API and returns the user data.
    """
    response = await client.post("/users/", json=test_user_credentials)
    assert response.status_code == 200
    return response.json()

@pytest.fixture(scope="function")
async def authenticated_user_client(client: AsyncClient, created_test_user: dict, test_user_credentials: dict) -> AsyncClient:
    """
    Fixture that returns an authenticated client for the test user.
    """
    login_data = {
        "username": test_user_credentials["username"],
        "password": test_user_credentials["password"],
    }
    response = await client.post("/users/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    client.headers["Authorization"] = f"Bearer {token}"
    return client

@pytest.fixture(scope="function")
async def authenticated_admin_client(client: AsyncClient, db_session: AsyncSession) -> AsyncClient:
    """
    Fixture that creates an admin user, authenticates, and returns an authenticated client.
    """
    admin_username = "adminuser"
    admin_password = "AdminPassword123$"  # pragma: allowlist secret
    
    hashed_password = await get_password_hash(admin_password)
    admin_user = UserModel(
        username=admin_username,
        hashed_password=hashed_password,
        role="admin"
    )
    db_session.add(admin_user)
    await db_session.commit()

    login_data = {"username": admin_username, "password": admin_password}
    response = await client.post("/users/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    client.headers["Authorization"] = f"Bearer {token}"
    return client