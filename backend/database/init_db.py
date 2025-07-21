"""
Database initialization script for FutureGolf application.
This script creates all database tables based on the defined models.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.config import engine, Base, logger
from models import User, Video, VideoAnalysis, Subscription, Payment, UsageRecord
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)


def create_database_extensions():
    """Create required PostgreSQL extensions."""
    logger.info("Creating PostgreSQL extensions...")
    
    extensions = [
        "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",
        "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";",
    ]
    
    with engine.connect() as conn:
        for extension in extensions:
            try:
                conn.execute(text(extension))
                logger.info(f"Successfully created extension: {extension}")
            except Exception as e:
                logger.warning(f"Could not create extension {extension}: {e}")
        conn.commit()


def create_indexes():
    """Create additional indexes for better performance."""
    logger.info("Creating additional database indexes...")
    
    indexes = [
        # User indexes
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);",
        "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);",
        
        # Video indexes
        "CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);",
        "CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_videos_user_status ON videos(user_id, status);",
        
        # Video Analysis indexes
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_user_id ON video_analyses(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_video_id ON video_analyses(video_id);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_status ON video_analyses(status);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_created_at ON video_analyses(created_at);",
        
        # Subscription indexes
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);",
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);",
        
        # Payment indexes
        "CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON payments(subscription_id);",
        "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);",
        "CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);",
        
        # Usage Record indexes
        "CREATE INDEX IF NOT EXISTS idx_usage_records_user_id ON usage_records(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_usage_records_subscription_id ON usage_records(subscription_id);",
        "CREATE INDEX IF NOT EXISTS idx_usage_records_billing_period ON usage_records(billing_period_start, billing_period_end);",
    ]
    
    with engine.connect() as conn:
        for index in indexes:
            try:
                conn.execute(text(index))
                logger.info(f"Successfully created index: {index.split()[5]}")
            except Exception as e:
                logger.warning(f"Could not create index {index}: {e}")
        conn.commit()


def init_database():
    """Initialize the database with all tables and configurations."""
    logger.info("Starting database initialization...")
    
    try:
        # Create extensions
        create_database_extensions()
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
        
        # Create additional indexes
        create_indexes()
        
        logger.info("Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def drop_database():
    """Drop all database tables."""
    logger.warning("Dropping all database tables...")
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        return False


def check_database_connection():
    """Check if database connection is working."""
    logger.info("Testing database connection...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("Database connection successful!")
            return True
            
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def show_table_info():
    """Show information about created tables."""
    logger.info("Database table information:")
    
    try:
        with engine.connect() as conn:
            # Get table names
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            
            for table in tables:
                table_name = table[0]
                logger.info(f"Table: {table_name}")
                
                # Get column information
                result = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    logger.info(f"  - {col[0]}: {col[1]} {nullable}{default}")
                
                logger.info("")
                
    except Exception as e:
        logger.error(f"Failed to show table info: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FutureGolf Database Management")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--drop", action="store_true", help="Drop all tables")
    parser.add_argument("--check", action="store_true", help="Check database connection")
    parser.add_argument("--info", action="store_true", help="Show table information")
    
    args = parser.parse_args()
    
    if args.check:
        if check_database_connection():
            sys.exit(0)
        else:
            sys.exit(1)
    
    if args.drop:
        if drop_database():
            logger.info("Database dropped successfully.")
        else:
            logger.error("Failed to drop database.")
            sys.exit(1)
    
    if args.init:
        if init_database():
            logger.info("Database initialized successfully.")
        else:
            logger.error("Failed to initialize database.")
            sys.exit(1)
    
    if args.info:
        show_table_info()
    
    if not any(vars(args).values()):
        # Default action: initialize database
        if init_database():
            logger.info("Database initialized successfully.")
        else:
            logger.error("Failed to initialize database.")
            sys.exit(1)