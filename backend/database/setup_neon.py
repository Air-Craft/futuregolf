#!/usr/bin/env python3
"""
Quick setup script for Neon PostgreSQL database.
This script automates the database setup process.
"""

import os
import sys
import subprocess
from pathlib import Path
import logging
from urllib.parse import urlparse

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are installed."""
    logger.info("Checking dependencies...")
    
    required_packages = [
        'sqlalchemy',
        'psycopg2-binary',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error("Please install them with: pip install " + " ".join(missing_packages))
        return False
    
    logger.info("All dependencies are installed.")
    return True


def get_database_url():
    """Get database URL from user input or environment."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.info("DATABASE_URL not found in environment.")
        print("\nPlease enter your Neon database connection string.")
        print("It should look like: postgresql://username:password@host.neon.tech:5432/database?sslmode=require")
        
        while True:
            database_url = input("\nDatabase URL: ").strip()
            
            if not database_url:
                logger.error("Database URL cannot be empty.")
                continue
            
            # Basic validation
            try:
                parsed = urlparse(database_url)
                if not parsed.scheme == 'postgresql':
                    logger.error("URL must start with 'postgresql://'")
                    continue
                
                if not parsed.hostname:
                    logger.error("Invalid hostname in URL")
                    continue
                
                break
            except Exception as e:
                logger.error(f"Invalid URL format: {e}")
                continue
    
    return database_url


def create_env_file(database_url):
    """Create production environment file."""
    logger.info("Creating production environment file...")
    
    env_file = backend_dir / ".env.production"
    
    if env_file.exists():
        response = input(f"\n{env_file} already exists. Overwrite? (y/n): ").lower()
        if response != 'y':
            logger.info("Skipping environment file creation.")
            return True
    
    # Generate a secure secret key
    import secrets
    secret_key = secrets.token_urlsafe(32)
    
    env_content = f"""# Neon PostgreSQL Database Configuration for FutureGolf
DATABASE_URL={database_url}

# Neon-optimized settings
SQL_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# JWT Configuration
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
DEBUG=false
ENVIRONMENT=production
PORT=8000

# CORS Configuration (update with your frontend domain)
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Add your other configuration here as needed
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        logger.info(f"Created environment file: {env_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to create environment file: {e}")
        return False


def test_connection(database_url):
    """Test database connection."""
    logger.info("Testing database connection...")
    
    # Set environment variable temporarily
    os.environ["DATABASE_URL"] = database_url
    
    try:
        from database.config import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("Database connection successful!")
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def initialize_database():
    """Initialize the database with tables and indexes."""
    logger.info("Initializing database...")
    
    try:
        from database.init_db import init_database
        
        if init_database():
            logger.info("Database initialized successfully!")
            return True
        else:
            logger.error("Database initialization failed!")
            return False
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def run_tests():
    """Run database tests."""
    logger.info("Running database tests...")
    
    try:
        from database.test_db import DatabaseTester
        
        with DatabaseTester() as tester:
            success = tester.run_all_tests()
            
        if success:
            logger.info("All database tests passed!")
            return True
        else:
            logger.error("Some database tests failed!")
            return False
            
    except Exception as e:
        logger.error(f"Database tests failed: {e}")
        return False


def setup_migrations():
    """Set up database migrations."""
    logger.info("Setting up database migrations...")
    
    try:
        from database.migrations import create_initial_migration
        
        if create_initial_migration():
            logger.info("Database migrations set up successfully!")
            return True
        else:
            logger.error("Database migrations setup failed!")
            return False
            
    except Exception as e:
        logger.error(f"Database migrations setup failed: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("FutureGolf Neon PostgreSQL Database Setup")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Get database URL
    database_url = get_database_url()
    
    # Create environment file
    if not create_env_file(database_url):
        sys.exit(1)
    
    # Test connection
    if not test_connection(database_url):
        logger.error("Please check your database URL and try again.")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        logger.warning("Some tests failed, but setup may still be usable.")
    
    # Set up migrations
    if not setup_migrations():
        logger.warning("Migrations setup failed, but database is still usable.")
    
    print("\n" + "=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update .env.production with your actual frontend domain")
    print("2. Configure your FastAPI application to use the database")
    print("3. Set up authentication and authorization")
    print("4. Deploy your application")
    print("\nFor more information, see database/NEON_SETUP.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed with unexpected error: {e}")
        sys.exit(1)