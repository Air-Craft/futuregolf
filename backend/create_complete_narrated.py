#!/usr/bin/env python3
"""
Create narrated video that plays full commentary without cutting off.
Video sections adjust to match narration length.
"""

import os
import sys
import json
import asyncio
import subprocess
from dotenv import load_dotenv

load_dotenv()

class CompleteNarratedVideo:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
    def create_commentary_script(self, analysis_data, pose_data):
        """Create full commentary script."""
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
        
        # Build comprehensive commentary
        script = "Welcome to your golf swing analysis powered by advanced biomechanical tracking. "
        script += f"Overall, I rate this swing a {score} out of 10. "
        
        # Positive feedback
        if highlights:
            script += "Let's start with what you're doing well. "
            for highlight in highlights:
                script += highlight + ". "
        
        # Technical analysis
        script += f"Looking at your biomechanics, your spine angle at setup is {setup_angle:.0f} degrees. "
        script += f"By impact, it changes to {impact_angle:.0f} degrees. "
        script += "This indicates some loss of posture through the swing. "
        
        # Areas for improvement
        if improvements:
            script += "Here are the key areas to focus on in practice. "
            for i, imp in enumerate(improvements, 1):
                script += f"Number {i}: {imp}. "
        
        # Specific coaching tips
        if comments:
            script += "My coaching recommendations are: "
            for comment in comments:
                script += comment + ". "
        
        # Closing
        script += "Remember, improvement comes with consistent practice. "
        script += "Focus on one change at a time, and you'll see steady progress. "
        script += "Keep up the good work!"
        
        return script
    
    async def generate_tts_openai(self, text, output_path):
        """Generate speech using OpenAI TTS."""
        import openai
        
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            speed=0.9  # Slower for clarity
        )
        
        response.stream_to_file(output_path)
        return True
    
    async def create_complete_video(self, original_video, pose_overlay_video, analysis_path, pose_path, output_path):
        """Create video that matches narration length."""
        
        print("📊 Loading analysis data...")
        with open(analysis_path, 'r') as f:
            analysis_data = json.load(f)
        
        with open(pose_path, 'r') as f:
            pose_data = json.load(f)
        
        # Generate commentary
        print("✍️  Creating full commentary script...")
        script = self.create_commentary_script(analysis_data, pose_data)
        print(f"Script: {len(script.split())} words (~{len(script.split())//2.5:.0f} seconds)")
        
        # Generate TTS
        print("🎙️  Generating narration...")
        audio_path = original_video.replace('.mp4', '_complete_narration.mp3')
        await self.generate_tts_openai(script, audio_path)
        
        # Get audio duration
        audio_probe = ['ffprobe', '-v', 'error', '-show_entries', 
                      'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                      audio_path]
        audio_duration = float(subprocess.check_output(audio_probe).decode().strip())
        print(f"🎵 Audio duration: {audio_duration:.1f} seconds")
        
        # Calculate segment durations to match audio
        seg1_duration = 5  # Original speed
        seg2_duration = 10  # Slow motion
        seg3_duration = max(audio_duration - seg1_duration - seg2_duration, 10)  # Rest on freeze frame
        
        print(f"📹 Video structure: {seg1_duration}s + {seg2_duration}s + {seg3_duration:.1f}s = {seg1_duration + seg2_duration + seg3_duration:.1f}s")
        
        # Create video to match audio length exactly
        print("🎬 Creating video with MediaPipe overlay...")
        
        # First, create the visual-only video
        temp_video = original_video.replace('.mp4', '_complete_temp.mp4')
        
        # Segment 1: Original speed (5s)
        seg1_cmd = [
            'ffmpeg', '-i', pose_overlay_video,
            '-t', str(seg1_duration),
            '-c:v', 'copy', '-an',
            '-y', original_video.replace('.mp4', '_seg1_temp.mp4')
        ]
        subprocess.run(seg1_cmd, check=True)
        
        # Segment 2: Slow motion (10s)
        seg2_cmd = [
            'ffmpeg', '-i', pose_overlay_video,
            '-filter:v', 'setpts=2*PTS',
            '-t', str(seg2_duration),
            '-an', '-y', original_video.replace('.mp4', '_seg2_temp.mp4')
        ]
        subprocess.run(seg2_cmd, check=True)
        
        # Segment 3: Hold on last frame
        # Extract last frame
        last_frame = original_video.replace('.mp4', '_last_frame.jpg')
        cmd = [
            'ffmpeg', '-sseof', '-0.1', '-i', pose_overlay_video,
            '-frames:v', '1', '-y', last_frame
        ]
        subprocess.run(cmd, check=True)
        
        # Create static video from last frame
        seg3_cmd = [
            'ffmpeg', '-loop', '1', '-i', last_frame,
            '-c:v', 'libx264', '-t', str(seg3_duration),
            '-pix_fmt', 'yuv420p', '-vf', 'scale=720:1280',
            '-y', original_video.replace('.mp4', '_seg3_temp.mp4')
        ]
        subprocess.run(seg3_cmd, check=True)
        
        # Concatenate all segments
        concat_list = original_video.replace('.mp4', '_concat_list.txt')
        with open(concat_list, 'w') as f:
            f.write(f"file '{os.path.abspath(original_video.replace('.mp4', '_seg1_temp.mp4'))}'\n")
            f.write(f"file '{os.path.abspath(original_video.replace('.mp4', '_seg2_temp.mp4'))}'\n")
            f.write(f"file '{os.path.abspath(original_video.replace('.mp4', '_seg3_temp.mp4'))}'\n")
        
        concat_cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', concat_list, '-c:v', 'copy',
            '-y', temp_video
        ]
        subprocess.run(concat_cmd, check=True)
        
        # Add narration to match video length
        print("🎤 Adding complete narration...")
        final_cmd = [
            'ffmpeg', '-i', temp_video, '-i', audio_path,
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'copy', '-c:a', 'aac',
            '-shortest',  # Use shorter of the two
            '-y', output_path
        ]
        subprocess.run(final_cmd, check=True)
        
        # Cleanup
        for f in [last_frame, concat_list, temp_video, audio_path,
                  original_video.replace('.mp4', '_seg1_temp.mp4'),
                  original_video.replace('.mp4', '_seg2_temp.mp4'),
                  original_video.replace('.mp4', '_seg3_temp.mp4')]:
            if os.path.exists(f):
                os.remove(f)
        
        print(f"✅ Complete narrated analysis created: {output_path}")
        print(f"   Duration: {audio_duration:.1f} seconds")
        print(f"   - MediaPipe skeleton overlay throughout")
        print(f"   - Full narration without cutoff")
        print(f"   - Ready for WhatsApp sharing")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python create_complete_narrated.py <original_video_path>")
        sys.exit(1)
    
    original_video = sys.argv[1]
    pose_overlay = original_video.replace('.mp4', '_pose_overlay.mp4').replace('.mov', '_pose_overlay.mp4')
    analysis_path = original_video.replace('.mp4', '_analysis.json').replace('.mov', '_analysis.json')
    pose_path = original_video.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    output_path = original_video.replace('.mp4', '_complete_narrated.mp4').replace('.mov', '_complete_narrated.mp4')
    
    # Check files exist
    for path, name in [(pose_overlay, "Pose overlay video"), 
                       (analysis_path, "Analysis data"),
                       (pose_path, "Pose data")]:
        if not os.path.exists(path):
            print(f"❌ {name} not found: {path}")
            sys.exit(1)
    
    creator = CompleteNarratedVideo()
    await creator.create_complete_video(original_video, pose_overlay, analysis_path, pose_path, output_path)

if __name__ == "__main__":
    asyncio.run(main())