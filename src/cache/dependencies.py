from typing import Annotated
from fastapi import Depends
from redis.asyncio import Redis
from src.cache.session import get_redis_client

Redis_session = Annotated[Redis, Depends(get_redis_client)]