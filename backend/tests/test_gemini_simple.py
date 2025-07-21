"""
Simple test for Gemini AI integration.
"""

import os
import asyncio
import tempfile
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_gemini_simple():
    """Test basic Gemini functionality."""
    
    # Test file loading
    logger.info("Testing coaching prompt loading...")
    try:
        prompt_path = Path(__file__).parent / "prompts" / "video_analysis_swing_coaching.txt"
        if prompt_path.exists():
            with open(prompt_path, 'r') as f:
                prompt = f.read()
            logger.info(f"Loaded coaching prompt: {len(prompt)} characters")
        else:
            logger.warning(f"Coaching prompt not found: {prompt_path}")
    except Exception as e:
        logger.error(f"Failed to load coaching prompt: {e}")
    
    # Test mock analysis generation
    logger.info("Testing mock analysis generation...")
    try:
        mock_analysis = {
            "overall_score": 7,
            "swing_phases": {
                "setup": {"start": 0.0, "end": 1.0},
                "backswing": {"start": 1.0, "end": 2.5},
                "downswing": {"start": 2.5, "end": 3.0},
                "impact": {"start": 3.0, "end": 3.2},
                "follow_through": {"start": 3.2, "end": 5.0}
            },
            "coaching_points": [
                {
                    "timestamp": 1.5,
                    "category": "backswing",
                    "issue": "Slight over-rotation of shoulders",
                    "suggestion": "Focus on maintaining shoulder alignment with target line",
                    "priority": "medium"
                },
                {
                    "timestamp": 2.8,
                    "category": "downswing",
                    "issue": "Minor early extension",
                    "suggestion": "Maintain spine angle through impact",
                    "priority": "high"
                }
            ],
            "pose_analysis": {
                "shoulder_angle": "Good shoulder turn with slight over-rotation at top",
                "hip_rotation": "Excellent hip rotation and sequencing",
                "spine_angle": "Maintains good posture with minor early extension",
                "head_position": "Stable head position throughout swing"
            },
            "summary": "Overall solid swing with good fundamentals. Focus on maintaining spine angle through impact and controlling shoulder rotation at the top of the backswing.",
            "confidence": 0.85,
            "duration": 5.0
        }
        logger.info(f"Generated mock analysis: {mock_analysis.keys()}")
        logger.info(f"Mock analysis score: {mock_analysis.get('overall_score')}")
    except Exception as e:
        logger.error(f"Failed to generate mock analysis: {e}")
    
    # Test Gemini availability
    logger.info("Testing Gemini availability...")
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your-gemini-api-key-here":
            logger.info("Gemini API key configured")
            genai.configure(api_key=api_key)
            try:
                models = list(genai.list_models())
                logger.info(f"Available models: {[m.name for m in models]}")
            except Exception as e:
                logger.error(f"Failed to list models: {e}")
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
    
    # Test temp directory creation
    logger.info("Testing temp directory creation...")
    try:
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {temp_dir}")
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        logger.info("Temp directory cleaned up")
    except Exception as e:
        logger.error(f"Failed to create temp directory: {e}")
    
    logger.info("Simple Gemini test completed!")


if __name__ == "__main__":
    asyncio.run(test_gemini_simple())