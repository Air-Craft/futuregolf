"""
Database migration to add blob name columns for Google Cloud Storage integration.
"""

from sqlalchemy import text
from database.config import engine
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Add blob name columns to videos table."""
    with engine.connect() as conn:
        try:
            # Add blob name columns
            conn.execute(text("""
                ALTER TABLE videos 
                ADD COLUMN IF NOT EXISTS video_blob_name TEXT,
                ADD COLUMN IF NOT EXISTS thumbnail_blob_name TEXT,
                ADD COLUMN IF NOT EXISTS processed_video_url TEXT,
                ADD COLUMN IF NOT EXISTS processed_blob_name TEXT
            """))
            
            conn.commit()
            logger.info("Successfully added blob name columns to videos table")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove blob name columns from videos table."""
    with engine.connect() as conn:
        try:
            # Remove blob name columns
            conn.execute(text("""
                ALTER TABLE videos 
                DROP COLUMN IF EXISTS video_blob_name,
                DROP COLUMN IF EXISTS thumbnail_blob_name,
                DROP COLUMN IF EXISTS processed_video_url,
                DROP COLUMN IF EXISTS processed_blob_name
            """))
            
            conn.commit()
            logger.info("Successfully removed blob name columns from videos table")
            
        except Exception as e:
            logger.error(f"Migration rollback failed: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()