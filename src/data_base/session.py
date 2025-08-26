from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.config import settings

# Create an asynchronous SQLAlchemy engine using the database URL from settings
engine = create_async_engine(settings.DATABASE_URL)

# Create an asynchronous session factory
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

async def get_db():
    """
    Dependency generator that provides a SQLAlchemy async session.

    Yields:
        AsyncSession: An instance of the database session.
    Ensures:
        The session is closed after use.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()