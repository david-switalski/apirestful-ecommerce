import asyncio
import pytest
import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
import redis.asyncio as redis

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from alembic.config import Config
from alembic import command

from src.main import app
from src.data_base.dependencies import get_db
from src.cache.session import get_redis_client
from src.models.users import User as UserModel
from src.models.products import Product as ProductModel
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

# REDIS TEST SETUP
TEST_REDIS_HOST = "localhost"
TEST_REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
TEST_REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
TEST_REDIS_DB = int(os.getenv("REDIS_DB", 1)) # Use DB 1 for testing to isolate from dev DB 0


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Session-scoped fixture to create and tear down the test database and migrations.
    """
    engine = create_async_engine(MAINTENANCE_URL, poolclass=NullPool)
    async with engine.connect() as conn:
        autocommit_conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        await autocommit_conn.execute(text(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'test_{db_name}'"))
        await autocommit_conn.execute(text(f'DROP DATABASE IF EXISTS "test_{db_name}"'))
        await autocommit_conn.execute(text(f'CREATE DATABASE "test_{db_name}"'))
    await engine.dispose()

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, command.upgrade, alembic_cfg, "head")

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
async def test_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """
    Function-scoped fixture to provide a Redis client for tests.
    Flushes the test Redis DB after each test for isolation.
    """
    client = redis.Redis(
        host=TEST_REDIS_HOST,
        port=TEST_REDIS_PORT,
        password=TEST_REDIS_PASSWORD,
        db=TEST_REDIS_DB,
        decode_responses=True
    )
    assert await client.ping(), "Redis server is not available"
    yield client
    await client.flushdb()
    await client.close()

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession, test_redis_client: redis.Redis) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture to provide an HTTPX AsyncClient with overridden DB and Redis dependencies.
    """
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_redis_client() -> AsyncGenerator[redis.Redis, None]:
        yield test_redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis_client
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()

# USER AND AUTH FIXTURES

@pytest.fixture(scope="function")
def test_user_credentials() -> dict:
    return {"username": "testuser", "password": "Password123$"} # pragma: allowlist secret

@pytest.fixture(scope="function")
async def created_test_user(client: AsyncClient, test_user_credentials: dict) -> dict:
    response = await client.post("/users/", json=test_user_credentials)
    assert response.status_code == 201
    return response.json()

@pytest.fixture(scope="function")
async def authenticated_user_client(client: AsyncClient, created_test_user: dict, test_user_credentials: dict) -> AsyncClient:
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
    admin_username = "adminuser"
    admin_password = "AdminPassword123$" # pragma: allowlist secret
    
    hashed_password = await get_password_hash(admin_password)
    admin_user = UserModel(username=admin_username, hashed_password=hashed_password, role="admin")
    db_session.add(admin_user)
    await db_session.commit()

    login_data = {"username": admin_username, "password": admin_password}
    response = await client.post("/users/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client

# PRODUCT FIXTURES

@pytest.fixture
async def product_in_db(db_session: AsyncSession) -> ProductModel:
    product = ProductModel(
        name="Test Product",
        category="Tests",
        price=10.00,
        stock=20,
        description="A product for testing."
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product

@pytest.fixture
async def another_product_in_db(db_session: AsyncSession) -> ProductModel:
    product = ProductModel(
        name="Another Test Product",
        category="Tests",
        price=5.50,
        stock=15,
        description="Another product for testing."
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product