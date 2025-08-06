#!/usr/bin/env python3
"""
Script to analyze a video file and print the raw LLM response.
Usage: python analyze_video.py <video_path> [model_name]
Default model: gemini-2.5-flash
Available models: gemini-2.5-flash, gemini-2.5-pro, gemini-1.5-pro, gemini-1.5-flash
"""

import os
import sys
import json
import asyncio
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("❌ Google Gemini AI not available. Install google-genai package.")
    sys.exit(1)

import aiofiles
import cv2


class VideoAnalyzer:
    """Standalone video analyzer that prints raw LLM response."""
    
    def __init__(self, model_name="gemini-2.5-flash"):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        
        if not self.gemini_api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            sys.exit(1)
        
        # Configure Gemini AI with new v2 API
        self.client = genai.Client(api_key=self.gemini_api_key)
        
        # Safety settings - using new API format
        self.safety_settings = [
            types.SafetySetting(
                category='HARM_CATEGORY_HATE_SPEECH',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_DANGEROUS_CONTENT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_HARASSMENT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
        ]
        
        # Generation config
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            safety_settings=self.safety_settings
        )
        
        print(f"✅ Gemini AI initialized successfully with model: {self.model_name}")
    
    async def load_prompt(self) -> str:
        """Load the coaching prompt template."""
        try:
            prompt_path = os.path.join(
                os.path.dirname(__file__), 
                "prompts", 
                "video_analysis_swing_coaching.txt"
            )
            
            async with aiofiles.open(prompt_path, 'r') as f:
                return await f.read()
                
        except Exception as e:
            print(f"❌ Failed to load coaching prompt: {e}")
            sys.exit(1)
    
    async def analyze_video(self, video_path: str) -> None:
        """Analyze video and print raw LLM response."""
        
        # Convert relative path to absolute path from current working directory
        if not os.path.isabs(video_path):
            video_path = os.path.abspath(video_path)
        
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            print(f"    Current working directory: {os.getcwd()}")
            sys.exit(1)
        
        print(f"📹 Analyzing video: {video_path}")
        print(f"📂 Working directory: {os.getcwd()}")
        
        try:
            # Get video properties
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            print(f"📊 Video properties:")
            print(f"    Duration: {duration:.2f} seconds")
            print(f"    FPS: {fps:.1f}")
            print(f"    Frame count: {frame_count}")
            
            # Load prompt
            print("📝 Loading coaching prompt...")
            coaching_prompt = await self.load_prompt()
            
            # Format prompt
            try:
                escaped_prompt = coaching_prompt.replace('{', '{{').replace('}', '}}')
                escaped_prompt = escaped_prompt.replace('{{duration}}', '{duration}')
                escaped_prompt = escaped_prompt.replace('{{frame_rate}}', '{frame_rate}')
                
                enhanced_prompt = escaped_prompt.format(
                    duration=f"{duration:.2f}",
                    frame_rate=f"{fps:.1f}"
                )
                print(f"✅ Prompt formatted successfully ({len(enhanced_prompt)} chars)")
            except KeyError as ke:
                print(f"❌ KeyError during prompt formatting: {ke}")
                sys.exit(1)
            
            # Upload video to Gemini using new v2 API
            print(f"📤 Uploading video to Gemini ({os.path.getsize(video_path) / 1024 / 1024:.1f}MB)...")
            upload_start = time.time()
            
            video_file = await self.client.aio.files.upload(file=video_path)
            
            # Wait for processing
            processing_count = 0
            while video_file.state.name == "PROCESSING":
                processing_count += 1
                print(f"⏳ Waiting for Gemini video processing... ({processing_count * 2}s elapsed)")
                await asyncio.sleep(2)
                video_file = await self.client.aio.files.get(name=video_file.name)
            
            upload_elapsed = time.time() - upload_start
            print(f"✅ Video uploaded and processed in {upload_elapsed:.1f}s")
            
            if video_file.state.name == "FAILED":
                print("❌ Gemini video processing FAILED")
                sys.exit(1)
            
            # Show what we're sending to Gemini
            print("\n" + "="*80)
            print(f"🚀 CALLING GEMINI API - {self.model_name}")
            print("="*80)
            print(f"📤 FULL PROMPT BEING SENT ({len(enhanced_prompt)} chars):")
            print("-"*40)
            print(enhanced_prompt)  # Print the entire prompt, no abbreviation
            print("-"*40)
            print(f"📹 Video file ID: {video_file.name}")
            print(f"📹 Video state: {video_file.state.name}")
            print(f"⚙️ Safety settings: {len(self.safety_settings)} categories")
            print(f"⚙️ Response format: JSON only")
            print("="*80)
            
            # Generate analysis
            print("🚀 Calling Gemini API...")
            api_start_time = time.time()
            
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=[video_file, enhanced_prompt],
                    config=self.generation_config
                )
                print("✅ Gemini API call completed successfully")
            except Exception as api_error:
                print(f"❌ Gemini API call failed: {type(api_error).__name__}: {api_error}")
                sys.exit(1)
            
            api_elapsed = time.time() - api_start_time
            print(f"📥 Gemini response received in {api_elapsed:.1f}s")
            
            # Print raw response
            print("\n" + "="*80)
            print("📄 RAW LLM RESPONSE")
            print("="*80)
            
            try:
                response_text = response.text
                print(f"Response length: {len(response_text)} characters")
                print(f"Response type: {type(response_text)}")
                print("-"*80)
                print(response_text)
                print("-"*80)
                
                # Try to parse as JSON for validation
                try:
                    parsed = json.loads(response_text.strip())
                    print("✅ Response is valid JSON")
                    print(f"🔍 JSON structure: {list(parsed.keys())}")
                except json.JSONDecodeError as e:
                    print(f"⚠️ Response is not valid JSON: {e}")
                    
            except Exception as e:
                print(f"❌ Error accessing response text: {e}")
                print(f"Response object: {response}")
                sys.exit(1)
            
            # Clean up
            try:
                await self.client.aio.files.delete(name=video_file.name)
                print("🧹 Cleaned up uploaded file")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to cleanup file: {cleanup_error}")
            
            print("="*80)
            print("✅ Analysis completed successfully")
            
        except Exception as e:
            print(f"💥 Analysis failed: {e}")
            sys.exit(1)


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze video with Gemini AI")
    parser.add_argument("video_path", help="Path to video file")
    parser.add_argument("--model", default="gemini-2.5-flash", 
                       choices=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-pro", "gemini-1.5-flash"],
                       help="Gemini model to use (default: gemini-2.5-flash)")
    parser.add_argument("--show-full-prompt", action="store_true", 
                       help="Show the full prompt being sent")
    
    args = parser.parse_args()
    
    analyzer = VideoAnalyzer(model_name=args.model)
    
    if args.show_full_prompt:
        # Load and show the full prompt
        prompt = await analyzer.load_prompt()
        print("\n" + "="*80)
        print("📝 FULL PROMPT TEMPLATE")
        print("="*80)
        print(prompt)
        print("="*80)
        print()
    
    await analyzer.analyze_video(args.video_path)


if __name__ == "__main__":
    asyncio.run(main())