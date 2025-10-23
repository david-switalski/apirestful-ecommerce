from typing import AsyncGenerator
from redis.asyncio import ConnectionPool, Redis
from src.core.config import settings

redis_pool = ConnectionPool(
    host=settings.REDIS_HOST,  
    port=settings.REDIS_PORT,  
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,  
    decode_responses=True 
)

async def get_redis_client() -> AsyncGenerator[Redis, None]:
    client = Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()
        