import asyncio
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.fixtures.server_fixture import TestServer
from tests.test_swing_detection_ws import SwingDetectionTestClient
from tests.utils.video_frame_extractor import VideoFrameExtractor

async def test_with_detailed_logging():
    # Start server
    server = TestServer()
    server.start()
    
    # Extract frames
    extractor = VideoFrameExtractor()
    extractor.cleanup_output_dir('test_video')
    video_config = extractor.get_test_video_config('test_video')
    frames_path = extractor.extract_frames(video_config['path'], 'test_video')
    
    # Create client
    client = SwingDetectionTestClient()
    frames = client.load_frames(frames_path)[:40]  # Test with first 40 frames
    
    print(f'Loaded {len(frames)} frames')
    
    # Connect
    ws_url = server.get_ws_url('/ws/detect-golf-swing')
    await client.connect(ws_url)
    
    # Send frames with detailed logging
    for i, frame in enumerate(frames):
        print(f'\nSending frame {i} at timestamp {frame["timestamp"]:.2f}s')
        await client.send_frame(frame['timestamp'], frame['image_base64'])
        response = await client.receive_response()
        print(f'  Response: {response}')
        
        if response.get('status') == 'analyzing':
            # Wait for analysis to complete
            print('  Waiting for analysis to complete...')
            max_wait = 30  # seconds
            start_time = asyncio.get_event_loop().time()
            
            while True:
                # Send another frame to check status
                next_frame_idx = (i + 1) % len(frames)
                next_frame = frames[next_frame_idx]
                await client.send_frame(next_frame['timestamp'], next_frame['image_base64'])
                check_response = await client.receive_response()
                
                if check_response.get('status') != 'analyzing':
                    print(f'  Analysis complete: {check_response}')
                    break
                    
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > max_wait:
                    print(f'  ERROR: Analysis timed out after {max_wait}s')
                    break
                    
                await asyncio.sleep(0.1)
    
    # Cleanup
    await client.disconnect()
    server.stop()
    extractor.cleanup_output_dir('test_video')

asyncio.run(test_with_detailed_logging())