"""
Extract frames from video for testing
Mimics iOS app frame extraction behavior
"""

import cv2
import os
import json
import yaml
import base64
from pathlib import Path
from PIL import Image
from io import BytesIO
import logging
import shutil

logger = logging.getLogger(__name__)


class VideoFrameExtractor:
    """Extract frames from video files for testing"""
    
    def __init__(self, config_path: str = "tests/config/test_frame_extraction.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.fps = self.config['frame_extraction']['fps']
        self.image_config = self.config['frame_extraction']['image_processing']
        self.output_dir = Path(self.config['frame_extraction']['output_dir'])
    
    def cleanup_output_dir(self, video_name: str):
        """Clean up extracted frames for a video"""
        video_dir = self.output_dir / video_name
        if video_dir.exists():
            logger.info(f"Cleaning up existing frames in {video_dir}")
            shutil.rmtree(video_dir)
    
    def extract_frames(self, video_path: str, video_name: str) -> Path:
        """Extract frames from video file"""
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Create output directory
        output_path = self.output_dir / video_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        # Get video properties
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps if video_fps > 0 else 0
        
        logger.info(f"Video: {video_path.name}")
        logger.info(f"  FPS: {video_fps}, Total frames: {total_frames}, Duration: {duration:.2f}s")
        logger.info(f"  Extracting at {self.fps} fps (every {1/self.fps:.2f}s)")
        
        # Calculate frame interval
        frame_interval = int(video_fps / self.fps)
        
        frames_info = []
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract frame at specified interval
            if frame_count % frame_interval == 0:
                timestamp = frame_count / video_fps
                
                # Process frame (mimicking iOS app)
                processed_frame = self._process_frame(frame)
                
                # Save frame
                filename = f"frame_{extracted_count:03d}.webp"
                filepath = output_path / filename
                processed_frame.save(filepath, 'WEBP', quality=self.image_config['quality'])
                
                # Get base64 for frames_info
                buffer = BytesIO()
                processed_frame.save(buffer, 'WEBP', quality=self.image_config['quality'])
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                frames_info.append({
                    "filename": filename,
                    "timestamp": timestamp,
                    "frame_number": extracted_count,
                    "image_base64": image_base64
                })
                
                extracted_count += 1
            
            frame_count += 1
        
        cap.release()
        
        # Save frames info
        frames_info_path = output_path / "frames_info.json"
        with open(frames_info_path, 'w') as f:
            json.dump(frames_info, f, indent=2)
        
        logger.info(f"Extracted {extracted_count} frames to {output_path}")
        return output_path
    
    def _process_frame(self, frame):
        """Process frame to match iOS app behavior"""
        # Convert from BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        
        # Convert to grayscale if configured
        if self.image_config['convert_bw']:
            pil_image = pil_image.convert('L')
        
        # Resize to fit within max_size box (maintaining aspect ratio)
        max_width, max_height = self.image_config['max_size']
        original_width, original_height = pil_image.size
        
        # Calculate scale to fit within box
        scale = min(max_width / original_width, max_height / original_height)
        
        # Only resize if image is larger than box
        if scale < 1:
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return pil_image
    
    def get_test_video_config(self, video_name: str) -> dict:
        """Get configuration for a specific test video"""
        for video in self.config['frame_extraction']['test_videos']:
            if video['name'] == video_name:
                return video
        raise ValueError(f"Test video not found in config: {video_name}")


if __name__ == "__main__":
    # Test extraction
    import logging
    logging.basicConfig(level=logging.INFO)
    
    extractor = VideoFrameExtractor()
    
    # Extract from test_video.mov
    video_config = extractor.get_test_video_config("test_video")
    extractor.cleanup_output_dir("test_video")
    output_path = extractor.extract_frames(video_config['path'], "test_video")
    print(f"Frames extracted to: {output_path}")