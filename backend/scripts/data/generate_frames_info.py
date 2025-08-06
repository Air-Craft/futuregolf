#!/usr/bin/env python3
"""Generate frames_info.json from existing frame files"""

import json
import os
from pathlib import Path

frames_dir = Path("tests/fixtures/swing-detection/test_movie001")

# Get all jpg files and sort them
frame_files = sorted(frames_dir.glob("*.jpg"))

frames_info = []
for i, frame_file in enumerate(frame_files):
    # Extract timestamp from filename (format: 000-00.jpg means 0.00 seconds)
    filename = frame_file.name
    parts = filename.replace('.jpg', '').split('-')
    seconds = int(parts[0])
    centiseconds = int(parts[1])
    timestamp = seconds + centiseconds / 100.0
    
    frames_info.append({
        "filename": filename,
        "timestamp": timestamp,
        "frame_number": i
    })

# Save as JSON
output_file = frames_dir / "frames_info.json"
with open(output_file, 'w') as f:
    json.dump(frames_info, f, indent=2)

print(f"Generated {output_file} with {len(frames_info)} frames")