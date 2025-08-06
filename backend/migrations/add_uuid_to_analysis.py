"""
Migration script to add UUID and new fields to video_analyses table.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text
import uuid

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Load environment variables
load_dotenv()

from app.database.config import AsyncSessionLocal


async def run_migration():
    """Run migration to add UUID and new fields to video_analyses table."""
    async with AsyncSessionLocal() as session:
        try:
            print("Starting migration: Adding UUID and new fields to video_analyses table...")
            
            # Add UUID column if it doesn't exist
            await session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'video_analyses' AND column_name = 'uuid'
                    ) THEN
                        ALTER TABLE video_analyses 
                        ADD COLUMN uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid();
                        
                        CREATE INDEX ix_video_analyses_uuid ON video_analyses(uuid);
                    END IF;
                END $$;
            """))
            
            # Add original_video_url column if it doesn't exist
            await session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'video_analyses' AND column_name = 'original_video_url'
                    ) THEN
                        ALTER TABLE video_analyses 
                        ADD COLUMN original_video_url TEXT;
                    END IF;
                END $$;
            """))
            
            # Add processed_video_url_new column if it doesn't exist
            await session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'video_analyses' AND column_name = 'processed_video_url_new'
                    ) THEN
                        ALTER TABLE video_analyses 
                        ADD COLUMN processed_video_url_new TEXT;
                    END IF;
                END $$;
            """))
            
            # Add error_description column if it doesn't exist
            await session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'video_analyses' AND column_name = 'error_description'
                    ) THEN
                        ALTER TABLE video_analyses 
                        ADD COLUMN error_description TEXT;
                    END IF;
                END $$;
            """))
            
            # Add analysis_json column if it doesn't exist
            await session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'video_analyses' AND column_name = 'analysis_json'
                    ) THEN
                        ALTER TABLE video_analyses 
                        ADD COLUMN analysis_json JSONB;
                    END IF;
                END $$;
            """))
            
            # Make video_id nullable for two-step flow
            await session.execute(text("""
                ALTER TABLE video_analyses 
                ALTER COLUMN video_id DROP NOT NULL;
            """))
            
            # Update existing records to have UUIDs if they don't have them
            await session.execute(text("""
                UPDATE video_analyses 
                SET uuid = gen_random_uuid() 
                WHERE uuid IS NULL;
            """))
            
            # Note: We need to handle enum updates separately
            # The new enum values are added in the model but existing DB may have old values
            # For now, we'll leave existing status values as-is since we support both
            
            await session.commit()
            print("✅ Migration completed successfully!")
            
            # Verify the changes
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'video_analyses'
                AND column_name IN ('uuid', 'original_video_url', 'processed_video_url_new', 
                                   'error_description', 'analysis_json', 'video_id')
                ORDER BY column_name;
            """))
            
            print("\nVerification - New/Modified columns:")
            for row in result:
                print(f"  - {row.column_name}: {row.data_type} (nullable: {row.is_nullable})")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(run_migration())