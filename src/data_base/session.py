from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.config import settings

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = async_sessionmaker(autocommit = False, autoflush = False, bind = engine)   

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()