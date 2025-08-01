"""
Simple test for swing detection with updated parameters
"""

import asyncio
import json
import base64
import websockets
from pathlib import Path
import time
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.swing_detection import IOS_FRAME_INTERVAL, LLM_SUBMISSION_THRESHOLD, POST_DETECTION_COOLDOWN

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
WS_URL = "ws://localhost:8001/ws/detect-golf-swing"
FRAMES_DIR = Path("tests/fixtures/swing-detection/test_movie001")

async def test_swing_detection():
    """Test swing detection with new parameters"""
    
    # Load frames info
    frames_info_path = FRAMES_DIR / "frames_info.json"
    if not frames_info_path.exists():
        logger.error("Frames not found. Please run: pdm run python tests/extract_video_frames.py")
        return
        
    with open(frames_info_path, 'r') as f:
        frames_data = json.load(f)
    
    logger.info(f"Loaded {len(frames_data)} frames")
    logger.info(f"Frame interval: {IOS_FRAME_INTERVAL}s")
    logger.info(f"LLM submission threshold: {LLM_SUBMISSION_THRESHOLD}s")
    logger.info(f"Post-detection cooldown: {POST_DETECTION_COOLDOWN}s")
    
    # Connect to WebSocket
    async with websockets.connect(WS_URL) as websocket:
        logger.info("Connected to WebSocket endpoint")
        
        swings_detected = 0
        detection_times = []
        frames_sent = 0
        start_time = time.time()
        
        for frame_info in frames_data:
            # Load image
            image_path = FRAMES_DIR / frame_info['filename']
            with open(image_path, 'rb') as img_file:
                image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Send frame
            timestamp = frame_info['timestamp']
            message = {
                "timestamp": timestamp,
                "image_base64": image_base64
            }
            
            await websocket.send(json.dumps(message))
            frames_sent += 1
            
            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            
            # Log response
            status = data.get('status', 'unknown')
            
            if status == 'cooldown':
                cooldown_remaining = data.get('cooldown_remaining', 0)
                logger.info(f"Frame {frames_sent} ({timestamp:.2f}s): COOLDOWN - {cooldown_remaining:.1f}s remaining")
            elif status == 'test_complete':
                logger.info(f"\n✅ TEST COMPLETE: {data.get('message')}")
                break
            elif status == 'evaluated':
                if data.get("swing_detected"):
                    swings_detected += 1
                    detection_times.append(timestamp)
                    confidence = data.get('confidence', 0.0)
                    logger.info(f"\n🏌️ SWING {swings_detected} DETECTED at {timestamp:.2f}s (confidence: {confidence:.2f})")
            elif status == 'awaiting_more_data':
                if frames_sent % 10 == 0:  # Log every 10th frame
                    window = data.get('context_window', 0)
                    confidence = data.get('confidence', 0.0)
                    logger.info(f"Frame {frames_sent} ({timestamp:.2f}s): Waiting - window: {window:.2f}s, conf: {confidence:.2f}")
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"\n📊 Test Summary:")
        logger.info(f"  Total frames sent: {frames_sent}")
        logger.info(f"  Total swings detected: {swings_detected}")
        logger.info(f"  Time elapsed: {elapsed_time:.2f}s")
        logger.info(f"  Detection times: {[f'{t:.2f}s' for t in detection_times]}")
        
        # Assert we detected at least 3 swings (test ends after 3)
        assert swings_detected >= 3, f"Expected at least 3 swings, got {swings_detected}"
        logger.info("\n✅ Test PASSED!")

if __name__ == "__main__":
    # First extract frames if needed
    frames_info_path = FRAMES_DIR / "frames_info.json"
    if not frames_info_path.exists():
        logger.info("Extracting frames from test video...")
        os.system("pdm run python tests/extract_video_frames.py")
    
    # Run test
    asyncio.run(test_swing_detection())