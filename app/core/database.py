"""Database configuration and session management"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    print("database informaton : ", settings.DATABASE_URL)
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
