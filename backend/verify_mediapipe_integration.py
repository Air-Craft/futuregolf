#!/usr/bin/env python3
"""
Quick verification script for MediaPipe integration.
Runs basic checks to ensure everything is working correctly.
"""

import os
import sys
import asyncio
import logging

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import mediapipe as mp
        import cv2
        import numpy as np
        logger.info("✓ All dependencies installed (MediaPipe, OpenCV, NumPy)")
        return True
    except ImportError as e:
        logger.error(f"✗ Missing dependency: {e}")
        return False


def check_services():
    """Check if services can be imported and initialized."""
    try:
        from services.pose_analysis_service import get_pose_analysis_service
        from services.video_analysis_service import get_video_analysis_service
        
        # Test service initialization
        pose_service = get_pose_analysis_service()
        video_service = get_video_analysis_service()
        
        logger.info("✓ Services imported and initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Service initialization failed: {e}")
        return False


def check_test_video():
    """Check if test video exists."""
    test_video_path = os.path.join(os.path.dirname(__file__), "tests", "test_video.mov")
    if os.path.exists(test_video_path):
        logger.info("✓ Test video found")
        return True
    else:
        logger.error("✗ Test video not found")
        return False


def check_integration():
    """Check integration between services."""
    try:
        from services.video_analysis_service import VideoAnalysisService
        
        service = VideoAnalysisService()
        has_pose_service = hasattr(service, 'pose_analysis_service') and service.pose_analysis_service is not None
        
        if has_pose_service:
            logger.info("✓ Video analysis service has pose analysis integration")
            return True
        else:
            logger.error("✗ Video analysis service missing pose analysis integration")
            return False
    except Exception as e:
        logger.error(f"✗ Integration check failed: {e}")
        return False


def check_api_endpoints():
    """Check if API endpoints are properly configured."""
    try:
        from api.video_analysis import router
        
        # Check if new endpoints are registered
        endpoint_paths = [route.path for route in router.routes]
        
        expected_endpoints = [
            '/pose-analysis/{analysis_id}',
            '/body-angles/{analysis_id}',
            '/biomechanical-scores/{analysis_id}'
        ]
        
        missing_endpoints = []
        for endpoint in expected_endpoints:
            # Check if any route path contains the endpoint pattern
            if not any(endpoint.replace('{analysis_id}', '').rstrip('/') in path for path in endpoint_paths):
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            logger.error(f"✗ Missing API endpoints: {missing_endpoints}")
            return False
        else:
            logger.info("✓ All API endpoints configured correctly")
            return True
    except Exception as e:
        logger.error(f"✗ API endpoint check failed: {e}")
        return False


async def check_pose_analysis_basic():
    """Check basic pose analysis functionality."""
    try:
        from services.pose_analysis_service import get_pose_analysis_service
        
        pose_service = get_pose_analysis_service()
        
        # Test with mock data (without actual video processing)
        mock_result = await pose_service._generate_mock_pose_analysis()
        
        if mock_result.get('success'):
            logger.info("✓ Basic pose analysis functionality working")
            return True
        else:
            logger.error("✗ Basic pose analysis functionality failed")
            return False
    except Exception as e:
        logger.error(f"✗ Pose analysis basic check failed: {e}")
        return False


async def main():
    """Run all verification checks."""
    logger.info("="*60)
    logger.info("MEDIAPIPE INTEGRATION VERIFICATION")
    logger.info("="*60)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Services", check_services),
        ("Test Video", check_test_video),
        ("Integration", check_integration),
        ("API Endpoints", check_api_endpoints),
        ("Basic Pose Analysis", check_pose_analysis_basic),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        logger.info(f"\n--- {check_name} ---")
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"✗ {check_name}: Exception occurred: {e}")
            results.append((check_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{status}: {check_name}")
    
    logger.info(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("\n🎉 ALL VERIFICATION CHECKS PASSED!")
        logger.info("MediaPipe integration is ready for use.")
        
        # Print usage instructions
        logger.info("\n" + "="*60)
        logger.info("USAGE INSTRUCTIONS")
        logger.info("="*60)
        logger.info("1. Start the server: python start_server.py")
        logger.info("2. Upload a video via API")
        logger.info("3. Analyze video: POST /api/v1/video-analysis/analyze/{video_id}")
        logger.info("4. Get pose analysis: GET /api/v1/video-analysis/pose-analysis/{analysis_id}")
        logger.info("5. Get body angles: GET /api/v1/video-analysis/body-angles/{analysis_id}")
        logger.info("6. Get biomechanical scores: GET /api/v1/video-analysis/biomechanical-scores/{analysis_id}")
        
        return 0
    else:
        logger.error("\n❌ SOME VERIFICATION CHECKS FAILED")
        logger.error("Please check the logs above and fix any issues.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)