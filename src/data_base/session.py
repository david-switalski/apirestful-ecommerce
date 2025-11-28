from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings

# Create an asynchronous SQLAlchemy engine using the database URL from settings
engine = create_async_engine(settings.DATABASE_URL)

# Create an asynchronous session factory
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator that provides a SQLAlchemy asynchronous session.

    Yields:
        AsyncSession: An active asynchronous database session for use in FastAPI dependencies.

    This function ensures that the session is properly opened and closed
    for each request, maintaining database connection integrity.
    """
    async with SessionLocal() as session:
        async with session.begin():
            yield session
