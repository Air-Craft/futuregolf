#!/usr/bin/env python3
"""
Create narrated golf analysis video with ElevenLabs TTS.
Format: Swing replay → Freeze frame → Commentary with visuals
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import requests
import cv2
import numpy as np

load_dotenv()

class NarratedAnalysisCreator:
    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.elevenlabs_api_key:
            print("⚠️  ELEVENLABS_API_KEY not found - using OpenAI TTS instead")
            self.use_openai = True
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        else:
            self.use_openai = False
        
    def create_commentary_script(self, analysis_data):
        """Create a natural commentary script from analysis data."""
        swings = analysis_data.get('swings', [])
        summary = analysis_data.get('summary', {})
        
        if not swings:
            return "No swing data available."
        
        swing = swings[0]
        score = swing.get('score', 'N/A')
        comments = swing.get('comments', [])
        highlights = summary.get('highlights', [])
        improvements = summary.get('improvements', [])
        
        # Build natural commentary
        script = f"Let's analyze this golf swing. "
        script += f"Overall, I'd rate this a {score} out of 10. "
        
        # Positive feedback first
        if highlights:
            script += "Here's what you're doing well: "
            script += ". ".join(highlights) + ". "
        
        # Areas for improvement
        if improvements:
            script += "Now, let's focus on areas for improvement. "
            for imp in improvements[:2]:  # Top 2 improvements
                script += imp + ". "
        
        # Specific tips
        if comments:
            script += "Here are my coaching tips: "
            script += ". ".join(comments) + ". "
        
        script += "Keep practicing these adjustments, and you'll see significant improvement in your game."
        
        return script
    
    async def generate_tts_elevenlabs(self, text, output_path):
        """Generate speech using ElevenLabs API."""
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"❌ ElevenLabs TTS failed: {response.status_code}")
            return False
    
    async def generate_tts_openai(self, text, output_path):
        """Generate speech using OpenAI TTS as fallback."""
        import openai
        
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",  # Professional female voice
            input=text
        )
        
        response.stream_to_file(output_path)
        return True
    
    async def create_narrated_video(self, video_path, pose_data_path, analysis_data_path, output_path):
        """Create the full narrated analysis video."""
        
        print("📊 Loading analysis data...")
        with open(analysis_data_path, 'r') as f:
            analysis_data = json.load(f)
        
        # Generate commentary script
        print("✍️  Creating commentary script...")
        script = self.create_commentary_script(analysis_data)
        print(f"Script length: {len(script.split())} words (~{len(script.split())//2.5:.0f} seconds)")
        
        # Generate TTS audio
        print("🎙️  Generating narration...")
        audio_path = video_path.replace('.mp4', '_narration.mp3')
        
        if self.use_openai:
            await self.generate_tts_openai(script, audio_path)
        else:
            await self.generate_tts_elevenlabs(script, audio_path)
        
        # Get audio duration
        audio_duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                             audio_path]
        audio_duration = float(subprocess.check_output(audio_duration_cmd).decode().strip())
        print(f"🎵 Audio duration: {audio_duration:.1f} seconds")
        
        # Create video structure:
        # 1. Original swing (5 sec)
        # 2. Slow-motion replay (10 sec) 
        # 3. Freeze frame with commentary (audio_duration)
        
        # Get video info
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Create segments
        segments = []
        
        # Segment 1: Original speed with title
        print("🎬 Creating video segments...")
        seg1_path = video_path.replace('.mp4', '_seg1.mp4')
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', f"drawtext=text='Golf Swing Analysis':fontsize=40:fontcolor=white:box=1:boxcolor=black@0.5:x=(w-text_w)/2:y=50:enable='lt(t,3)'",
            '-t', '5', '-y', seg1_path
        ]
        subprocess.run(cmd, check=True)
        segments.append(seg1_path)
        
        # Segment 2: Slow motion replay
        seg2_path = video_path.replace('.mp4', '_seg2.mp4')
        cmd = [
            'ffmpeg', '-i', video_path,
            '-filter_complex', "[0:v]setpts=4*PTS,drawtext=text='SLOW MOTION':fontsize=30:fontcolor=yellow:x=20:y=20[v]",
            '-map', '[v]', '-t', '10', '-y', seg2_path
        ]
        subprocess.run(cmd, check=True)
        segments.append(seg2_path)
        
        # Segment 3: Freeze frame with audio
        seg3_path = video_path.replace('.mp4', '_seg3.mp4')
        
        # Extract impact frame
        impact_frame_path = video_path.replace('.mp4', '_impact.jpg')
        impact_time = 3.0  # Approximate impact time
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ss', str(impact_time), '-frames:v', '1',
            '-y', impact_frame_path
        ]
        subprocess.run(cmd, check=True)
        
        # Create freeze frame video with commentary overlay
        cmd = [
            'ffmpeg', '-loop', '1', '-i', impact_frame_path,
            '-i', audio_path,
            '-c:v', 'libx264', '-tune', 'stillimage',
            '-c:a', 'aac', '-b:a', '192k',
            '-vf', "drawtext=text='ANALYSIS':fontsize=40:fontcolor=white:box=1:boxcolor=black@0.7:x=(w-text_w)/2:y=100",
            '-shortest', '-pix_fmt', 'yuv420p',
            '-y', seg3_path
        ]
        subprocess.run(cmd, check=True)
        segments.append(seg3_path)
        
        # Concatenate all segments
        print("🎬 Combining segments...")
        concat_file = video_path.replace('.mp4', '_concat.txt')
        with open(concat_file, 'w') as f:
            for seg in segments:
                # Use absolute paths for concat file
                abs_seg = os.path.abspath(seg)
                f.write(f"file '{abs_seg}'\n")
        
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', concat_file, '-c', 'copy',
            '-y', output_path
        ]
        subprocess.run(cmd, check=True)
        
        # Cleanup
        for seg in segments:
            os.remove(seg)
        os.remove(concat_file)
        os.remove(impact_frame_path)
        os.remove(audio_path)
        
        print(f"✅ Narrated analysis video created: {output_path}")
        print(f"   Total duration: ~{5 + 10 + audio_duration:.0f} seconds")
        print(f"   - Original swing: 5 sec")
        print(f"   - Slow motion: 10 sec")
        print(f"   - Commentary: {audio_duration:.1f} sec")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python create_narrated_analysis.py <original_video_path>")
        print("   Expects _pose.json and _analysis.json files to exist")
        sys.exit(1)
    
    video_path = sys.argv[1]
    pose_path = video_path.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    analysis_path = video_path.replace('.mp4', '_analysis.json').replace('.mov', '_analysis.json')
    output_path = video_path.replace('.mp4', '_narrated.mp4').replace('.mov', '_narrated.mp4')
    
    if not os.path.exists(analysis_path):
        print(f"❌ Analysis data not found: {analysis_path}")
        sys.exit(1)
    
    creator = NarratedAnalysisCreator()
    await creator.create_narrated_video(video_path, pose_path, analysis_path, output_path)

if __name__ == "__main__":
    asyncio.run(main())