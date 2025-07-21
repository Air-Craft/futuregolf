"""
Test video analysis API endpoints.
"""

import httpx
import asyncio
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


async def test_analysis_api():
    """Test the video analysis API endpoints."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test health endpoint
        logger.info("Testing health endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            logger.info(f"Health check: {response.status_code} - {response.json()}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return
        
        # Test auth config endpoint
        logger.info("Testing auth config endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/auth/config")
            logger.info(f"Auth config: {response.status_code} - {response.json()}")
        except Exception as e:
            logger.error(f"Auth config failed: {e}")
        
        # Test video analysis endpoints (these will fail without auth, but let's see the errors)
        logger.info("Testing video analysis endpoints without auth...")
        
        # Test analyze video endpoint
        try:
            response = await client.post(f"{BASE_URL}/api/v1/video-analysis/analyze/1")
            logger.info(f"Analyze video: {response.status_code} - {response.json()}")
        except Exception as e:
            logger.error(f"Analyze video failed: {e}")
        
        # Test get analysis status
        try:
            response = await client.get(f"{BASE_URL}/api/v1/video-analysis/status/1")
            logger.info(f"Analysis status: {response.status_code} - {response.json()}")
        except Exception as e:
            logger.error(f"Analysis status failed: {e}")
        
        # Test get analysis results
        try:
            response = await client.get(f"{BASE_URL}/api/v1/video-analysis/results/1")
            logger.info(f"Analysis results: {response.status_code} - {response.json()}")
        except Exception as e:
            logger.error(f"Analysis results failed: {e}")
        
        # Test get video analysis
        try:
            response = await client.get(f"{BASE_URL}/api/v1/video-analysis/video/1")
            logger.info(f"Video analysis: {response.status_code} - {response.json()}")
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
        
        # Test get user analyses
        try:
            response = await client.get(f"{BASE_URL}/api/v1/video-analysis/user/analyses")
            logger.info(f"User analyses: {response.status_code} - {response.json()}")
        except Exception as e:
            logger.error(f"User analyses failed: {e}")
        
        logger.info("API test completed!")


if __name__ == "__main__":
    asyncio.run(test_analysis_api())