#!/usr/bin/env python3
"""
Create narrated video using ElevenLabs v3 API with new voices.
"""

import os
import sys
import json
import asyncio
import subprocess
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings

load_dotenv()

class NarratedVideoV3:
    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment")
        
        self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
        
        # Available voices (you can choose from these)
        self.voices = {
            "george": "JBFqnCBsd6RMkjVDRZzb",  # British accent, narrative
            "rachel": "21m00Tcm4TlvDq8ikWAM",  # American, clear
            "antoni": "ErXwobaYiN019PkySvjV",  # American, warm
            "brian": "nPczCjzI2devNBz1zQrb",   # American, deep
            "jessica": "cgSgspJ2msm6clMCkdW9", # American, expressive
            "alice": "Xb7hH8MSUJpSbSDYk0k2",   # British, news
        }
        
    def create_commentary_script(self, analysis_data, pose_data):
        """Create concise commentary that fits video length."""
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
        
        # Build commentary
        script = f"Golf swing analysis. Score: {score} out of 10. "
        
        if highlights:
            script += "Strengths: "
            script += ". ".join(highlights[:2]) + ". "
        
        script += f"Your spine angle moves from {setup_angle:.0f} to {impact_angle:.0f} degrees. "
        
        if improvements:
            script += "Focus on: "
            script += ". ".join(improvements[:2]) + ". "
        
        script += "Keep practicing!"
        
        return script
    
    async def generate_tts_elevenlabs(self, text, output_path, voice_id="george"):
        """Generate speech using ElevenLabs v3 SDK."""
        print(f"🎙️  Generating narration with voice: {voice_id}")
        
        # Get the voice ID
        if voice_id in self.voices:
            voice_id = self.voices[voice_id]
        
        # Generate audio
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_turbo_v2_5",  # Latest turbo model
            output_format="mp3_44100_128",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )
        
        # Save to file
        with open(output_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
        
        return True
    
    async def create_narrated_video(self, original_video, pose_overlay_video, analysis_path, pose_path, output_path, voice="george"):
        """Create video with ElevenLabs narration."""
        
        print("📊 Loading analysis data...")
        with open(analysis_path, 'r') as f:
            analysis_data = json.load(f)
        
        with open(pose_path, 'r') as f:
            pose_data = json.load(f)
        
        # Generate commentary
        print("✍️  Creating commentary script...")
        script = self.create_commentary_script(analysis_data, pose_data)
        print(f"Script: {len(script.split())} words")
        print(f"Script: {script}")
        
        # Generate TTS
        print(f"🎙️  Generating narration with {voice} voice...")
        audio_path = original_video.replace('.mp4', '_elevenlabs_v3.mp3')
        await self.generate_tts_elevenlabs(script, audio_path, voice)
        
        # Get audio duration
        audio_probe = ['ffprobe', '-v', 'error', '-show_entries', 
                      'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                      audio_path]
        audio_duration = float(subprocess.check_output(audio_probe).decode().strip())
        print(f"🎵 Audio duration: {audio_duration:.1f} seconds")
        
        # Get video duration
        video_probe = ['ffprobe', '-v', 'error', '-show_entries', 
                      'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                      pose_overlay_video]
        video_duration = float(subprocess.check_output(video_probe).decode().strip())
        print(f"📹 Video duration: {video_duration:.1f} seconds")
        
        # Always extend video to be longer than audio to prevent cutoff
        target_duration = audio_duration + 1.0  # Add 1 second buffer
        if target_duration > video_duration:
            print(f"📹 Extending video from {video_duration:.1f}s to {target_duration:.1f}s...")
            
            # Extract last frame
            last_frame = original_video.replace('.mp4', '_last_frame_v3.jpg')
            cmd = [
                'ffmpeg', '-sseof', '-0.1', '-i', pose_overlay_video,
                '-frames:v', '1', '-y', last_frame
            ]
            subprocess.run(cmd, check=True)
            
            # Create extended video
            extended_video = original_video.replace('.mp4', '_extended_v3.mp4')
            extension_time = target_duration - video_duration
            
            # Create extension segment
            extension_seg = original_video.replace('.mp4', '_extension_v3.mp4')
            cmd = [
                'ffmpeg', '-loop', '1', '-i', last_frame,
                '-c:v', 'libx264', '-t', str(extension_time),
                '-pix_fmt', 'yuv420p', '-vf', 'scale=720:1280',
                '-y', extension_seg
            ]
            subprocess.run(cmd, check=True)
            
            # Concatenate
            concat_file = original_video.replace('.mp4', '_concat_v3.txt')
            with open(concat_file, 'w') as f:
                f.write(f"file '{os.path.abspath(pose_overlay_video)}'\n")
                f.write(f"file '{os.path.abspath(extension_seg)}'\n")
            
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', concat_file, '-c', 'copy',
                '-y', extended_video
            ]
            subprocess.run(cmd, check=True)
            
            input_video = extended_video
            
            # Cleanup
            os.remove(last_frame)
            os.remove(extension_seg)
            os.remove(concat_file)
        else:
            input_video = pose_overlay_video
        
        # Add audio to video without -shortest to ensure full audio plays
        print("🎬 Creating final video...")
        cmd = [
            'ffmpeg', '-i', input_video, '-i', audio_path,
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'copy', '-c:a', 'aac',
            '-y', output_path
        ]
        subprocess.run(cmd, check=True)
        
        # Cleanup
        os.remove(audio_path)
        if input_video != pose_overlay_video:
            os.remove(input_video)
        
        # Get final video duration
        final_probe = ['ffprobe', '-v', 'error', '-show_entries', 
                      'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                      output_path]
        final_duration = float(subprocess.check_output(final_probe).decode().strip())
        
        print(f"✅ Narrated video created: {output_path}")
        print(f"   Voice: {voice}")
        print(f"   Video duration: {final_duration:.1f} seconds")
        print(f"   Audio duration: {audio_duration:.1f} seconds")
        print(f"   Full narration guaranteed to play")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python create_narrated_v3.py <video_path> [voice]")
        print("Available voices: george, rachel, antoni, brian, jessica, alice")
        sys.exit(1)
    
    original_video = sys.argv[1]
    voice = sys.argv[2] if len(sys.argv) > 2 else "george"
    
    pose_overlay = original_video.replace('.mp4', '_pose_overlay.mp4').replace('.mov', '_pose_overlay.mp4')
    analysis_path = original_video.replace('.mp4', '_analysis.json').replace('.mov', '_analysis.json')
    pose_path = original_video.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    output_path = original_video.replace('.mp4', f'_narrated_v3_{voice}.mp4').replace('.mov', f'_narrated_v3_{voice}.mp4')
    
    # Check files exist
    for path, name in [(pose_overlay, "Pose overlay video"), 
                       (analysis_path, "Analysis data"),
                       (pose_path, "Pose data")]:
        if not os.path.exists(path):
            print(f"❌ {name} not found: {path}")
            sys.exit(1)
    
    creator = NarratedVideoV3()
    await creator.create_narrated_video(original_video, pose_overlay, analysis_path, pose_path, output_path, voice)

if __name__ == "__main__":
    asyncio.run(main())