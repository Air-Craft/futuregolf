#!/usr/bin/env python3
"""
Setup script for Neon database.
This script will create the database tables using our SQLAlchemy models.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Load environment variables
load_dotenv()

def setup_database():
    """Set up Neon database with all required tables."""
    print("🚀 FutureGolf - Neon Database Setup")
    print("=" * 50)
    
    # Check for database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url or database_url == "postgresql://username:password@host/database":
        print("\n❌ DATABASE_URL not configured in .env file")
        print("\nPlease update your .env file with the Neon database URL.")
        print("It should look like:")
        print("DATABASE_URL=postgresql://username:password@host.neon.tech:5432/database?sslmode=require")
        return False
    
    print(f"\n✅ Database URL found")
    print(f"   Connecting to: {database_url.split('@')[1].split('/')[0]}...")
    
    try:
        # Import database components
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        from database.config import Base
        from models.user import User
        from models.video import Video
        from models.video_analysis import VideoAnalysis
        from models.subscription import Subscription, Payment, UsageRecord
        
        print("\n📦 Creating database engine...")
        engine = create_engine(database_url)
        
        # Test connection
        print("🔌 Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version}")
        
        # Create all tables
        print("\n📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """))
            tables = [row[0] for row in result]
            
            print(f"\n📋 Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
        
        # Create test session
        print("\n🧪 Testing database operations...")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Count existing users
        user_count = session.query(User).count()
        print(f"✅ Database operations working (found {user_count} users)")
        
        session.close()
        
        print("\n✅ Neon database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error setting up database: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Provide specific help for common errors
        if "could not connect" in str(e).lower():
            print("\n💡 Connection Tips:")
            print("1. Check your DATABASE_URL format")
            print("2. Ensure the database exists in Neon")
            print("3. Verify your connection string includes ?sslmode=require")
            print("4. Check that your IP is allowed in Neon settings")
        elif "permission denied" in str(e).lower():
            print("\n💡 Permission Tips:")
            print("1. Ensure your database user has CREATE TABLE permissions")
            print("2. Check that the database exists and you have access")
        
        return False

def create_sample_data():
    """Create some sample data for testing."""
    print("\n📝 Would you like to create sample data? (y/n): ", end='')
    response = input().strip().lower()
    
    if response != 'y':
        print("Skipping sample data creation.")
        return
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models.user import User
        from datetime import datetime
        
        database_url = os.getenv("DATABASE_URL")
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test user
        test_user = User(
            email="test@futuregolf.com",
            name="Test User",
            email_verified=True,
            created_at=datetime.utcnow()
        )
        test_user.set_password("testpassword123")
        
        session.add(test_user)
        session.commit()
        
        print(f"✅ Created test user: {test_user.email}")
        session.close()
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

def main():
    """Run database setup."""
    success = setup_database()
    
    if success:
        create_sample_data()
        
        print("\n🎉 Database is ready for use!")
        print("\nNext steps:")
        print("1. Start the FastAPI server: python start_server.py")
        print("2. Access the API docs at: http://localhost:8000/docs")
        print("3. Begin Phase 2 development!")
    else:
        print("\n❌ Database setup failed. Please fix the issues and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()