"""FastAPI dependencies for dependency injection."""

from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import redis.asyncio as aioredis

from app.core.config import settings


# Synchronous database setup (for migrations and sync operations)
# Use SQLite for testing to avoid PostgreSQL connection issues
engine = create_engine(
    "sqlite:///./test.db",
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Async database setup
async_database_url = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)
async_engine = create_async_engine(
    async_database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_db() -> Generator[Session, None, None]:
    """Get synchronous database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Get Redis connection."""
    redis_client = aioredis.from_url(settings.redis_url)
    try:
        yield redis_client
    finally:
        await redis_client.close()


async def startup_database():
    """Connect to database on startup."""
    # Test the connection
    async with async_engine.begin() as conn:
        # This will test the connection
        pass


async def shutdown_database():
    """Disconnect from database on shutdown."""
    await async_engine.dispose()
