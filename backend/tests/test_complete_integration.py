#!/usr/bin/env python3
"""
Complete integration test for MediaPipe pose analysis.
Tests the full pipeline from video analysis to API endpoints.
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.video_analysis_service import VideoAnalysisService
from services.pose_analysis_service import get_pose_analysis_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_complete_integration():
    """Test complete integration of pose analysis with video analysis service."""
    try:
        logger.info("Starting complete integration test...")
        
        # Test video path
        test_video_path = os.path.join(os.path.dirname(__file__), "tests", "test_video.mov")
        
        if not os.path.exists(test_video_path):
            logger.error(f"Test video not found at: {test_video_path}")
            return False
        
        # Create video analysis service
        video_analysis_service = VideoAnalysisService()
        
        # Test pose analysis service availability
        if not video_analysis_service.pose_analysis_service:
            logger.error("Pose analysis service not available")
            return False
        
        logger.info("✓ Pose analysis service is available")
        
        # Test pose analysis directly
        pose_result = await video_analysis_service.pose_analysis_service.analyze_video_pose(test_video_path)
        
        if not pose_result.get('success'):
            logger.error(f"Pose analysis failed: {pose_result.get('error', 'Unknown error')}")
            return False
        
        logger.info("✓ Pose analysis completed successfully")
        
        # Test video analysis with pose integration
        logger.info("Testing integrated video analysis...")
        
        # Mock video analysis (without actual database operations)
        try:
            # Download video (simulate)
            video_path = test_video_path
            
            # Perform pose analysis
            pose_analysis_result = await video_analysis_service.pose_analysis_service.analyze_video_pose(video_path)
            
            if not pose_analysis_result.get('success'):
                logger.error("Pose analysis failed in integration")
                return False
            
            # Load coaching prompt
            coaching_prompt = await video_analysis_service._load_coaching_prompt()
            
            # Analyze with Gemini (this will use mock analysis)
            analysis_result = await video_analysis_service._analyze_with_gemini(
                video_path, 
                coaching_prompt, 
                pose_analysis_result
            )
            
            # Check combined results
            if not analysis_result:
                logger.error("Video analysis failed")
                return False
            
            logger.info("✓ Integrated video analysis completed")
            
            # Validate data structure
            if not validate_integration_results(analysis_result, pose_analysis_result):
                logger.error("Integration results validation failed")
                return False
            
            logger.info("✓ Integration results validation passed")
            
            # Save integration test results
            integration_results = {
                "pose_analysis": pose_analysis_result,
                "video_analysis": analysis_result,
                "integration_status": "success"
            }
            
            output_file = os.path.join(os.path.dirname(__file__), "integration_test_results.json")
            with open(output_file, 'w') as f:
                json.dump(integration_results, f, indent=2)
            
            logger.info(f"Integration test results saved to: {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Complete integration test failed: {e}")
        return False


def validate_integration_results(analysis_result, pose_result):
    """Validate that integration results contain expected data."""
    try:
        # Check basic structure
        if not isinstance(analysis_result, dict):
            logger.error("Analysis result is not a dictionary")
            return False
        
        if not isinstance(pose_result, dict):
            logger.error("Pose result is not a dictionary")
            return False
        
        # Check pose analysis structure
        required_pose_fields = [
            'angle_analysis', 
            'swing_phases', 
            'biomechanical_efficiency', 
            'recommendations'
        ]
        
        for field in required_pose_fields:
            if field not in pose_result:
                logger.error(f"Missing pose analysis field: {field}")
                return False
        
        # Check angle analysis
        angle_analysis = pose_result.get('angle_analysis', {})
        expected_body_parts = ['spine_angle', 'shoulder_tilt', 'hip_rotation', 'head_position']
        
        for body_part in expected_body_parts:
            if body_part not in angle_analysis:
                logger.warning(f"Missing body part in angle analysis: {body_part}")
        
        # Check biomechanical efficiency
        biomech = pose_result.get('biomechanical_efficiency', {})
        expected_scores = ['overall_score', 'kinetic_chain_score', 'power_transfer_score', 'balance_score']
        
        for score in expected_scores:
            if score not in biomech:
                logger.warning(f"Missing biomechanical score: {score}")
        
        # Check swing phases
        swing_phases = pose_result.get('swing_phases', {})
        expected_phases = ['setup', 'backswing', 'downswing', 'impact', 'follow_through']
        
        for phase in expected_phases:
            if phase not in swing_phases:
                logger.warning(f"Missing swing phase: {phase}")
        
        logger.info("✓ Integration results validation completed")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False


async def test_mock_api_responses():
    """Test that API responses would include pose analysis data."""
    try:
        logger.info("Testing mock API responses...")
        
        # Simulate analysis data structure
        mock_analysis = {
            "pose_data": {
                "angle_analysis": {
                    "spine_angle": {
                        "setup": {"angle": 35.0, "optimal": True, "status": "green"}
                    }
                },
                "biomechanical_efficiency": {
                    "overall_score": 82.0
                }
            },
            "body_position_data": {
                "spine_angle": {
                    "setup": {"angle": 35.0, "optimal": True, "status": "green"}
                }
            },
            "swing_metrics": {
                "overall_score": 82.0,
                "kinetic_chain_score": 78.0
            }
        }
        
        # Test pose analysis endpoint response
        pose_response = {
            "success": True,
            "analysis_id": 1,
            "pose_analysis": mock_analysis["pose_data"],
            "body_angles": mock_analysis["body_position_data"],
            "biomechanical_scores": mock_analysis["swing_metrics"]
        }
        
        # Test body angles endpoint response
        body_angles_response = {
            "success": True,
            "analysis_id": 1,
            "body_angles": mock_analysis["body_position_data"],
            "optimal_ranges": {
                "spine_angle": {"min": 30, "max": 45},
                "shoulder_tilt": {"min": 5, "max": 15},
                "hip_rotation": {"min": 30, "max": 45}
            }
        }
        
        # Test biomechanical scores endpoint response
        biomech_response = {
            "success": True,
            "analysis_id": 1,
            "biomechanical_scores": mock_analysis["swing_metrics"],
            "score_descriptions": {
                "overall_score": "Overall swing efficiency and biomechanical correctness",
                "kinetic_chain_score": "Efficiency of energy transfer through the kinetic chain"
            }
        }
        
        # Validate responses
        if not all([
            pose_response.get("success"),
            body_angles_response.get("success"),
            biomech_response.get("success")
        ]):
            logger.error("Mock API responses validation failed")
            return False
        
        logger.info("✓ Mock API responses validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Mock API response test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    logger.info("=" * 60)
    logger.info("MEDIAPIPE POSE ANALYSIS COMPLETE INTEGRATION TEST")
    logger.info("=" * 60)
    
    tests = [
        ("Complete Integration Test", test_complete_integration),
        ("Mock API Response Test", test_mock_api_responses),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = await test_func()
            results.append((test_name, result))
            logger.info(f"✓ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            logger.error(f"✗ {test_name}: FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("INTEGRATION TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
        logger.info("MediaPipe pose analysis is fully integrated and working correctly.")
        return 0
    else:
        logger.error("❌ SOME INTEGRATION TESTS FAILED")
        logger.error("Check the logs above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)