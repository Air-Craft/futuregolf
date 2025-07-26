#!/usr/bin/env python3
"""Test pose analysis service activation."""
import asyncio
import sys
sys.path.insert(0, '.')

from services.pose_analysis_service import get_pose_analysis_service

async def test_pose_service():
    try:
        # Get the service
        pose_service = get_pose_analysis_service()
        print(f"✅ Pose service created: {pose_service}")
        
        # Check if MediaPipe is available
        if hasattr(pose_service, 'pose') and pose_service.pose is not None:
            print("✅ MediaPipe is active and ready!")
            print("   The pose detection will work with real body tracking")
        else:
            print("❌ MediaPipe not initialized - using mock data")
            
        # Test with a mock video path
        result = await pose_service.analyze_video_pose("test_video.mp4")
        print(f"\nAnalysis result success: {result.get('success')}")
        
        if result.get('angle_analysis'):
            print("✅ Got angle analysis data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pose_service())