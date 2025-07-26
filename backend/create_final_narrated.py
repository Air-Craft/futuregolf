#!/usr/bin/env python3
"""
Create the final narrated analysis video:
1. Original swing with MediaPipe overlay
2. Slow motion replay 
3. Freeze frame with commentary
All with professional narration throughout.
"""

import os
import sys
import json
import asyncio
import subprocess
from dotenv import load_dotenv

load_dotenv()

class FinalNarratedVideo:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
    def create_commentary_script(self, analysis_data, pose_data):
        """Create commentary matching video segments."""
        swings = analysis_data.get('swings', [])
        summary = analysis_data.get('summary', {})
        angle_analysis = pose_data.get('angle_analysis', {})
        
        if not swings:
            return "No swing data available."
        
        swing = swings[0]
        score = swing.get('score', 'N/A')
        comments = swing.get('comments', [])
        highlights = summary.get('highlights', [])
        improvements = summary.get('improvements', [])
        
        # Get spine angles
        spine_angles = angle_analysis.get('spine_angle', {})
        setup_angle = spine_angles.get('setup', {}).get('angle', 'N/A')
        impact_angle = spine_angles.get('impact', {}).get('angle', 'N/A')
        
        # Build commentary for each segment
        script = "Welcome to your golf swing analysis. "
        script += f"I'll be using advanced biomechanical tracking to evaluate your swing. "
        script += f"Overall, I rate this swing a {score} out of 10. "
        
        # During slow motion
        script += f"Now in slow motion, notice your spine angle at setup is {setup_angle:.0f} degrees. "
        script += f"By impact, it changes to {impact_angle:.0f} degrees. "
        
        # Analysis section
        if highlights:
            script += "What you're doing well: "
            script += ". ".join(highlights) + ". "
        
        if improvements:
            script += "Key areas to improve: "
            for imp in improvements[:2]:
                script += imp + ". "
        
        if comments:
            script += "My specific recommendations: "
            script += ". ".join(comments) + ". "
        
        script += "Keep working on these adjustments and you'll see great improvement."
        
        return script
    
    async def generate_tts_openai(self, text, output_path):
        """Generate speech using OpenAI TTS."""
        import openai
        
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            speed=0.95  # Slightly slower for clarity
        )
        
        response.stream_to_file(output_path)
        return True
    
    async def create_final_video(self, original_video, pose_overlay_video, analysis_path, pose_path, output_path):
        """Create the final narrated video with all elements."""
        
        print("📊 Loading analysis data...")
        with open(analysis_path, 'r') as f:
            analysis_data = json.load(f)
        
        with open(pose_path, 'r') as f:
            pose_data = json.load(f)
        
        # Generate commentary
        print("✍️  Creating commentary script...")
        script = self.create_commentary_script(analysis_data, pose_data)
        print(f"Script: {len(script.split())} words")
        
        # Generate TTS
        print("🎙️  Generating narration...")
        audio_path = original_video.replace('.mp4', '_final_narration.mp3')
        await self.generate_tts_openai(script, audio_path)
        
        # Get audio duration
        audio_probe = ['ffprobe', '-v', 'error', '-show_entries', 
                      'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                      audio_path]
        audio_duration = float(subprocess.check_output(audio_probe).decode().strip())
        print(f"🎵 Audio duration: {audio_duration:.1f} seconds")
        
        # Create video segments
        print("🎬 Creating video segments...")
        
        # Segment 1: Original with MediaPipe overlay (5 seconds)
        seg1_path = original_video.replace('.mp4', '_final_seg1.mp4')
        cmd = [
            'ffmpeg', '-i', pose_overlay_video,
            '-vf', "drawtext=text='BIOMECHANICAL ANALYSIS':fontsize=40:fontcolor=white:box=1:boxcolor=black@0.7:x=(w-text_w)/2:y=50",
            '-t', '5', '-an', '-y', seg1_path
        ]
        subprocess.run(cmd, check=True)
        
        # Segment 2: Slow motion with overlay (8 seconds)
        seg2_path = original_video.replace('.mp4', '_final_seg2.mp4')
        cmd = [
            'ffmpeg', '-i', pose_overlay_video,
            '-filter_complex', "[0:v]setpts=2.5*PTS,drawtext=text='SLOW MOTION ANALYSIS':fontsize=30:fontcolor=yellow:x=20:y=20[v]",
            '-map', '[v]', '-t', '8', '-an', '-y', seg2_path
        ]
        subprocess.run(cmd, check=True)
        
        # Segment 3: Freeze on impact with full analysis overlay
        remaining_time = max(audio_duration - 13, 5)  # At least 5 seconds
        seg3_path = original_video.replace('.mp4', '_final_seg3.mp4')
        
        # Get impact frame from pose overlay
        impact_time = 3.0
        impact_frame = original_video.replace('.mp4', '_final_impact.jpg')
        cmd = [
            'ffmpeg', '-i', pose_overlay_video,
            '-ss', str(impact_time), '-frames:v', '1',
            '-y', impact_frame
        ]
        subprocess.run(cmd, check=True)
        
        # Create analysis text
        score = analysis_data.get('swings', [{}])[0].get('score', 'N/A')
        improvements = analysis_data.get('summary', {}).get('improvements', [])
        
        analysis_text = f"SCORE: {score}/10"
        if improvements:
            # Remove apostrophes to avoid ffmpeg issues
            improvement_text = improvements[0][:50].replace("'", "")
            analysis_text += " | " + improvement_text
        
        # Use simple text to avoid ffmpeg parsing issues
        cmd = [
            'ffmpeg', '-loop', '1', '-i', impact_frame,
            '-vf', f"drawtext=text='ANALYSIS - Score {score}/10':fontsize=35:fontcolor=white:box=1:boxcolor=black@0.7:x=(w-text_w)/2:y=100",
            '-t', str(remaining_time), '-pix_fmt', 'yuv420p',
            '-an', '-y', seg3_path
        ]
        subprocess.run(cmd, check=True)
        
        # Concatenate segments
        print("🎬 Combining segments...")
        segments = [seg1_path, seg2_path, seg3_path]
        concat_file = original_video.replace('.mp4', '_final_concat.txt')
        with open(concat_file, 'w') as f:
            for seg in segments:
                f.write(f"file '{os.path.abspath(seg)}'\n")
        
        # Create video without audio first
        temp_video = original_video.replace('.mp4', '_final_temp.mp4')
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', concat_file, '-c:v', 'copy',
            '-y', temp_video
        ]
        subprocess.run(cmd, check=True)
        
        # Add narration to the entire video
        print("🎤 Adding narration...")
        cmd = [
            'ffmpeg', '-i', temp_video, '-i', audio_path,
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
            '-shortest',  # Stop when video ends
            '-y', output_path
        ]
        subprocess.run(cmd, check=True)
        
        # Cleanup
        for seg in segments:
            os.remove(seg)
        os.remove(concat_file)
        os.remove(temp_video)
        os.remove(impact_frame)
        os.remove(audio_path)
        
        total_duration = 5 + 8 + remaining_time
        print(f"✅ Final narrated analysis created: {output_path}")
        print(f"   Total duration: {total_duration:.0f} seconds")
        print(f"   - Original with skeleton: 5 sec")
        print(f"   - Slow motion analysis: 8 sec")
        print(f"   - Detailed breakdown: {remaining_time:.0f} sec")
        print(f"   - Professional narration throughout")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python create_final_narrated.py <original_video_path>")
        print("   Expects _pose_overlay.mp4, _pose.json, and _analysis.json files")
        sys.exit(1)
    
    original_video = sys.argv[1]
    pose_overlay = original_video.replace('.mp4', '_pose_overlay.mp4').replace('.mov', '_pose_overlay.mp4')
    analysis_path = original_video.replace('.mp4', '_analysis.json').replace('.mov', '_analysis.json')
    pose_path = original_video.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    output_path = original_video.replace('.mp4', '_final_narrated.mp4').replace('.mov', '_final_narrated.mp4')
    
    # Check files exist
    for path, name in [(pose_overlay, "Pose overlay video"), 
                       (analysis_path, "Analysis data"),
                       (pose_path, "Pose data")]:
        if not os.path.exists(path):
            print(f"❌ {name} not found: {path}")
            sys.exit(1)
    
    creator = FinalNarratedVideo()
    await creator.create_final_video(original_video, pose_overlay, analysis_path, pose_path, output_path)

if __name__ == "__main__":
    asyncio.run(main())