#!/usr/bin/env python3
"""
Test script for MediaPipe pose analysis integration.
Tests pose detection with the test video and validates results.
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pose_analysis_service import get_pose_analysis_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_pose_analysis():
    """Test pose analysis with the test video."""
    try:
        # Get pose analysis service
        pose_service = get_pose_analysis_service()
        
        # Path to test video
        test_video_path = os.path.join(os.path.dirname(__file__), "tests", "test_video.mov")
        
        if not os.path.exists(test_video_path):
            logger.error(f"Test video not found at: {test_video_path}")
            return False
        
        logger.info(f"Testing pose analysis with video: {test_video_path}")
        
        # Analyze video pose
        result = await pose_service.analyze_video_pose(test_video_path)
        
        # Validate results
        if not result.get('success'):
            logger.error(f"Pose analysis failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Print results summary
        logger.info("Pose analysis completed successfully!")
        
        # Check pose landmarks
        pose_landmarks = result.get('pose_landmarks', [])
        logger.info(f"Extracted pose landmarks from {len(pose_landmarks)} frames")
        
        # Check angle analysis
        angle_analysis = result.get('angle_analysis', {})
        logger.info("Angle Analysis Results:")
        for body_part, phases in angle_analysis.items():
            logger.info(f"  {body_part.replace('_', ' ').title()}:")
            if isinstance(phases, dict):
                for phase, data in phases.items():
                    if isinstance(data, dict) and 'angle' in data:
                        status = data.get('status', 'unknown')
                        angle = data.get('angle', 0)
                        logger.info(f"    {phase}: {angle:.1f}° ({status})")
                    elif isinstance(data, (int, float)):
                        logger.info(f"    {phase}: {data}")
        
        # Check biomechanical efficiency
        efficiency = result.get('biomechanical_efficiency', {})
        logger.info("Biomechanical Efficiency Scores:")
        for metric, score in efficiency.items():
            logger.info(f"  {metric.replace('_', ' ').title()}: {score:.1f}")
        
        # Check swing phases
        swing_phases = result.get('swing_phases', {})
        logger.info("Detected Swing Phases:")
        for phase, timing in swing_phases.items():
            if isinstance(timing, dict):
                start = timing.get('start', 0)
                end = timing.get('end', 0)
                logger.info(f"  {phase.replace('_', ' ').title()}: {start:.1f}s - {end:.1f}s")
        
        # Check recommendations
        recommendations = result.get('recommendations', [])
        logger.info(f"Generated {len(recommendations)} coaching recommendations")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"  {i}. {rec.get('body_part', 'Unknown').title()}: {rec.get('issue', 'No issue')}")
        
        # Save detailed results to file
        output_file = os.path.join(os.path.dirname(__file__), "pose_analysis_test_results.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Detailed results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        return False


def validate_pose_landmarks(landmarks_data):
    """Validate pose landmarks data structure."""
    if not landmarks_data:
        return False
    
    required_fields = ['frame_number', 'timestamp', 'landmarks']
    
    for frame_data in landmarks_data:
        for field in required_fields:
            if field not in frame_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Check landmarks structure
        if frame_data['landmarks']:
            landmark = frame_data['landmarks'][0]
            required_coords = ['x', 'y', 'z']
            for coord in required_coords:
                if coord not in landmark:
                    logger.error(f"Missing coordinate: {coord}")
                    return False
    
    return True


def validate_angle_analysis(angle_analysis):
    """Validate angle analysis data structure."""
    expected_body_parts = ['spine_angle', 'shoulder_tilt', 'hip_rotation', 'head_position']
    
    for body_part in expected_body_parts:
        if body_part not in angle_analysis:
            logger.warning(f"Missing body part analysis: {body_part}")
            continue
        
        if body_part == 'head_position':
            required_fields = ['stability_score', 'lateral_movement', 'vertical_movement']
            for field in required_fields:
                if field not in angle_analysis[body_part]:
                    logger.error(f"Missing head position field: {field}")
                    return False
        else:
            # Check for phase-specific data
            phases = angle_analysis[body_part]
            if not isinstance(phases, dict):
                logger.error(f"Invalid structure for {body_part}")
                return False
    
    return True


async def test_video_analysis_integration():
    """Test pose analysis integration with video analysis service."""
    try:
        from services.video_analysis_service import VideoAnalysisService
        
        logger.info("Testing video analysis service integration...")
        
        # Create video analysis service
        analysis_service = VideoAnalysisService()
        
        # Check if pose service is available
        if not hasattr(analysis_service, 'pose_analysis_service') or not analysis_service.pose_analysis_service:
            logger.error("Pose analysis service not available in video analysis service")
            return False
        
        logger.info("Video analysis service has pose analysis integration")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("Starting MediaPipe pose analysis tests...")
    
    # Test 1: Basic pose analysis
    logger.info("\n=== Test 1: Basic Pose Analysis ===")
    pose_test_passed = await test_pose_analysis()
    
    # Test 2: Integration test
    logger.info("\n=== Test 2: Integration Test ===")
    integration_test_passed = await test_video_analysis_integration()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Pose Analysis Test: {'PASSED' if pose_test_passed else 'FAILED'}")
    logger.info(f"Integration Test: {'PASSED' if integration_test_passed else 'FAILED'}")
    
    if pose_test_passed and integration_test_passed:
        logger.info("All tests PASSED! MediaPipe pose analysis is working correctly.")
        return 0
    else:
        logger.error("Some tests FAILED. Check the logs for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)