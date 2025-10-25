from typing import Annotated
from fastapi import Depends
from redis.asyncio import Redis
from src.cache.session import get_redis_client


# Dependency that provides an asynchronous Redis client session.
# This Annotated type can be used in endpoint functions to get a Redis connection.
Redis_session = Annotated[Redis, Depends(get_redis_client)]