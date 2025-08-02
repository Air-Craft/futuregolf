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
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import server fixture
from tests.fixtures.server_fixture import pytest_server_fixture
from tests.utils.video_frame_extractor import VideoFrameExtractor

@pytest.fixture(scope="session")
def server(request):
    """Conditionally create server fixture based on --base-url"""
    base_url = request.config.getoption("--base-url")
    if base_url:
        # Don't create a server in live mode
        yield None
    else:
        # Create the fixture server
        from tests.fixtures.server_fixture import TestServer
        test_server = TestServer()
        test_server.start()
        yield test_server
        test_server.stop()


@pytest.fixture
def server_or_live(server, base_url, live_server_mode):
    """Provide either fixture server or live server URL"""
    if live_server_mode:
        # Create a mock object that has the get_ws_url method
        class LiveServer:
            def __init__(self, base_url):
                self.base_url = base_url.rstrip('/')
            
            def get_ws_url(self, path):
                if self.base_url.startswith('https://'):
                    ws_base = self.base_url.replace('https://', 'wss://')
                elif self.base_url.startswith('http://'):
                    ws_base = self.base_url.replace('http://', 'ws://')
                else:
                    ws_base = f"ws://{self.base_url}"
                return f"{ws_base}{path}"
        
        return LiveServer(base_url)
    else:
        return server

# Test configuration
FRAME_SUBMISSION_INTERVAL = 1.25  # Seconds between checking for swings

# Setup logging
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def frame_extractor():
    """Create frame extractor for tests"""
    return VideoFrameExtractor()


@pytest.fixture(scope="function")
def extract_test_frames(frame_extractor, no_cleanup):
    """Extract frames from test video and cleanup after test"""
    video_name = "test_video"
    video_config = frame_extractor.get_test_video_config(video_name)
    frames_path = frame_extractor.output_dir / video_name
    
    # Check if frames already exist
    frames_info_path = frames_path / "frames_info.json"
    if frames_info_path.exists() and no_cleanup:
        print(f"♻️  Reusing existing frames from {frames_path}")
    else:
        # Cleanup before extraction if not preserving
        if not no_cleanup and frames_path.exists():
            frame_extractor.cleanup_output_dir(video_name)
        
        # Extract frames
        frames_path = frame_extractor.extract_frames(video_config['path'], video_name)
    
    yield frames_path, video_config['expected_swings']
    
    # Cleanup after test only if not preserving
    if not no_cleanup:
        frame_extractor.cleanup_output_dir(video_name)
    else:
        print(f"🗂️  Preserved extracted frames in {frames_path}")

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
        print(f"Sending frame @ {timestamp:.1f}s")
        await self.websocket.send(json.dumps(message))
        
    async def receive_response(self) -> Dict[str, Any]:
        """Receive response from server"""
        response = await self.websocket.recv()
        print(f"Received response: {response}")
        return json.loads(response)
        
    def load_frames(self, frames_dir: Path) -> List[Dict[str, Any]]:
        """Load frames from extracted video frames"""
        frames_info_path = frames_dir / "frames_info.json"
        with open(frames_info_path, 'r') as f:
            frames_data = json.load(f)
            
        frames = []
        for frame_info in frames_data:
            # Use pre-encoded base64 from frames_info
            frames.append({
                'timestamp': frame_info['timestamp'],
                'image_base64': frame_info['image_base64']
            })
            
        return frames
        
    async def send_frames_continuously(self, frames: List[Dict[str, Any]], done_event: asyncio.Event):
        """
        Send frames continuously without waiting for responses
        Simulates real iOS app behavior
        """
        print(f"\n📤 Starting frame sender - {len(frames)} frames to send")
        
        for frame_idx, frame in enumerate(frames):
            # Add frame to queue for tracking
            self.image_queue.append(frame)
            
            # Send frame without waiting for response
            await self.send_frame(frame['timestamp'], frame['image_base64'])
            
            # Log progress every 10 frames
            if frame_idx % 10 == 0:
                print(f"📤 Sent frame {frame_idx}/{len(frames)} @ {frame['timestamp']:.1f}s")
            
            # Small delay to prevent overwhelming the server
            # This simulates realistic frame intervals
            await asyncio.sleep(0.2)
        
        print(f"📤 Frame sender complete - sent all {len(frames)} frames")
        done_event.set()
    
    async def receive_responses_continuously(self, done_event: asyncio.Event):
        """
        Continuously receive responses from the server
        Processes swing detections and status updates
        """
        print(f"\n📥 Starting response receiver")
        
        while True:
            try:
                # Check if we should stop receiving
                if done_event.is_set() and len(self.all_responses) >= len(self.image_queue):
                    print("📥 All frames processed, stopping receiver")
                    break
                
                # Set timeout to avoid hanging if server stops responding
                response = await asyncio.wait_for(self.receive_response(), timeout=5.0)
                self.all_responses.append(response)
                
                # Process response
                status = response.get('status', 'unknown')
                timestamp = response.get('timestamp', 0)
                
                # Log important statuses
                if status == 'analyzing':
                    if len(self.all_responses) % 10 == 0:  # Reduce noise
                        print(f"📥 [{len(self.all_responses)}] Analyzing... elapsed: {response.get('elapsed_time', 0):.1f}s")
                elif status == 'evaluated':
                    print(f"📥 [{len(self.all_responses)}] Evaluated @ {timestamp:.1f}s")
                
                # Check for swing detection
                if response.get('swing_detected', False):
                    swing_info = {
                        'timestamp': response['timestamp'],
                        'response_index': len(self.all_responses) - 1,
                        'queue_size': len(self.image_queue),
                        'context_window': response.get('context_window', 0),
                        'context_size': response.get('context_size', 0),
                        'confidence': response.get('confidence', 0.0)
                    }
                    self.swings_detected.append(swing_info)
                    
                    print(f"\n✅ SWING DETECTED at {response['timestamp']}s!")
                    print(f"   Confidence: {response.get('confidence', 0.0):.2f}")
                    print(f"   Context window: {response.get('context_window', 0):.2f}s")
                    print(f"   Context size: {response.get('context_size', 0)} KB")
                    print(f"   Total swings: {response.get('total_swings', len(self.swings_detected))}")
                    
                    # Note: Queue reset happens on server side
                elif status == 'evaluated':
                    # Log when evaluated but no swing detected
                    confidence = response.get('confidence', 0.0)
                    print(f"📥 [{len(self.all_responses)}] Evaluated but no swing - confidence: {confidence:.2f}")
                    
            except asyncio.TimeoutError:
                if done_event.is_set():
                    print("📥 Timeout waiting for response, but all frames sent - stopping")
                    break
                else:
                    print("📥 Timeout waiting for response, continuing...")
                    continue
            except Exception as e:
                print(f"📥 Error receiving response: {e}")
                if done_event.is_set():
                    break
                continue
        
        print(f"📥 Response receiver stopped - received {len(self.all_responses)} responses")
    
    async def simulate_ios_streaming(self, frames: List[Dict[str, Any]]):
        """
        Simulate iOS app behavior with true asynchronous streaming:
        - Send frames continuously without waiting for responses
        - Receive responses independently in parallel
        - Maintain temporal relationships through timestamps
        """
        
        print(f"\n🚀 Starting swing detection simulation with {len(frames)} frames")
        print("   Simulating continuous iOS streaming behavior")
        
        # Event to signal when all frames have been sent
        done_event = asyncio.Event()
        
        # Create concurrent tasks for sending and receiving
        sender_task = asyncio.create_task(
            self.send_frames_continuously(frames, done_event)
        )
        receiver_task = asyncio.create_task(
            self.receive_responses_continuously(done_event)
        )
        
        try:
            # Wait for both tasks to complete
            await asyncio.gather(sender_task, receiver_task)
            
        except Exception as e:
            print(f"❌ Error during simulation: {e}")
            # Cancel tasks on error
            sender_task.cancel()
            receiver_task.cancel()
            raise
        
        print(f"\n📊 Simulation complete:")
        print(f"   Frames sent: {len(frames)}")
        print(f"   Responses received: {len(self.all_responses)}")
        print(f"   Swings detected: {len(self.swings_detected)}")

@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"),
    reason="Requires GEMINI_API_KEY or GOOGLE_API_KEY to be set"
)
async def test_swing_detection_three_swings(server_or_live, extract_test_frames, caplog, base_url, live_server_mode):
    """Test that the system detects 3 swings in the test video
    
    Uses real golf swing video and extracts frames matching iOS app behavior.
    NOTE: This test requires a valid GEMINI_API_KEY or GOOGLE_API_KEY to be set.
    
    Can be run in two modes:
    1. Fixture mode (default): Starts its own test server
    2. Live mode: Connects to an existing server via --base-url
    """
    
    frames_path, expected_swings = extract_test_frames
    client = SwingDetectionTestClient()
    
    # Set logging level to capture DEBUG logs
    import logging
    caplog.set_level(logging.INFO)
    
    # Print mode info
    if live_server_mode:
        print(f"🌐 Running in LIVE SERVER mode against: {base_url}")
    else:
        print(f"🏗️  Running in FIXTURE SERVER mode")
    
    try:
        # Load frames
        frames = client.load_frames(frames_path)
        print(f"Loaded {len(frames)} frames from test video")
        print(f"Sample frame 10: {frames[10]}")
        
        # Connect to WebSocket using appropriate server URL
        ws_url = server_or_live.get_ws_url("/ws/detect-golf-swing")
        print(f"🔗 About to connect to WebSocket URL: {ws_url}")
        await client.connect(ws_url)
        print(f"✅ Connected to WebSocket endpoint: {ws_url}")
        
        # Run simulation
        await client.simulate_ios_streaming(frames)
        
        # Verify results
        print(f"\nTest completed!")
        print(f"Total frames sent: {len(frames)}")
        print(f"Swings detected: {len(client.swings_detected)}")
        print(f"All responses received: {len(client.all_responses)}")
        
        # Verify we got responses for all frames
        assert len(client.all_responses) > 0, "No responses received from server"
        
        # Verify server is processing frames
        analyzing_responses = [r for r in client.all_responses if r.get('status') == 'analyzing']
        assert len(analyzing_responses) > 0, "Server should have analyzed frames"
        
        # Print relevant logs (only in fixture mode)
        if not live_server_mode:
            print("\n=== Server Logs ===")
            for record in caplog.records:
                if "swing_detection_ws" in record.name or "Task check" in record.message or "Background analysis" in record.message or "Analysis completed" in record.message:
                    print(f"{record.levelname}: {record.message}")
        
        # Verify we detected the expected number of swings
        assert len(client.swings_detected) == expected_swings, \
            f"Expected {expected_swings} swings, but detected {len(client.swings_detected)}"
        
        print(f"\n✅ Successfully detected {expected_swings} swings as expected!")
        
        # Print swing detection summary
        print("\n📊 SWING DETECTION SUMMARY:")
        print("-" * 50)
        for i, swing in enumerate(client.swings_detected, 1):
            print(f"Swing {i}:")
            print(f"  - Detected at: {swing['timestamp']}s")
            print(f"  - Confidence: {swing['confidence']:.2f}")
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

# Memory trimming test removed - rolling window no longer used
# Buffer only clears after successful swing detection

@pytest.mark.asyncio
async def test_swing_detection_continuous_streaming(server_or_live, extract_test_frames):
    """Test continuous streaming behavior without gaps"""
    
    frames_path, _ = extract_test_frames
    client = SwingDetectionTestClient()
    
    try:
        # Load frames
        frames = client.load_frames(frames_path)[:20]  # Use first 20 frames
        
        # Connect to WebSocket using appropriate server URL
        ws_url = server_or_live.get_ws_url("/ws/detect-golf-swing")
        await client.connect(ws_url)
        
        # Stream frames continuously
        for i, frame in enumerate(frames):
            await client.send_frame(frame['timestamp'], frame['image_base64'])
            response = await client.receive_response()
            
            # Verify we get valid responses
            assert 'status' in response
            assert response['status'] in ['evaluated', 'awaiting_more_data', 'analyzing']
            
        print("✅ Continuous streaming test passed")
        
    finally:
        await client.disconnect()

def cleanup_test_frames():
    """Clean up extracted frames after tests"""
    # Note: Cleanup is now handled by the extract_test_frames fixture
    pass

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
    parser.add_argument("--url", default="ws://localhost:8009/ws/detect-golf-swing", help="WebSocket URL")
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