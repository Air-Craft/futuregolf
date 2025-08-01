"""
Extract frames from video for swing detection testing
Based on AI_SWING_DETECTION.md testing requirements
"""

import cv2
import os
import sys
from pathlib import Path
from typing import List, Tuple
import shutil
from PIL import Image
import io
import base64

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.swing_detection import IOS_FRAME_INTERVAL, IMAGE_MAX_SIZE, IMAGE_JPEG_QUALITY

def extract_frames_with_json(video_path: str, output_dir: str, interval: float = IOS_FRAME_INTERVAL) -> List[dict]:
    """Extract frames and save JSON info file"""
    frames_info = extract_frames(video_path, output_dir, interval)
    
    # Save frame info for tests
    import json
    info_file = os.path.join(output_dir, "frames_info.json")
    with open(info_file, 'w') as f:
        # Don't save base64 in JSON to keep file size small
        frames_data = [
            {
                'timestamp': f['timestamp'],
                'filename': f['filename']
            }
            for f in frames_info
        ]
        json.dump(frames_data, f, indent=2)
    
    print(f"\nFrame info saved to: {info_file}")
    return frames_info

def extract_frames(video_path: str, output_dir: str, interval: float = IOS_FRAME_INTERVAL) -> List[dict]:
    """
    Extract frames from video at specified interval
    
    Args:
        video_path: Path to input video
        output_dir: Directory to save frames
        interval: Time interval between frames in seconds
        
    Returns:
        List of frame info dicts with timestamp and filename
    """
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"Video properties:")
    print(f"  FPS: {fps}")
    print(f"  Total frames: {total_frames}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Extracting frames every {interval} seconds")
    
    frames_info = []
    frame_count = 0
    
    # Calculate frame interval
    frame_interval = int(fps * interval)
    
    while True:
        # Set frame position
        frame_pos = frame_count * frame_interval
        if frame_pos >= total_frames:
            break
            
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        
        # Read frame
        ret, frame = cap.read()
        if not ret:
            break
        
        # Calculate timestamp
        timestamp = frame_pos / fps
        
        # Format filename with timestamp
        timestamp_str = f"{int(timestamp):03d}-{int((timestamp % 1) * 100):02d}"
        filename = f"{timestamp_str}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        # Convert to PIL Image for resizing
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        
        # Resize maintaining aspect ratio (same as iOS app)
        pil_image.thumbnail(IMAGE_MAX_SIZE, Image.Resampling.LANCZOS)
        
        # Save with compression
        pil_image.save(filepath, 'JPEG', quality=IMAGE_JPEG_QUALITY, optimize=True)
        
        # Also save as base64 for easy use in tests
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=IMAGE_JPEG_QUALITY, optimize=True)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        frames_info.append({
            'timestamp': timestamp,
            'filename': filename,
            'filepath': filepath,
            'image_base64': image_base64
        })
        
        print(f"Extracted frame at {timestamp:.2f}s -> {filename}")
        
        frame_count += 1
    
    cap.release()
    
    print(f"\nTotal frames extracted: {len(frames_info)}")
    return frames_info

def main():
    """Extract frames from test video"""
    
    # Paths
    test_video = "tests/fixtures/video/test_video.mov"
    output_dir = "tests/fixtures/swing-detection/test_movie001"
    
    # Clean up existing directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    # Extract frames
    frames_info = extract_frames(test_video, output_dir)
    
    # Save frame info for tests
    import json
    info_file = os.path.join(output_dir, "frames_info.json")
    with open(info_file, 'w') as f:
        # Don't save base64 in JSON to keep file size small
        frames_data = [
            {
                'timestamp': f['timestamp'],
                'filename': f['filename']
            }
            for f in frames_info
        ]
        json.dump(frames_data, f, indent=2)
    
    print(f"\nFrame info saved to: {info_file}")
    
    # Analyze swing detection windows
    print("\nSwing detection windows (1.25s intervals):")
    window_start = 0
    window_num = 1
    
    for i, frame in enumerate(frames_info):
        if frame['timestamp'] - window_start >= 1.25:
            print(f"  Window {window_num}: {window_start:.2f}s - {frame['timestamp']:.2f}s")
            window_start = frame['timestamp']
            window_num += 1

if __name__ == "__main__":
    main()