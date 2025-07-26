#!/usr/bin/env python3
"""
Create the definitive narrated video with:
1. Full audio playback (no cutoff)
2. Text recommendations overlaid
3. MediaPipe skeleton throughout
"""

import os
import sys
import json
import asyncio
import subprocess
from dotenv import load_dotenv

load_dotenv()

class FinalCompleteVideo:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
    def create_commentary_script(self, analysis_data, pose_data):
        """Create concise commentary that fits well with video."""
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
        
        # Build concise commentary
        script = f"Golf swing analysis. Score: {score} out of 10. "
        
        if highlights:
            script += "Positives: "
            script += ". ".join(highlights) + ". "
        
        script += f"Your spine angle changes from {setup_angle:.0f} to {impact_angle:.0f} degrees. "
        
        if improvements:
            script += "Focus areas: "
            script += ". ".join(improvements) + ". "
        
        if comments:
            script += "Tips: "
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
            input=text,
            speed=1.0
        )
        
        response.stream_to_file(output_path)
        return True
    
    async def create_final_complete_video(self, original_video, full_analysis_video, analysis_path, pose_path, output_path):
        """Create video with text overlays and full audio."""
        
        print("📊 Loading analysis data...")
        with open(analysis_path, 'r') as f:
            analysis_data = json.load(f)
        
        with open(pose_path, 'r') as f:
            pose_data = json.load(f)
        
        # Extract key data for overlays
        score = analysis_data.get('swings', [{}])[0].get('score', 'N/A')
        improvements = analysis_data.get('summary', {}).get('improvements', [])
        tips = analysis_data.get('swings', [{}])[0].get('comments', [])
        
        # Generate commentary
        print("✍️  Creating commentary...")
        script = self.create_commentary_script(analysis_data, pose_data)
        print(f"Script: {len(script.split())} words")
        
        # Generate TTS
        print("🎙️  Generating narration...")
        audio_path = original_video.replace('.mp4', '_final_audio.mp3')
        await self.generate_tts_openai(script, audio_path)
        
        # Get audio duration
        audio_probe = ['ffprobe', '-v', 'error', '-show_entries', 
                      'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                      audio_path]
        audio_duration = float(subprocess.check_output(audio_probe).decode().strip())
        print(f"🎵 Audio duration: {audio_duration:.1f} seconds")
        
        # Get video duration
        video_probe = ['ffprobe', '-v', 'error', '-show_entries', 
                      'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                      full_analysis_video]
        video_duration = float(subprocess.check_output(video_probe).decode().strip())
        print(f"📹 Video duration: {video_duration:.1f} seconds")
        
        # If audio is longer than video, extend video
        if audio_duration > video_duration:
            print(f"📹 Extending video from {video_duration:.1f}s to {audio_duration:.1f}s...")
            
            # Extract last frame
            last_frame = original_video.replace('.mp4', '_last_frame_final.jpg')
            cmd = [
                'ffmpeg', '-sseof', '-0.1', '-i', full_analysis_video,
                '-frames:v', '1', '-y', last_frame
            ]
            subprocess.run(cmd, check=True)
            
            # Create extended video
            extended_video = original_video.replace('.mp4', '_extended.mp4')
            extension_time = audio_duration - video_duration + 1  # Add 1 second buffer
            
            # Create extension segment from last frame
            extension_seg = original_video.replace('.mp4', '_extension.mp4')
            cmd = [
                'ffmpeg', '-loop', '1', '-i', last_frame,
                '-c:v', 'libx264', '-t', str(extension_time),
                '-pix_fmt', 'yuv420p', '-vf', 'scale=720:1280',
                '-y', extension_seg
            ]
            subprocess.run(cmd, check=True)
            
            # Concatenate original + extension
            concat_file = original_video.replace('.mp4', '_extend_concat.txt')
            with open(concat_file, 'w') as f:
                f.write(f"file '{os.path.abspath(full_analysis_video)}'\n")
                f.write(f"file '{os.path.abspath(extension_seg)}'\n")
            
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', concat_file, '-c', 'copy',
                '-y', extended_video
            ]
            subprocess.run(cmd, check=True)
            
            # Use extended video as input
            input_video = extended_video
            
            # Cleanup
            os.remove(last_frame)
            os.remove(extension_seg)
            os.remove(concat_file)
        else:
            input_video = full_analysis_video
        
        # Add text overlays to the video
        print("📝 Adding text overlays...")
        
        # Prepare text for overlays (escape special characters)
        score_text = f"Score: {score}/10"
        improvements_text = "IMPROVEMENTS:"
        tips_text = "COACH TIPS:"
        
        # Build complex filter for text overlays with proper escaping
        filter_parts = []
        
        # Score (always visible) - escape colons
        score_escaped = score_text.replace(':', '\\:')
        filter_parts.append(f"drawtext=text='{score_escaped}':fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.7:x=w-tw-20:y=20")
        
        # Improvements box (visible after 3 seconds)
        y_pos = 100
        improvements_escaped = improvements_text.replace(':', '\\:')
        filter_parts.append(f"drawtext=text='{improvements_escaped}':fontsize=25:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y={y_pos}:enable='gt(t,3)'")
        
        for i, imp in enumerate(improvements[:2]):
            y_pos += 35
            # Remove problematic characters and escape colons
            clean_imp = imp.replace("'", "").replace('"', '').replace(':', '\\:')[:60]
            filter_parts.append(f"drawtext=text='{clean_imp}':fontsize=20:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y={y_pos}:enable='gt(t,3)'")
        
        # Tips box (visible after 6 seconds)
        y_pos = 250
        tips_escaped = tips_text.replace(':', '\\:')
        filter_parts.append(f"drawtext=text='{tips_escaped}':fontsize=25:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y={y_pos}:enable='gt(t,6)'")
        
        for i, tip in enumerate(tips[:2]):
            y_pos += 35
            # Remove problematic characters and escape colons
            clean_tip = tip.replace("'", "").replace('"', '').replace(':', '\\:')[:60]
            filter_parts.append(f"drawtext=text='{clean_tip}':fontsize=20:fontcolor=white:box=1:boxcolor=black@0.7:x=20:y={y_pos}:enable='gt(t,6)'")
        
        # Join all filters
        filter_complex = ','.join(filter_parts)
        
        # Create final video with overlays and audio
        print("🎬 Creating final video...")
        cmd = [
            'ffmpeg', '-i', input_video, '-i', audio_path,
            '-filter_complex', filter_complex,
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            '-y', output_path
        ]
        
        # Run with error checking
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            # Try simpler version without complex text
            print("🔄 Trying simpler version...")
            cmd = [
                'ffmpeg', '-i', input_video, '-i', audio_path,
                '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac',
                '-y', output_path
            ]
            subprocess.run(cmd, check=True)
        
        # Cleanup
        os.remove(audio_path)
        if input_video != full_analysis_video:
            os.remove(input_video)
        
        # Get final duration
        final_probe = ['ffprobe', '-v', 'error', '-show_entries', 
                      'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                      output_path]
        final_duration = float(subprocess.check_output(final_probe).decode().strip())
        
        print(f"✅ Final complete video created: {output_path}")
        print(f"   Duration: {final_duration:.1f} seconds")
        print(f"   - Full narration plays to completion")
        print(f"   - Text recommendations on screen")
        print(f"   - MediaPipe skeleton overlay")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python create_final_complete.py <original_video_path>")
        sys.exit(1)
    
    original_video = sys.argv[1]
    full_analysis = original_video.replace('.mp4', '_full_analysis.mp4').replace('.mov', '_full_analysis.mp4')
    analysis_path = original_video.replace('.mp4', '_analysis.json').replace('.mov', '_analysis.json')
    pose_path = original_video.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    output_path = original_video.replace('.mp4', '_final_complete.mp4').replace('.mov', '_final_complete.mp4')
    
    # Check files exist
    if not os.path.exists(full_analysis):
        print(f"❌ Full analysis video not found: {full_analysis}")
        print("   Run render_full_analysis.py first")
        sys.exit(1)
    
    creator = FinalCompleteVideo()
    await creator.create_final_complete_video(original_video, full_analysis, analysis_path, pose_path, output_path)

if __name__ == "__main__":
    asyncio.run(main())