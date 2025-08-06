#!/usr/bin/env python3
"""
Test swing detection against a live server
This allows testing with a manually started server to see all logs
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the test client and utilities
from tests.test_swing_detection_ws import SwingDetectionTestClient
from tests.utils.video_frame_extractor import VideoFrameExtractor


async def test_live_server(ws_url: str, video_name: str = "test_video"):
    """Test swing detection against a live server"""
    
    print(f"🔗 Connecting to: {ws_url}")
    print(f"📹 Using video: {video_name}")
    
    # Create frame extractor
    frame_extractor = VideoFrameExtractor()
    
    # Extract frames
    print("\n📸 Extracting frames from video...")
    video_config = frame_extractor.get_test_video_config(video_name)
    frames_path = frame_extractor.extract_frames(video_config['path'], video_name)
    
    # Create client
    client = SwingDetectionTestClient()
    
    try:
        # Load frames
        frames = client.load_frames(frames_path)
        print(f"✅ Loaded {len(frames)} frames")
        
        # Connect to WebSocket
        await client.connect(ws_url)
        print("✅ Connected to WebSocket endpoint")
        
        # Run simulation
        print("\n🚀 Starting swing detection simulation...")
        await client.simulate_ios_streaming(frames)
        
        # Print results
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Total frames sent: {len(frames)}")
        print(f"   Responses received: {len(client.all_responses)}")
        print(f"   Swings detected: {len(client.swings_detected)}")
        print(f"   Expected swings: {video_config['expected_swings']}")
        
        # Detailed swing info
        if client.swings_detected:
            print("\n🏌️ SWING DETAILS:")
            for i, swing in enumerate(client.swings_detected, 1):
                print(f"\nSwing {i}:")
                print(f"  - Timestamp: {swing['timestamp']:.2f}s")
                print(f"  - Confidence: {swing['confidence']:.2f}")
                print(f"  - Context window: {swing['context_window']:.2f}s")
                print(f"  - Context size: {swing['context_size']} KB")
        
        # Check for errors
        error_responses = [r for r in client.all_responses if 'error' in r]
        if error_responses:
            print("\n❌ ERRORS DETECTED:")
            for err in error_responses[:5]:  # Show first 5 errors
                print(f"  - {err.get('error', 'Unknown error')}")
        
        # Summary of response statuses
        status_counts = {}
        for resp in client.all_responses:
            status = resp.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\n📈 RESPONSE STATUS SUMMARY:")
        for status, count in sorted(status_counts.items()):
            print(f"  - {status}: {count}")
        
        # Success check
        success = len(client.swings_detected) == video_config['expected_swings']
        if success:
            print(f"\n✅ SUCCESS: Detected all {video_config['expected_swings']} expected swings!")
        else:
            print(f"\n⚠️  WARNING: Expected {video_config['expected_swings']} swings, but detected {len(client.swings_detected)}")
        
        return success
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Disconnect
        await client.disconnect()
        print("\n🔌 Disconnected from WebSocket")
        
        # Cleanup frames
        frame_extractor.cleanup_output_dir(video_name)
        print("🧹 Cleaned up extracted frames")


def main():
    parser = argparse.ArgumentParser(
        description="Test swing detection against a live server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test against local server on default port
  python test_swing_detection_live.py
  
  # Test against local server on custom port
  python test_swing_detection_live.py --base http://localhost:8001
  
  # Test against remote server
  python test_swing_detection_live.py --base https://api.example.com
  
  # Use a different test video
  python test_swing_detection_live.py --video my_test_video
"""
    )
    
    parser.add_argument(
        "--base",
        default="http://localhost:8009",
        help="Base URL of the server (default: http://localhost:8009)"
    )
    
    parser.add_argument(
        "--video",
        default="test_video",
        help="Name of test video to use (default: test_video)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Construct WebSocket URL from base URL
    base_url = args.base.rstrip('/')
    if base_url.startswith('https://'):
        ws_url = base_url.replace('https://', 'wss://') + '/ws/detect-golf-swing'
    elif base_url.startswith('http://'):
        ws_url = base_url.replace('http://', 'ws://') + '/ws/detect-golf-swing'
    else:
        # Assume http if no protocol specified
        ws_url = f"ws://{base_url}/ws/detect-golf-swing"
    
    print(f"🌐 Base URL: {base_url}")
    print(f"🔗 WebSocket URL: {ws_url}")
    
    # Set up logging if verbose
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Run the test
    success = asyncio.run(test_live_server(ws_url, args.video))
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()