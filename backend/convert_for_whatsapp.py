#!/usr/bin/env python3
"""
Convert video to WhatsApp-compatible format.
WhatsApp supports MP4 with H.264 codec.
"""

import subprocess
import sys
import os

def convert_for_whatsapp(input_path: str, output_path: str = None):
    """Convert video to WhatsApp-compatible MP4."""
    
    if not os.path.exists(input_path):
        print(f"❌ Video not found: {input_path}")
        return
    
    if output_path is None:
        # Default output name
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_whatsapp.mp4"
    
    print(f"📹 Converting: {input_path}")
    print(f"📱 Output: {output_path}")
    
    # FFmpeg command for WhatsApp compatibility
    # - H.264 video codec
    # - AAC audio codec (even though we don't have audio)
    # - Reasonable bitrate for quality/size balance
    # - Max 16MB file size recommended for WhatsApp
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',      # H.264 codec
        '-preset', 'medium',     # Balance between speed and compression
        '-crf', '23',           # Quality (lower = better, 23 is good balance)
        '-c:a', 'aac',          # AAC audio codec
        '-b:a', '128k',         # Audio bitrate
        '-movflags', '+faststart',  # Enable streaming
        '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
        '-vf', 'scale=720:-2',  # Scale to 720p width (WhatsApp will compress anyway)
        '-y',                   # Overwrite output
        output_path
    ]
    
    try:
        print("🔄 Converting...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Get file size
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"✅ Conversion complete!")
            print(f"📊 File size: {size_mb:.1f} MB")
            
            if size_mb > 16:
                print("⚠️  File is larger than 16MB - WhatsApp might compress it further")
            
            print(f"\n📱 Ready to share on WhatsApp: {output_path}")
        else:
            print(f"❌ Conversion failed:")
            print(result.stderr)
            
    except FileNotFoundError:
        print("❌ FFmpeg not found. Install it with: brew install ffmpeg")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_for_whatsapp.py <video_path> [output_path]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_for_whatsapp(input_path, output_path)