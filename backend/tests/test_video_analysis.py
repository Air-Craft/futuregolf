"""
Test script for video analysis functionality.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.video_analysis_service import get_video_analysis_service
from database.config import get_db_session
from models.video import Video
from models.user import User
from models.video_analysis import VideoAnalysis, AnalysisStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_video_analysis():
    """Test the video analysis functionality."""
    
    # Initialize service
    try:
        service = get_video_analysis_service()
    except Exception as e:
        logger.error(f"Failed to initialize video analysis service: {e}")
        logger.info("This is expected if Google Cloud credentials are not configured.")
        service = None
    
    if service:
        # Test loading coaching prompt
        logger.info("Testing coaching prompt loading...")
        try:
            prompt = await service._load_coaching_prompt()
            logger.info(f"Loaded coaching prompt: {len(prompt)} characters")
        except Exception as e:
            logger.error(f"Failed to load coaching prompt: {e}")
        
        # Test mock analysis generation
        logger.info("Testing mock analysis generation...")
        try:
            mock_analysis = await service._generate_mock_analysis()
            logger.info(f"Generated mock analysis: {mock_analysis.keys()}")
            logger.info(f"Mock analysis score: {mock_analysis.get('overall_score')}")
        except Exception as e:
            logger.error(f"Failed to generate mock analysis: {e}")
    else:
        logger.info("Skipping service tests due to initialization failure")
    
    # Test Gemini availability
    logger.info("Testing Gemini availability...")
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your-gemini-api-key-here":
            logger.info("Gemini API key configured")
            genai.configure(api_key=api_key)
            models = genai.list_models()
            logger.info(f"Available models: {[m.name for m in models]}")
        else:
            logger.warning("Gemini API key not configured - will use mock analysis")
    except ImportError:
        logger.warning("Gemini not available - will use mock analysis")
    except Exception as e:
        logger.error(f"Gemini configuration error: {e}")
    
    # Test video file existence
    test_video_path = Path(__file__).parent / "tests" / "test_video.mov"
    if test_video_path.exists():
        logger.info(f"Test video found: {test_video_path} ({test_video_path.stat().st_size} bytes)")
    else:
        logger.warning(f"Test video not found: {test_video_path}")
    
    # Test database connection
    logger.info("Testing database connection...")
    try:
        from database.config import get_async_session
        async with get_async_session() as session:
            # Test basic query
            from sqlalchemy import select
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if user:
                logger.info(f"Database connection successful. Found user: {user.email}")
            else:
                logger.info("Database connection successful. No users found.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    logger.info("Video analysis test completed!")


if __name__ == "__main__":
    asyncio.run(test_video_analysis())