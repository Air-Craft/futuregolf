#!/bin/bash

# Make WhatsApp-compatible video
# Usage: ./make_whatsapp_video.sh input.mp4

if [ $# -eq 0 ]; then
    echo "Usage: $0 <input_video.mp4>"
    exit 1
fi

INPUT="$1"
OUTPUT="${INPUT%.*}_whatsapp.mp4"

echo "🎬 Converting to WhatsApp format..."
ffmpeg -i "$INPUT" \
    -c:v libx264 -profile:v baseline -level 3.0 \
    -pix_fmt yuv420p \
    -vf "scale=720:-2" \
    -c:a aac -b:a 128k -ar 44100 -ac 2 \
    -movflags +faststart \
    -brand mp42 \
    -y "$OUTPUT" 2>/dev/null

if [ $? -eq 0 ]; then
    SIZE=$(ls -lh "$OUTPUT" | awk '{print $5}')
    echo "✅ WhatsApp video created: $OUTPUT ($SIZE)"
    echo "📱 Ready to share!"
else
    echo "❌ Conversion failed"
fi