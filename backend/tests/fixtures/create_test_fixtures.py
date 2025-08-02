#!/usr/bin/env python3
"""
Create test fixtures for swing detection tests
This ensures test frames are always available
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_test_frames():
    """Create dummy test frames for swing detection testing"""
    
    # Create output directory
    output_dir = Path(__file__).parent / "swing-detection" / "test_movie001"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    frames_info = []
    
    # Create 50 simple test frames to simulate a longer video
    for i in range(50):
        # Create a simple image with text
        img = Image.new('RGB', (640, 480), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add frame number text
        text = f"Frame {i}"
        try:
            # Try to use a default font
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        except:
            # Fallback to default font
            font = None
        
        # Draw text in center
        draw.text((320, 240), text, fill='black', font=font, anchor='mm')
        
        # Add a circle that moves (simulating motion)
        x = 100 + (i * 8) % 440  # Move across screen and wrap
        y = 200 + (i * 3) % 200  # Move vertically
        draw.ellipse([x-20, y-20, x+20, y+20], fill='red')
        
        # Add additional motion elements to simulate a swing
        if 10 <= i <= 20:  # Simulate backswing
            draw.arc([200, 150, 400, 350], start=180, end=270, fill='blue', width=5)
        elif 20 < i <= 30:  # Simulate downswing
            draw.arc([200, 150, 400, 350], start=270, end=360, fill='green', width=5)
        
        # Save the frame
        timestamp = i * 0.2  # 0.2 second intervals
        filename = f"frame_{i:03d}.jpg"
        filepath = output_dir / filename
        img.save(filepath, 'JPEG', quality=85)
        
        # Add to frames info
        frames_info.append({
            "filename": filename,
            "timestamp": timestamp,
            "frame_number": i
        })
    
    # Save frames info
    frames_info_path = output_dir / "frames_info.json"
    with open(frames_info_path, 'w') as f:
        json.dump(frames_info, f, indent=2)
    
    print(f"Created {len(frames_info)} test frames in {output_dir}")
    print(f"Frames info saved to {frames_info_path}")
    return output_dir

if __name__ == "__main__":
    create_test_frames()