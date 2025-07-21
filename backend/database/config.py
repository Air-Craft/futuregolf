"""
Database configuration for FutureGolf application.
Optimized for Neon PostgreSQL hosting.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool, NullPool
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/futuregolf"
)

# Async database URL (replace postgresql with postgresql+asyncpg)
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Parse DATABASE_URL to detect Neon hosting
parsed_url = urlparse(DATABASE_URL)
is_neon = "neon.tech" in parsed_url.hostname if parsed_url.hostname else False

# Neon-specific configuration
if is_neon:
    logger.info("Detected Neon PostgreSQL hosting - applying optimized settings")
    
    # Neon-optimized engine settings
    engine_kwargs = {
        "url": DATABASE_URL,
        "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),  # 30 minutes
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),  # Smaller pool for Neon
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),  # Conservative overflow
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),  # 30 seconds timeout
        "connect_args": {
            "sslmode": "require",
            "connect_timeout": 10,
            "command_timeout": 60,
            "server_settings": {
                "jit": "off",  # Disable JIT for better cold start performance
                "statement_timeout": "60000",  # 60 seconds
                "lock_timeout": "30000",  # 30 seconds
                "idle_in_transaction_session_timeout": "300000",  # 5 minutes
            }
        }
    }
    
    # Use NullPool for serverless environments if needed
    if os.getenv("USE_NULL_POOL", "false").lower() == "true":
        engine_kwargs["poolclass"] = NullPool
        logger.info("Using NullPool for serverless environment")
    
else:
    # Standard PostgreSQL configuration
    logger.info("Using standard PostgreSQL configuration")
    
    engine_kwargs = {
        "url": DATABASE_URL,
        "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "300")),  # 5 minutes
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "40")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    }

# Create SQLAlchemy engine
engine = create_engine(**engine_kwargs)

# Create async engine
async_engine_kwargs = engine_kwargs.copy()
async_engine_kwargs["url"] = ASYNC_DATABASE_URL
async_engine = create_async_engine(**async_engine_kwargs)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async session class
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine
)

# Create Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db_session():
    """
    Dependency to get async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_async_session():
    """
    Context manager to get async database session.
    """
    return AsyncSessionLocal()

def init_db():
    """
    Initialize database tables.
    """
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

def drop_db():
    """
    Drop all database tables.
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped.")