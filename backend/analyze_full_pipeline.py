#!/usr/bin/env python3
"""
Complete pipeline: MediaPipe pose detection + Gemini AI analysis + Video composition
"""

import asyncio
import sys
import os
import json
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pose_analysis_service import get_pose_analysis_service
from services.video_compositor import VideoCompositor

async def run_full_pipeline(video_path: str):
    """Run the complete analysis pipeline."""
    
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
    
    # Save pose results
    pose_results_path = video_path.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    with open(pose_results_path, 'w') as f:
        json.dump(pose_result, f, indent=2)
    print(f"💾 Pose data saved to: {pose_results_path}")
    
    # 2. Run Gemini analysis using the working analyze_video.py
    print("\n🤖 Running Gemini AI analysis...")
    print(f"Running: {sys.executable} analyze_video.py {video_path}")
    
    # Initialize variables
    analysis_path = video_path.replace('.mp4', '_analysis.json').replace('.mov', '_analysis.json')
    ai_analysis = {}
    
    result = subprocess.run(
        [sys.executable, "analyze_video.py", video_path],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    if result.returncode == 0:
        print("✅ AI analysis complete!")
        
        # Load the analysis results
        if os.path.exists(analysis_path):
            with open(analysis_path, 'r') as f:
                ai_analysis = json.load(f)
            
            # Show summary
            print(f"   - Overall quality: {ai_analysis.get('overall_quality', 'N/A')}")
            print(f"   - Swing phases detected: {len(ai_analysis.get('swing_phases', []))}")
    else:
        print(f"❌ AI analysis failed with return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        # Don't return, continue with what we have
    
    # 3. Create composite video with overlays
    print("\n🎬 Creating output video with overlays...")
    compositor = VideoCompositor()
    
    output_path = video_path.replace('.mp4', '_analyzed.mp4').replace('.mov', '_analyzed.mp4')
    
    # Prepare data for compositor
    swing_phases = ai_analysis.get('swing_phases', [])
    key_issues = ai_analysis.get('key_issues', [])
    
    composite_result = await compositor.composite_video(
        video_path,
        output_path,
        swing_phases,
        key_issues
    )
    
    if composite_result['success']:
        print(f"✅ Output video created: {output_path}")
    
    # 4. Save combined results
    combined_results = {
        "video_path": video_path,
        "pose_analysis": pose_result,
        "ai_analysis": ai_analysis,
        "output_video": output_path
    }
    
    results_path = video_path.replace('.mp4', '_complete.json').replace('.mov', '_complete.json')
    with open(results_path, 'w') as f:
        json.dump(combined_results, f, indent=2)
    
    print(f"\n📊 Complete results saved to: {results_path}")
    print("\n🎉 Analysis complete! You now have:")
    print(f"   - Pose data: {pose_results_path}")
    print(f"   - AI analysis: {analysis_path}")
    print(f"   - Analyzed video: {output_path}")
    print(f"   - Combined results: {results_path}")
    print("\n   Real MediaPipe body tracking + Gemini AI insights!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_full_pipeline.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    asyncio.run(run_full_pipeline(video_path))