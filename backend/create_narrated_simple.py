#!/usr/bin/env python3
"""
Create a simpler narrated video where commentary plays over the whole video.
"""

import os
import sys
import json
import asyncio
import subprocess
from dotenv import load_dotenv

load_dotenv()

class SimpleNarratedVideo:
    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
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
            script += "What you're doing well: "
            script += ". ".join(highlights) + ". "
        
        # Areas for improvement
        if improvements:
            script += "Areas to focus on: "
            for imp in improvements[:2]:
                script += imp + ". "
        
        # Specific tips
        if comments:
            script += "My coaching tips: "
            script += ". ".join(comments) + ". "
        
        script += "Keep practicing!"
        
        return script
    
    async def generate_tts_openai(self, text, output_path):
        """Generate speech using OpenAI TTS."""
        import openai
        
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        
        response.stream_to_file(output_path)
        return True
    
    async def create_simple_narrated(self, video_path, analysis_path, output_path):
        """Create video with narration overlay."""
        
        print("📊 Loading analysis data...")
        with open(analysis_path, 'r') as f:
            analysis_data = json.load(f)
        
        # Generate commentary
        print("✍️  Creating commentary...")
        script = self.create_commentary_script(analysis_data)
        print(f"Script: {len(script.split())} words")
        
        # Generate TTS
        print("🎙️  Generating narration...")
        audio_path = video_path.replace('.mp4', '_narration.mp3')
        await self.generate_tts_openai(script, audio_path)
        
        # Get video duration
        probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                     'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                     video_path]
        video_duration = float(subprocess.check_output(probe_cmd).decode().strip())
        
        # Get audio duration
        audio_probe = ['ffprobe', '-v', 'error', '-show_entries', 
                      'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                      audio_path]
        audio_duration = float(subprocess.check_output(audio_probe).decode().strip())
        
        print(f"Video: {video_duration:.1f}s, Audio: {audio_duration:.1f}s")
        
        # Create video with audio overlay
        # If audio is longer than video, loop the video
        # If video is longer than audio, audio plays once then stops
        print("🎬 Adding narration to video...")
        
        if audio_duration > video_duration:
            # Loop video to match audio length
            cmd = [
                'ffmpeg', '-stream_loop', '-1', '-i', video_path,
                '-i', audio_path,
                '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac',
                '-shortest',  # Stop when audio ends
                '-y', output_path
            ]
        else:
            # Simple overlay - audio plays over video
            cmd = [
                'ffmpeg', '-i', video_path,
                '-i', audio_path,
                '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac',
                '-y', output_path
            ]
        
        subprocess.run(cmd, check=True)
        
        # Cleanup
        os.remove(audio_path)
        
        print(f"✅ Narrated video created: {output_path}")
        print(f"   Commentary plays over the swing video")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python create_narrated_simple.py <video_path>")
        print("   Expects _analysis.json file to exist")
        sys.exit(1)
    
    video_path = sys.argv[1]
    analysis_path = video_path.replace('.mp4', '_analysis.json').replace('.mov', '_analysis.json')
    output_path = video_path.replace('.mp4', '_narrated_simple.mp4').replace('.mov', '_narrated_simple.mp4')
    
    if not os.path.exists(analysis_path):
        print(f"❌ Analysis data not found: {analysis_path}")
        sys.exit(1)
    
    creator = SimpleNarratedVideo()
    await creator.create_simple_narrated(video_path, analysis_path, output_path)

if __name__ == "__main__":
    asyncio.run(main())