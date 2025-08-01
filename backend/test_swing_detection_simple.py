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
from PIL import Image
from io import BytesIO

# Image processing settings (matching iOS and server)
IMAGE_MAX_SIZE = (128, 128)  # Target box size for resizing
IMAGE_WEBP_QUALITY = 40  # WebP compression quality
IMAGE_CONVERT_BW = True  # Convert to grayscale

# Override frame interval to simulate faster capture
FRAME_INTERVAL = 0.2  # Match updated iOS setting

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
WS_URL = "ws://localhost:8001/ws/detect-golf-swing"
FRAMES_DIR = Path("tests/fixtures/swing-detection/test_movie001")

def process_image(image_path: Path) -> str:
    """Process image with resizing and compression matching client settings"""
    # Open image
    image = Image.open(image_path)
    
    # Convert to grayscale if enabled
    if IMAGE_CONVERT_BW:
        image = image.convert('L')
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Calculate new size maintaining aspect ratio (box fit)
    original_width, original_height = image.size
    box_width, box_height = IMAGE_MAX_SIZE
    
    # Calculate scale factor to fit within box
    scale = min(box_width / original_width, box_height / original_height)
    
    # Only resize if the image is larger than the box
    if scale < 1:
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Compress and encode to WebP (or JPEG for compatibility)
    buffer = BytesIO()
    try:
        # Try WebP first
        image.save(buffer, format='WEBP', quality=IMAGE_WEBP_QUALITY, method=6)
    except:
        # Fallback to JPEG if WebP not supported
        image.save(buffer, format='JPEG', quality=IMAGE_WEBP_QUALITY)
    
    # Get base64 encoded string
    compressed_bytes = buffer.getvalue()
    return base64.b64encode(compressed_bytes).decode('utf-8')

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
    logger.info(f"Frame interval: {FRAME_INTERVAL}s (simulating faster capture)")
    logger.info(f"LLM submission threshold: {LLM_SUBMISSION_THRESHOLD}s")
    logger.info(f"Post-detection cooldown: {POST_DETECTION_COOLDOWN}s")
    
    # Connect to WebSocket
    async with websockets.connect(WS_URL) as websocket:
        logger.info("Connected to WebSocket endpoint")
        
        swings_detected = 0
        detection_times = []
        frames_sent = 0
        start_time = time.time()
        
        # Send frames at the specified interval
        frame_index = 0
        simulated_time = 0.0
        analyzing = False
        last_image_base64 = None
        
        while (frame_index < len(frames_data) or analyzing) and swings_detected < 3:
            # Only send new frames if we have them
            if frame_index < len(frames_data):
                # Load and process image
                frame_info = frames_data[frame_index]
                image_path = FRAMES_DIR / frame_info['filename']
                image_base64 = process_image(image_path)
                last_image_base64 = image_base64
            
                # Send frame with simulated timestamp
                message = {
                    "timestamp": simulated_time,
                    "image_base64": image_base64
                }
                
                await websocket.send(json.dumps(message))
                frames_sent += 1
                
                # Advance time and frame
                simulated_time += FRAME_INTERVAL
                # Use all frames in sequence to have enough data
                frame_index += 1
            
            # If we're out of frames but still analyzing, we need to keep listening
            if frame_index >= len(frames_data) and analyzing:
                # Send last frame again to trigger server processing
                if last_image_base64:
                    message = {
                        "timestamp": simulated_time,
                        "image_base64": last_image_base64
                    }
                    await websocket.send(json.dumps(message))
                    simulated_time += FRAME_INTERVAL
            
            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            
            # Log response
            status = data.get('status', 'unknown')
            
            if status == 'cooldown':
                cooldown_remaining = data.get('cooldown_remaining', 0)
                logger.info(f"Frame {frames_sent} ({simulated_time:.2f}s): COOLDOWN - {cooldown_remaining:.1f}s remaining")
            elif status == 'analyzing':
                elapsed = data.get('elapsed_time', 0)
                buffer_size = data.get('buffer_size', 0)
                analyzing = True
                if frames_sent % 5 == 0:  # Log every 5th frame
                    logger.info(f"Frame {frames_sent} ({simulated_time:.2f}s): ANALYZING - {elapsed:.1f}s elapsed, buffer: {buffer_size}")
            elif status == 'evaluated':
                analyzing = False
                if data.get("swing_detected"):
                    swings_detected += 1
                    detection_times.append(simulated_time)
                    confidence = data.get('confidence', 0.0)
                    logger.info(f"\n🏌️ SWING {swings_detected} DETECTED at {simulated_time:.2f}s (confidence: {confidence:.2f})")
                    
                    # Client decides to stop after 3 swings
                    if swings_detected >= 3:
                        logger.info(f"\n✅ CLIENT: Detected {swings_detected} swings, disconnecting")
                        break
            elif status == 'awaiting_more_data':
                window = data.get('context_window', 0)
                analyzing = False
                if frames_sent % 5 == 0:  # Log every 5th frame
                    logger.info(f"Frame {frames_sent} ({simulated_time:.2f}s): Waiting - window: {window:.2f}s")
            else:
                logger.info(f"Frame {frames_sent} ({simulated_time:.2f}s): Status: {status}, Data: {data}")
            
            # Add a small delay to simulate real-time sending
            await asyncio.sleep(0.05)
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"\n📊 Test Summary:")
        logger.info(f"  Total frames sent: {frames_sent}")
        logger.info(f"  Total swings detected: {swings_detected}")
        logger.info(f"  Time elapsed: {elapsed_time:.2f}s")
        logger.info(f"  Detection times: {[f'{t:.2f}s' for t in detection_times]}")
        
        # Assert we detected at least 2 swings (limited by test video)
        assert swings_detected >= 2, f"Expected at least 2 swings, got {swings_detected}"
        logger.info("\n✅ Test PASSED!")

if __name__ == "__main__":
    # First extract frames if needed
    frames_info_path = FRAMES_DIR / "frames_info.json"
    if not frames_info_path.exists():
        logger.info("Extracting frames from test video...")
        os.system("pdm run python tests/extract_video_frames.py")
    
    # Run test
    asyncio.run(test_swing_detection())