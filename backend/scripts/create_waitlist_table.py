#!/usr/bin/env python3
"""
Script to create the waitlist table in the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from models.waitlist import WaitlistEntry
from models.base import Base
from dotenv import load_dotenv

load_dotenv()

def create_waitlist_table():
    """Create the waitlist table if it doesn't exist"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in environment variables")
        return False
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Create only the waitlist table
        WaitlistEntry.__table__.create(engine, checkfirst=True)
        
        print("✅ Waitlist table created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating waitlist table: {str(e)}")
        return False

if __name__ == "__main__":
    create_waitlist_table()