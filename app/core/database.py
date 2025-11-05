"""Database configuration and session management using asyncpg"""

import asyncpg
from app.config import settings


async def get_db():
    """Dependency for getting database connection from pool"""
    from app.dependency import db
    if db is None:
        raise RuntimeError("Database not configured")
    async with db.pool.acquire() as connection:
        try:
            yield connection
        finally:
            await connection.close()


async def init_db():
    """Initialize database tables if needed"""
    # For asyncpg, we typically don't need table initialization like SQLAlchemy
    # since we're connecting to an existing PostgreSQL database
    print("Database connection established using asyncpg")
    print("Database URL:", settings.asyncpg_dsn)


async def close_db():
    """Close database connections - handled by ConfigureAsyncpg"""
    # Connection pool cleanup is handled by ConfigureAsyncpg.on_disconnect
    pass
