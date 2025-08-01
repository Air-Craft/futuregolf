"""
Test WebSocket-based swing detection
Based on AI_SWING_DETECTION.md testing requirements
"""

import pytest
import asyncio
import json
import base64
import websockets
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
import os
import shutil

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
FRAME_SUBMISSION_INTERVAL = 1.25  # Seconds between checking for swings
WS_URL = "ws://localhost:8000/ws/detect-golf-swing"
FRAMES_DIR = Path("tests/fixtures/swing-detection/test_movie001")

@pytest.fixture(scope="session", autouse=True)
def setup_and_cleanup():
    """Setup test frames before tests and cleanup after"""
    # Setup: Extract frames if not present
    if not FRAMES_DIR.exists() or not (FRAMES_DIR / "frames_info.json").exists():
        print("Extracting frames from test video...")
        from tests.extract_video_frames import extract_frames_with_json
        test_video = "tests/fixtures/video/test_video.mov"
        extract_frames_with_json(test_video, str(FRAMES_DIR))
    
    yield  # Run tests
    
    # Cleanup: Remove extracted frames
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
        print(f"\nCleaned up test frames from {FRAMES_DIR}")

class SwingDetectionTestClient:
    """WebSocket client for testing swing detection"""
    
    def __init__(self):
        self.websocket = None
        self.swings_detected: List[Dict[str, Any]] = []
        self.all_responses: List[Dict[str, Any]] = []
        self.image_queue: List[Dict[str, Any]] = []
        self.current_queue_start_idx = 0
        
    async def connect(self, url: str):
        """Connect to WebSocket endpoint"""
        self.websocket = await websockets.connect(url)
        
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            
    async def send_frame(self, timestamp: float, image_base64: str):
        """Send a frame to the server"""
        message = {
            "timestamp": timestamp,
            "image_base64": image_base64
        }
        await self.websocket.send(json.dumps(message))
        
    async def receive_response(self) -> Dict[str, Any]:
        """Receive response from server"""
        response = await self.websocket.recv()
        return json.loads(response)
        
    def load_frames(self) -> List[Dict[str, Any]]:
        """Load frames from extracted video frames"""
        frames_info_path = FRAMES_DIR / "frames_info.json"
        with open(frames_info_path, 'r') as f:
            frames_data = json.load(f)
            
        frames = []
        for frame_info in frames_data:
            # Load image file
            image_path = FRAMES_DIR / frame_info['filename']
            with open(image_path, 'rb') as img_file:
                image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                
            frames.append({
                'timestamp': frame_info['timestamp'],
                'image_base64': image_base64
            })
            
        return frames
        
    async def simulate_ios_streaming(self, frames: List[Dict[str, Any]]):
        """
        Simulate iOS app behavior:
        - Stream images rapidly (no delays) 
        - Timestamps in frames maintain temporal relationships
        - Reset queue when swing is detected
        """
        
        print(f"\nStarting swing detection simulation with {len(frames)} frames")
        print("Sending frames rapidly (timestamps maintain video timing)")
        
        frame_idx = 0
        
        while frame_idx < len(frames):
            current_frame = frames[frame_idx]
            
            # Add frame to queue
            self.image_queue.append(current_frame)
            
            # Send current frame immediately (no delay)
            await self.send_frame(
                current_frame['timestamp'],
                current_frame['image_base64']
            )
            
            # Receive response immediately
            response = await self.receive_response()
            self.all_responses.append(response)
            
            # Check if swing was detected
            if response.get('swing_detected', False):
                swing_info = {
                    'timestamp': response['timestamp'],
                    'frame_index': frame_idx,
                    'queue_size': len(self.image_queue),
                    'context_window': response.get('context_window', 0),
                    'context_size': response.get('context_size', 0),
                    'confidence': response.get('confidence', 0.0)
                }
                self.swings_detected.append(swing_info)
                
                print(f"\n✅ SWING DETECTED at {response['timestamp']}s!")
                print(f"   Confidence: {response.get('confidence', 0.0):.2f}")
                print(f"   Queue size: {len(self.image_queue)} frames")
                print(f"   Context window: {response.get('context_window', 0):.2f}s")
                print(f"   Context size: {response.get('context_size', 0)} KB")
                
                # Reset queue after swing detection
                self.image_queue = []
                self.current_queue_start_idx = frame_idx + 1
            else:
                # Check status and confidence
                status = response.get('status', 'unknown')
                confidence = response.get('confidence', 0.0)
                if frame_idx % 10 == 0:  # Log every 10th frame
                    print(f"Frame {frame_idx}: {status} - "
                          f"Confidence: {confidence:.2f}, "
                          f"Context window: {response.get('context_window', 0):.2f}s, "
                          f"Context size: {response.get('context_size', 0)} KB")
            
            frame_idx += 1
            
        print(f"\nSimulation complete. Swings detected: {len(self.swings_detected)}")

@pytest.mark.asyncio
async def test_swing_detection_three_swings():
    """Test that the system detects 3 swings in the test video"""
    
    client = SwingDetectionTestClient()
    
    try:
        # Load frames
        frames = client.load_frames()
        print(f"Loaded {len(frames)} frames from test video")
        
        # Connect to WebSocket
        await client.connect(WS_URL)
        print("Connected to WebSocket endpoint")
        
        # Run simulation
        await client.simulate_ios_streaming(frames)
        
        # Verify results - expecting 3 high-confidence swings  
        high_confidence_swings = [s for s in client.swings_detected if s['confidence'] >= 0.75]
        assert len(high_confidence_swings) == 3, \
            f"Expected 3 high-confidence swings (>= 0.75), but detected {len(high_confidence_swings)}"
        
        # Print swing detection summary
        print("\n📊 SWING DETECTION SUMMARY:")
        print("-" * 50)
        for i, swing in enumerate(client.swings_detected, 1):
            print(f"Swing {i}:")
            print(f"  - Detected at: {swing['timestamp']}s")
            print(f"  - Confidence: {swing['confidence']:.2f}")
            print(f"  - Frame index: {swing['frame_index']}")
            print(f"  - Queue size: {swing['queue_size']}")
            print(f"  - Context window: {swing['context_window']:.2f}s")
            print(f"  - Context size: {swing['context_size']} KB")
            print()
            
        # Additional assertions on timing
        for i, swing in enumerate(client.swings_detected):
            # Context window should be at least LLM_SUBMISSION_THRESHOLD
            assert swing['context_window'] >= 1.25, \
                f"Swing {i+1} context window too small: {swing['context_window']}s"
                
    finally:
        await client.disconnect()
        print("Disconnected from WebSocket")

@pytest.mark.asyncio  
async def test_swing_detection_memory_trimming():
    """Test that old frames are trimmed from memory after 5 seconds"""
    
    client = SwingDetectionTestClient()
    
    try:
        # Load frames 
        frames = client.load_frames()
        
        # Connect to WebSocket
        await client.connect(WS_URL)
        
        # Send frames spanning more than 5 seconds
        frames_to_send = [f for f in frames if f['timestamp'] <= 7.0]
        
        responses = []
        for frame in frames_to_send:
            await client.send_frame(frame['timestamp'], frame['image_base64'])
            response = await client.receive_response()
            responses.append(response)
            
        # Check that context window never exceeds 5 seconds
        for response in responses:
            context_window = response.get('context_window', 0)
            assert context_window <= 5.0, \
                f"Context window exceeds 5s limit: {context_window}s"
                
        print("✅ Memory trimming test passed - context window stays within 5s limit")
        
    finally:
        await client.disconnect()

@pytest.mark.asyncio
async def test_swing_detection_continuous_streaming():
    """Test continuous streaming behavior without gaps"""
    
    client = SwingDetectionTestClient()
    
    try:
        # Load frames
        frames = client.load_frames()[:20]  # Use first 20 frames
        
        # Connect to WebSocket
        await client.connect(WS_URL)
        
        # Stream frames continuously
        for i, frame in enumerate(frames):
            await client.send_frame(frame['timestamp'], frame['image_base64'])
            response = await client.receive_response()
            
            # Verify we get valid responses
            assert 'status' in response
            assert response['status'] in ['evaluated', 'awaiting_more_data']
            
        print("✅ Continuous streaming test passed")
        
    finally:
        await client.disconnect()

def cleanup_test_frames():
    """Clean up extracted frames after tests"""
    import shutil
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
        print(f"Cleaned up test frames from {FRAMES_DIR}")

def run_tests():
    """Run all tests"""
    try:
        # Run with pytest
        pytest.main([__file__, "-v", "-s"])
    finally:
        # Cleanup after tests
        cleanup_test_frames()

if __name__ == "__main__":
    # For manual testing
    import argparse
    parser = argparse.ArgumentParser(description="Test WebSocket swing detection")
    parser.add_argument("--url", default=WS_URL, help="WebSocket URL")
    parser.add_argument("--manual", action="store_true", help="Run manual test")
    args = parser.parse_args()
    
    if args.manual:
        # Run manual test
        async def manual_test():
            client = SwingDetectionTestClient()
            frames = client.load_frames()
            await client.connect(args.url)
            await client.simulate_ios_streaming(frames)
            await client.disconnect()
            
        asyncio.run(manual_test())
    else:
        run_tests()