#!/usr/bin/env python3
"""
Analyze video with detailed fault identification using Gemini AI.
"""

import os
import sys
import json
import asyncio
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
    from google.genai.types import GenerateContentConfig, SafetySetting, HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("❌ Google Gemini AI not available. Install google-genai package.")
    sys.exit(1)

import aiofiles
import cv2


class DetailedVideoAnalyzer:
    """Video analyzer with detailed fault identification."""
    
    def __init__(self, model_name="gemini-2.0-flash-exp"):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        
        if not self.gemini_api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            sys.exit(1)
        
        # Configure Gemini AI with new v2 API
        self.client = genai.Client(api_key=self.gemini_api_key)
        
        print(f"✅ Gemini AI initialized successfully with model: {self.model_name}")
    
    async def load_prompt(self) -> str:
        """Load the detailed fault analysis prompt template."""
        try:
            prompt_path = os.path.join(
                os.path.dirname(__file__), 
                "prompts", 
                "video_analysis_detailed_faults.txt"
            )
            
            async with aiofiles.open(prompt_path, 'r') as f:
                return await f.read()
                
        except Exception as e:
            print(f"❌ Failed to load detailed prompt: {e}")
            sys.exit(1)
    
    async def analyze_video(self, video_path: str, show_full_prompt: bool = False) -> None:
        """Analyze video with detailed fault identification."""
        
        # Convert relative path to absolute path
        if not os.path.isabs(video_path):
            video_path = os.path.abspath(video_path)
        
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            sys.exit(1)
        
        print(f"📹 Analyzing video: {video_path}")
        
        try:
            # Get video properties
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            print(f"📊 Video properties:")
            print(f"    Duration: {duration:.2f} seconds")
            print(f"    FPS: {fps}")
            print(f"    Frame count: {frame_count}")
            
            # Load and format prompt
            print("📝 Loading detailed fault analysis prompt...")
            prompt_template = await self.load_prompt()
            
            # Format prompt with video metadata
            enhanced_prompt = prompt_template.format(
                duration=f"{duration:.2f}",
                frame_rate=f"{fps:.1f}"
            )
            
            if show_full_prompt:
                print("\n" + "="*50)
                print("FULL PROMPT BEING SENT TO GEMINI:")
                print("="*50)
                print(enhanced_prompt)
                print("="*50 + "\n")
            
            print(f"✅ Prompt formatted successfully")
            
            # Upload video to Gemini
            print(f"📤 Uploading video to Gemini...")
            upload_start = time.time()
            
            video_file = await self.client.aio.files.upload(file=video_path)
            
            # Wait for processing
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(2)
                video_file = await self.client.aio.files.get(name=video_file.name)
            
            upload_elapsed = time.time() - upload_start
            print(f"✅ Video uploaded in {upload_elapsed:.1f}s")
            
            if video_file.state.name == "FAILED":
                print("❌ Gemini video processing FAILED")
                sys.exit(1)
            
            # Create config with safety settings included
            config = GenerateContentConfig(
                response_mime_type="application/json",
                safety_settings=[
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                    ),
                ]
            )
            
            # Generate analysis
            print("🚀 Calling Gemini API for detailed fault analysis...")
            api_start = time.time()
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[video_file, enhanced_prompt],
                config=config
            )
            
            api_elapsed = time.time() - api_start
            print(f"✅ Gemini response received in {api_elapsed:.1f}s")
            
            # Parse response
            response_text = response.text
            print(f"📥 Response length: {len(response_text)} characters")
            
            # Parse JSON
            parsed = json.loads(response_text.strip())
            print(f"✅ Successfully parsed JSON response")
            
            # Show summary
            print("\n📊 Analysis Summary:")
            print(f"   Overall quality: {parsed.get('overall_quality', 'N/A')}")
            
            if 'swings' in parsed and parsed['swings']:
                swing = parsed['swings'][0]
                print(f"   Score: {swing.get('score', 'N/A')}/10")
                faults = swing.get('identified_faults', [])
                print(f"   Identified faults: {len(faults)}")
                
                if faults:
                    print("\n🔍 Detected Faults:")
                    for fault in faults:
                        print(f"   • {fault['fault_name']} ({fault['timestamp_range'][0]}-{fault['timestamp_range'][1]})")
            
            # Save analysis
            output_path = video_path.replace('.mp4', '_detailed_analysis.json').replace('.mov', '_detailed_analysis.json')
            with open(output_path, 'w') as f:
                json.dump(parsed, f, indent=2)
            
            print(f"\n💾 Detailed analysis saved to: {output_path}")
            
            # Clean up
            await self.client.aio.files.delete(name=video_file.name)
            print("✅ Cleaned up uploaded file")
            
        except Exception as e:
            print(f"\n💥 Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


async def main():
    parser = argparse.ArgumentParser(description='Analyze video with detailed fault identification')
    parser.add_argument('video_path', help='Path to video file')
    parser.add_argument('--model', default='gemini-2.0-flash-exp',
                        choices=['gemini-2.0-flash-exp', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro'],
                        help='Gemini model to use')
    parser.add_argument('--show-full-prompt', action='store_true',
                        help='Display the full prompt being sent to Gemini')
    
    args = parser.parse_args()
    
    analyzer = DetailedVideoAnalyzer(model_name=args.model)
    await analyzer.analyze_video(args.video_path, args.show_full_prompt)


if __name__ == "__main__":
    asyncio.run(main())