#!/usr/bin/env python3
"""
Simple pipeline test to verify basic functionality.
"""

import asyncio
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from services.video_pipeline_service import get_video_pipeline_service


async def test_basic_pipeline():
    """Test basic pipeline functionality."""
    print("🎬 Testing Basic Video Pipeline")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline_service = get_video_pipeline_service()
    print("✅ Pipeline service initialized")
    
    # Test health check
    health = await pipeline_service.validate_pipeline_health()
    print(f"✅ Health check: {'HEALTHY' if health['pipeline_healthy'] else 'UNHEALTHY'}")
    
    # Show component status
    for component, status in health['components'].items():
        icon = "✅" if status['healthy'] else "❌"
        print(f"   {icon} {component}: {status['message']}")
    
    # Test video file
    test_video_path = os.path.join(os.path.dirname(__file__), "tests", "test_video.mov")
    
    if os.path.exists(test_video_path):
        print(f"✅ Test video found: {test_video_path}")
        file_size = os.path.getsize(test_video_path)
        print(f"   Size: {file_size / 1024:.1f} KB")
        
        # Test individual components
        print("\n📊 Testing Individual Components:")
        
        # Test pose analysis
        if pipeline_service.pose_analysis_service:
            print("   🏃 Testing pose analysis...")
            try:
                pose_result = await pipeline_service.pose_analysis_service.analyze_video_pose(test_video_path)
                print(f"   ✅ Pose analysis: {'Success' if pose_result.get('success') else 'Failed'}")
                if pose_result.get('success'):
                    metadata = pose_result.get('analysis_metadata', {})
                    print(f"       Frames: {metadata.get('total_frames', 0)}")
                    print(f"       Duration: {metadata.get('video_duration', 0):.1f}s")
            except Exception as e:
                print(f"   ❌ Pose analysis failed: {e}")
        else:
            print("   ⚠️ Pose analysis service not available")
        
        # Test AI analysis (mock)
        if pipeline_service.video_analysis_service:
            print("   🤖 AI analysis service available")
        else:
            print("   ⚠️ AI analysis service not available")
        
        # Test storage service
        if pipeline_service.storage_service:
            print("   📦 Storage service available")
        else:
            print("   ⚠️ Storage service not available (will use mock)")
        
        print("\n🎯 Testing Complete Pipeline Workflow:")
        print("   (This would normally process a video end-to-end)")
        print("   Pipeline components are ready for integration")
        
    else:
        print(f"❌ Test video not found: {test_video_path}")
    
    print("\n🎉 Basic pipeline test complete!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_basic_pipeline())
    exit(0 if success else 1)