#!/usr/bin/env python3
"""
Analyze video with both MediaPipe pose detection and Gemini AI.
This gives you the full "sciencey" analysis with real body tracking.
"""

import asyncio
import sys
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pose_analysis_service import get_pose_analysis_service
from services.video_compositor import VideoCompositor
import cv2

try:
    from google import genai
    from google.genai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("❌ Google Gemini AI not available. Install google-genai package.")
    sys.exit(1)

async def analyze_with_full_pipeline(video_path: str):
    """Run full analysis with MediaPipe + Gemini."""
    
    # Check file exists
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return
        
    print(f"🎥 Analyzing: {video_path}\n")
    
    # 1. MediaPipe Pose Analysis
    print("🏃 Running MediaPipe pose detection...")
    pose_service = get_pose_analysis_service()
    pose_result = await pose_service.analyze_video_pose(video_path)
    
    if pose_result.get('success'):
        print("✅ Pose detection complete!")
        print(f"   - Analyzed {pose_result.get('analysis_metadata', {}).get('total_frames', 0)} frames")
        print(f"   - Found swing phases: {list(pose_result.get('swing_phases', {}).keys())}")
        
        # Show some angle data
        angles = pose_result.get('angle_analysis', {})
        if angles.get('spine_angle'):
            for phase, data in angles['spine_angle'].items():
                print(f"   - {phase} spine angle: {data.get('angle', 0):.1f}°")
    else:
        print("⚠️  Pose detection failed, using mock data")
    
    # 2. Gemini AI Analysis
    print("\n🤖 Running Gemini AI analysis...")
    
    # Initialize Gemini client
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY not found")
        return
        
    client = genai.Client(api_key=gemini_api_key)
    
    # Load prompt
    import aiofiles
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "video_analysis_swing_coaching.txt")
    async with aiofiles.open(prompt_path, 'r') as f:
        prompt_template = await f.read()
    
    # Get video info
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    cap.release()
    
    # Format prompt - need to escape the curly braces in JSON
    escaped_prompt = prompt_template.replace('{', '{{').replace('}', '}}')
    # Now replace the actual placeholders
    escaped_prompt = escaped_prompt.replace('{{duration}}', '{duration}')
    escaped_prompt = escaped_prompt.replace('{{frame_rate}}', '{frame_rate}')
    
    prompt = escaped_prompt.format(
        duration=f"{duration:.2f}",
        frame_rate=f"{fps:.1f}"
    )
    
    # Upload video
    print("📤 Uploading video to Gemini...")
    video_file = await client.aio.files.upload(file=video_path)
    
    # Wait for processing
    while video_file.state.name == "PROCESSING":
        await asyncio.sleep(2)
        video_file = await client.aio.files.get(name=video_file.name)
    
    # Generate analysis
    print("🚀 Calling Gemini API...")
    
    # Use same format as analyze_video.py
    generation_config = {
        "response_mime_type": "application/json"
    }
    
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[video_file, prompt],
        config=generation_config,
        safety_settings=safety_settings
    )
    
    # Parse response
    ai_analysis = json.loads(response.text)
    ai_result = {"success": True, "analysis": ai_analysis}
    
    # Clean up
    await client.aio.files.delete(name=video_file.name)
    
    if ai_result.get('success'):
        print("✅ AI analysis complete!")
        analysis = ai_result.get('analysis', {})
        print(f"   - Overall quality: {analysis.get('overall_quality', 'N/A')}")
        print(f"   - Swing phases detected: {len(analysis.get('swing_phases', []))}")
    
    # 3. Create composite video with overlays
    print("\n🎬 Creating output video with overlays...")
    compositor = VideoCompositor()
    
    output_path = video_path.replace('.mp4', '_analyzed.mp4').replace('.mov', '_analyzed.mp4')
    
    # Prepare data for compositor
    ai_analysis = ai_result.get('analysis', {})
    swing_phases = ai_analysis.get('swing_phases', [])
    key_issues = ai_analysis.get('key_issues', [])
    
    composite_result = await compositor.create_composite_video(
        video_path,
        output_path,
        swing_phases,
        key_issues
    )
    
    if composite_result['success']:
        print(f"✅ Output video created: {output_path}")
    
    # 4. Save complete results
    results = {
        "video_path": video_path,
        "pose_analysis": pose_result,
        "ai_analysis": ai_result,
        "output_video": output_path
    }
    
    results_path = video_path.replace('.mp4', '_full_analysis.json').replace('.mov', '_full_analysis.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Full results saved to: {results_path}")
    print("\n🎉 Analysis complete! You now have:")
    print(f"   - Analyzed video: {output_path}")
    print(f"   - Full analysis data: {results_path}")
    print("   - Real MediaPipe pose detection data")
    print("   - Gemini AI coaching insights")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_with_pose.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    asyncio.run(analyze_with_full_pipeline(video_path))