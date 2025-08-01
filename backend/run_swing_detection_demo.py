"""
Demo script to run swing detection manually
This demonstrates the working implementation without pytest overhead
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.test_swing_detection_ws import SwingDetectionTestClient, FRAMES_DIR, WS_URL

async def main():
    """Run swing detection demo"""
    
    client = SwingDetectionTestClient()
    
    print("🏌️ Golf Swing Detection Demo")
    print("=" * 50)
    
    try:
        # Ensure frames are extracted
        if not FRAMES_DIR.exists() or not (FRAMES_DIR / "frames_info.json").exists():
            print("⚠️  Frames not found. Please run: pdm run python tests/extract_video_frames.py")
            return
            
        # Load frames
        frames = client.load_frames()
        print(f"✅ Loaded {len(frames)} frames from test video")
        
        # Connect to WebSocket
        await client.connect(WS_URL)
        print("✅ Connected to WebSocket endpoint")
        
        # Run simulation
        await client.simulate_ios_streaming(frames)
        
        # Display results
        print("\n" + "=" * 50)
        print("📊 RESULTS SUMMARY")
        print("=" * 50)
        print(f"Total swings detected: {len(client.swings_detected)}")
        print(f"Expected: 3-4 swings (AI interpretation may vary)")
        print(f"Status: {'✅ PASS' if 3 <= len(client.swings_detected) <= 4 else '❌ FAIL'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()
        print("\n✅ Demo complete!")

if __name__ == "__main__":
    # Ensure server is running
    print("⚠️  Make sure the backend server is running: pdm run python main.py")
    print()
    
    # Run the demo
    asyncio.run(main())