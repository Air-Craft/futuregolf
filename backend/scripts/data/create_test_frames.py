#!/usr/bin/env python3
"""Create dummy test frames for swing detection testing"""

from PIL import Image, ImageDraw, ImageFont
import os

output_dir = "tests/fixtures/swing-detection/test_movie001"

# Create 11 simple test frames
for i in range(11):
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
    x = 100 + (i * 40)
    y = 200 + (i * 10)
    draw.ellipse([x-20, y-20, x+20, y+20], fill='red')
    
    # Save the frame
    filename = f"frame_{i}.jpg"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath, 'JPEG', quality=85)
    print(f"Created {filepath}")

print("Test frames created successfully!")