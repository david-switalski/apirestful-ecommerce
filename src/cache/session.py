from typing import AsyncGenerator

from redis.asyncio import ConnectionPool
from redis.asyncio import Redis
from src.core.config import settings

# Create a reusable connection pool for the Redis server.
# This is more efficient than creating a new connection for every request.
# Configuration is loaded from the application's settings.
redis_pool = ConnectionPool(
    username=settings.REDIS_USER,
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    decode_responses=True,  # Automatically decode responses from bytes to strings (UTF-8).
)


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    Dependency injector that provides a Redis client from the connection pool.

    This async generator yields a client for use in a single request and
    ensures that the connection is properly closed afterward.

    Yields:
        Redis: An active asynchronous Redis client.
    """
    client = Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()
