from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.database_models import Base
from config.settings import settings
from typing import AsyncGenerator
import os

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.LOG_LEVEL.lower() == "debug",  # Log SQL queries in debug mode
    future=True
)

# Create async session factory
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_database():
    """Initialize database on startup"""
    await create_tables()
    print("Database initialized successfully") 
    