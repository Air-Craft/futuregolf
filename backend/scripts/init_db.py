#!/usr/bin/env python3
"""
Database initialization script for FutureGolf application.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.config import init_db, drop_db, engine, Base
from models import User, Video, VideoAnalysis, Subscription, Payment, UsageRecord
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_extensions():
    """Create required PostgreSQL extensions."""
    try:
        with engine.connect() as conn:
            # Create UUID extension for generating UUIDs
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            
            # Create extension for full-text search if needed
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\""))
            
            conn.commit()
            logger.info("PostgreSQL extensions created successfully")
    except Exception as e:
        logger.error(f"Error creating extensions: {e}")
        raise


def create_indexes():
    """Create additional database indexes for performance."""
    try:
        with engine.connect() as conn:
            # User indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_email_active 
                ON users(email) WHERE is_active = true
            """))
            
            # Video indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_videos_user_status 
                ON videos(user_id, status) WHERE deleted_at IS NULL
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_videos_created_at 
                ON videos(created_at DESC)
            """))
            
            # Video analysis indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_analyses_user_status 
                ON video_analyses(user_id, status)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_analyses_video_id 
                ON video_analyses(video_id)
            """))
            
            # Subscription indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status 
                ON subscriptions(user_id, status)
            """))
            
            # Usage records indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_usage_records_user_period 
                ON usage_records(user_id, billing_period_start, billing_period_end)
            """))
            
            conn.commit()
            logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise


def create_sample_data():
    """Create sample data for development."""
    from datetime import datetime, timedelta
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if sample data already exists
        if session.query(User).filter_by(email="admin@futuregolf.com").first():
            logger.info("Sample data already exists, skipping creation")
            return
        
        # Create sample admin user
        admin_user = User(
            email="admin@futuregolf.com",
            first_name="Admin",
            last_name="User",
            is_verified=True,
            subscription_tier="pro",
            trial_analysis_limit=999,
            monthly_video_minutes_limit=3600  # 60 hours for admin
        )
        
        # Create sample trial user
        trial_user = User(
            email="trial@futuregolf.com",
            first_name="Trial",
            last_name="User",
            is_verified=True,
            subscription_tier="trial"
        )
        
        session.add(admin_user)
        session.add(trial_user)
        session.commit()
        
        # Create sample subscription for admin user
        admin_subscription = Subscription(
            user_id=admin_user.id,
            tier="pro",
            status="active",
            price=29.99,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            monthly_video_limit=60,
            auto_renew=True
        )
        
        session.add(admin_subscription)
        session.commit()
        
        logger.info("Sample data created successfully")
        logger.info(f"Admin user created: {admin_user.email}")
        logger.info(f"Trial user created: {trial_user.email}")
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Main initialization function."""
    logger.info("Starting database initialization...")
    
    try:
        # Create PostgreSQL extensions
        create_extensions()
        
        # Initialize database tables
        init_db()
        
        # Create additional indexes
        create_indexes()
        
        # Create sample data if in development mode
        if os.getenv("ENVIRONMENT", "development") == "development":
            create_sample_data()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


def reset_database():
    """Reset the database by dropping and recreating all tables."""
    logger.warning("Resetting database...")
    
    try:
        # Drop all tables
        drop_db()
        
        # Recreate tables
        init_db()
        
        # Create indexes
        create_indexes()
        
        # Create sample data
        if os.getenv("ENVIRONMENT", "development") == "development":
            create_sample_data()
        
        logger.info("Database reset completed successfully!")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize FutureGolf database")
    parser.add_argument("--reset", action="store_true", help="Reset database (drop and recreate)")
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    else:
        main()