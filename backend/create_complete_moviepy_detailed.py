#!/usr/bin/env python3
"""
Create complete narrated video using MoviePy with detailed fault overlays.
Combines: MediaPipe skeleton, fault identification overlays, and ElevenLabs narration.
"""

import os
import sys
import json
import asyncio
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings

load_dotenv()

class MoviePyDetailedVideo:
    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment")
        
        self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
        
        # Available voices
        self.voices = {
            "george": "JBFqnCBsd6RMkjVDRZzb",  # British accent
            "rachel": "21m00Tcm4TlvDq8ikWAM",  # American, clear
            "antoni": "ErXwobaYiN019PkySvjV",  # American, warm
        }
        
    def create_commentary_script(self, analysis_data, pose_data):
        """Create commentary including fault descriptions."""
        swings = analysis_data.get('swings', [])
        summary = analysis_data.get('summary', {})
        angle_analysis = pose_data.get('angle_analysis', {})
        
        if not swings:
            return "No swing data available."
        
        swing = swings[0]
        score = swing.get('score', 'N/A')
        faults = swing.get('identified_faults', [])
        highlights = summary.get('highlights', [])
        improvements = summary.get('improvements', [])
        
        # Get spine angles
        spine_angles = angle_analysis.get('spine_angle', {})
        setup_angle = spine_angles.get('setup', {}).get('angle', 'N/A')
        impact_angle = spine_angles.get('impact', {}).get('angle', 'N/A')
        
        # Build commentary
        script = f"Golf swing analysis. Score: {score} out of 10. "
        
        if highlights:
            script += "Good points: "
            script += ", ".join(highlights) + ". "
        
        script += f"Your spine angle moves from {setup_angle:.0f} to {impact_angle:.0f} degrees. "
        
        # Mention key faults
        if faults:
            script += f"I've identified {len(faults)} areas to work on. "
            for fault in faults[:2]:  # First 2 faults
                script += f"{fault['fault_name']}: {fault['description'][:100]}. "
        
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
            model_id="eleven_turbo_v2_5",
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
    
    def create_text_overlays(self, video_clip, analysis_data, pose_data):
        """Add text overlays including fault indicators."""
        
        # Extract key data
        swing = analysis_data.get('swings', [{}])[0]
        score = swing.get('score', 'N/A')
        faults = swing.get('identified_faults', [])
        improvements = analysis_data.get('summary', {}).get('improvements', [])
        tips = swing.get('comments', [])
        
        # Get angles
        angle_analysis = pose_data.get('angle_analysis', {})
        spine_angles = angle_analysis.get('spine_angle', {})
        setup_angle = spine_angles.get('setup', {}).get('angle', 'N/A')
        impact_angle = spine_angles.get('impact', {}).get('angle', 'N/A')
        
        clips = [video_clip]
        
        # Score (always visible)
        score_text = TextClip(
            text=f"Score: {score}/10",
            font=None,  # Use system default
            font_size=30,
            color='yellow',
            stroke_color='black',
            stroke_width=2
        )
        score_text = score_text.with_position(('right', 'top')).with_duration(video_clip.duration)
        clips.append(score_text)
        
        # Spine angle info (visible after 2 seconds)
        angle_text = TextClip(
            text=f"Spine: {setup_angle:.0f}° → {impact_angle:.0f}°",
            font=None,  # Use system default
            font_size=24,
            color='white',
            bg_color='black'
        )
        angle_text = angle_text.with_position((20, 20)).with_duration(video_clip.duration - 2).with_start(2)
        clips.append(angle_text)
        
        # Fault indicators - show each fault during its timestamp range
        # But extend display time to be at least 2 seconds for visibility
        for i, fault in enumerate(faults):
            start_time = float(fault['timestamp_range'][0])
            end_time = float(fault['timestamp_range'][1])
            duration = end_time - start_time
            
            # Ensure minimum display time of 2 seconds
            display_duration = max(duration, 2.0)
            
            # Fault name
            fault_name_text = TextClip(
                text=f"⚠️ {fault['fault_name']}",
                font=None,
                font_size=25,
                color='red',
                bg_color='black'
            )
            fault_name_text = fault_name_text.with_position((20, 80 + i*40)).with_duration(display_duration).with_start(start_time)
            clips.append(fault_name_text)
        
        # Improvements box (visible after 4 seconds)
        y_pos = 220
        if improvements:
            imp_title = TextClip(
                text="IMPROVEMENTS:",
                font=None,  # Use system default
                font_size=25,
                color='white',
                bg_color='black'
            )
            imp_title = imp_title.with_position((20, y_pos)).with_duration(video_clip.duration - 4).with_start(4)
            clips.append(imp_title)
            
            for i, imp in enumerate(improvements[:3]):
                y_pos += 35
                imp_text = TextClip(
                    text=f"• {imp[:50]}",
                    font=None,  # Use system default
                    font_size=20,
                    color='white',
                    bg_color='black'
                )
                imp_text = imp_text.with_position((20, y_pos)).with_duration(video_clip.duration - 4).with_start(4)
                clips.append(imp_text)
        
        # Coach tips (visible after 8 seconds)
        y_pos = 380
        if tips and video_clip.duration > 8:
            tips_title = TextClip(
                text="QUICK TIPS:",
                font=None,  # Use system default
                font_size=25,
                color='white',
                bg_color='black'
            )
            tips_title = tips_title.with_position((20, y_pos)).with_duration(video_clip.duration - 8).with_start(8)
            clips.append(tips_title)
            
            for i, tip in enumerate(tips[:2]):
                y_pos += 35
                tip_text = TextClip(
                    text=f"• {tip[:50]}",
                    font=None,  # Use system default
                    font_size=20,
                    color='white',
                    bg_color='black'
                )
                tip_text = tip_text.with_position((20, y_pos)).with_duration(video_clip.duration - 8).with_start(8)
                clips.append(tip_text)
        
        # Progress bar at bottom
        progress_bar = TextClip(
            text=f"Detected {len(faults)} faults | MediaPipe Pose Analysis",
            font=None,  # Use system default
            font_size=16,
            color='cyan',
            bg_color='black'
        )
        progress_bar = progress_bar.with_position(('center', 'bottom')).with_duration(video_clip.duration)
        clips.append(progress_bar)
        
        # Composite all clips
        final_video = CompositeVideoClip(clips)
        return final_video
    
    async def create_complete_video(self, original_video, pose_overlay_video, analysis_path, pose_path, output_path, voice="george"):
        """Create complete video with MoviePy."""
        
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
        print(f"🎙️  Generating narration with {voice} voice...")
        audio_path = original_video.replace('.mp4', '_moviepy_detailed_audio.mp3')
        await self.generate_tts_elevenlabs(script, audio_path, voice)
        
        # Load video and audio
        print("🎬 Loading video with MediaPipe overlay...")
        video = VideoFileClip(pose_overlay_video)
        audio = AudioFileClip(audio_path)
        
        # Extend video if audio is longer
        if audio.duration > video.duration:
            print(f"📹 Extending video from {video.duration:.1f}s to {audio.duration:.1f}s...")
            # Get last frame and extend
            last_frame = video.get_frame(video.duration - 0.1)
            extension = ImageClip(last_frame).with_duration(audio.duration - video.duration + 0.5)
            video = concatenate_videoclips([video, extension])
        
        # Add text overlays
        print("📝 Adding text overlays with fault indicators...")
        video_with_text = self.create_text_overlays(video, analysis_data, pose_data)
        
        # Add audio
        print("🎵 Adding narration...")
        final_video = video_with_text.with_audio(audio)
        
        # Write final video
        print("💾 Rendering final video...")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=30,
            preset='medium',
            logger=None  # Suppress verbose output
        )
        
        # Cleanup
        video.close()
        audio.close()
        final_video.close()
        os.remove(audio_path)
        
        print(f"✅ Complete video created: {output_path}")
        print(f"   - MediaPipe skeleton overlay")
        print(f"   - Fault indicators during specific timestamps")
        print(f"   - Text overlays with improvements and tips")
        print(f"   - {voice} voice narration")
        print(f"   - Duration: {final_video.duration:.1f} seconds")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python create_complete_moviepy_detailed.py <video_path> [voice]")
        print("Available voices: george, rachel, antoni")
        sys.exit(1)
    
    original_video = sys.argv[1]
    voice = sys.argv[2] if len(sys.argv) > 2 else "george"
    
    pose_overlay = original_video.replace('.mp4', '_pose_overlay.mp4').replace('.mov', '_pose_overlay.mp4')
    analysis_path = original_video.replace('.mp4', '_detailed_analysis.json').replace('.mov', '_detailed_analysis.json')
    pose_path = original_video.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    output_path = original_video.replace('.mp4', f'_complete_detailed_{voice}.mp4').replace('.mov', f'_complete_detailed_{voice}.mp4')
    
    # Check files exist
    for path, name in [(pose_overlay, "Pose overlay video"), 
                       (analysis_path, "Detailed analysis data"),
                       (pose_path, "Pose data")]:
        if not os.path.exists(path):
            print(f"❌ {name} not found: {path}")
            print(f"   Run analyze_video_detailed.py first to generate detailed analysis")
            sys.exit(1)
    
    creator = MoviePyDetailedVideo()
    await creator.create_complete_video(original_video, pose_overlay, analysis_path, pose_path, output_path, voice)

if __name__ == "__main__":
    asyncio.run(main())