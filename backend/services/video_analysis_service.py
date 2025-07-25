"""
Video analysis service using Google Gemini AI for golf swing analysis.
"""

import os
import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiofiles
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from google import genai
    from google.genai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Gemini AI not available. Install google-genai package.")

from database.config import AsyncSessionLocal
from models.video_analysis import VideoAnalysis, AnalysisStatus
from models.video import Video
from services.storage_service import get_storage_service
from services.pose_analysis_service import get_pose_analysis_service

logger = logging.getLogger(__name__)


class VideoAnalysisService:
    """Service for analyzing golf swing videos using Google Gemini AI."""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        try:
            self.storage_service = get_storage_service()
        except Exception as e:
            logger.warning(f"Storage service not available: {e}")
            self.storage_service = None
        
        try:
            self.pose_analysis_service = get_pose_analysis_service()
        except Exception as e:
            logger.warning(f"Pose analysis service not available: {e}")
            self.pose_analysis_service = None
            
        self.temp_dir = tempfile.mkdtemp()
        
        # Configure Gemini AI with new v2 API
        if GEMINI_AVAILABLE and self.gemini_api_key:
            self.client = genai.Client(api_key=self.gemini_api_key)
            
            # Safety settings for video analysis (as list of dicts)
            self.safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                }
            ]
            
            # Model configuration for new API
            self.model_name = "gemini-2.5-flash"
            self.generation_config = {
                "response_mime_type": "application/json"
            }
            
            logger.info("Google Gemini AI v2 initialized successfully")
        else:
            logger.warning("Google Gemini AI not configured. Check GEMINI_API_KEY environment variable.")
    
    def analyze_video_sync(self, video_id: int, user_id: int) -> None:
        """Synchronous wrapper for analyze_video to be used in background tasks."""
        # Use the sync version to avoid event loop conflicts
        from services.video_analysis_service_sync import analyze_video_sync
        analyze_video_sync(self, video_id, user_id)
    
    async def analyze_video(self, video_id: int, user_id: int) -> Dict[str, Any]:
        """
        Analyze a golf swing video using Google Gemini AI.
        
        Args:
            video_id: The ID of the video to analyze
            user_id: The ID of the user who owns the video
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Get video and analysis records
            analysis_id = None
            video_url = None
            video_blob_name = None
            
            async with AsyncSessionLocal() as session:
                video = await session.get(Video, video_id)
                if not video or video.user_id != user_id:
                    raise ValueError("Video not found or access denied")
                
                # Store video info before session closes
                video_url = video.video_url
                video_blob_name = video.video_blob_name
                
                # Create or get analysis record
                analysis = await self._get_or_create_analysis(session, video_id, user_id)
                analysis.start_processing()
                await session.commit()
                analysis_id = analysis.id
            
            logger.info(f"Starting video analysis for video_id={video_id}, user_id={user_id}")
            
            # Download video file
            video_path = await self._download_video(video_blob_name or video_url)
            
            # Perform pose analysis
            pose_analysis_result = {}
            if self.pose_analysis_service:
                logger.info("Starting pose analysis...")
                pose_analysis_result = await self.pose_analysis_service.analyze_video_pose(video_path)
                logger.info("Pose analysis completed")
            
            # Load coaching prompts
            coaching_prompt = await self._load_coaching_prompt()
            
            # Analyze video with Gemini (include pose data in prompt)
            analysis_result = await self._analyze_with_gemini(video_path, coaching_prompt, pose_analysis_result)
            
            # Update analysis record with results
            async with AsyncSessionLocal() as session:
                analysis = await session.get(VideoAnalysis, analysis_id)
                
                # Store pose analysis data separately
                if pose_analysis_result.get('success'):
                    analysis.pose_data = pose_analysis_result
                    analysis.body_position_data = pose_analysis_result.get('angle_analysis', {})
                    analysis.swing_metrics = pose_analysis_result.get('biomechanical_efficiency', {})
                
                # Combine AI analysis with pose analysis for comprehensive results
                combined_analysis = analysis_result.copy()
                if pose_analysis_result.get('success'):
                    combined_analysis['pose_analysis'] = pose_analysis_result
                
                analysis.ai_analysis = combined_analysis
                analysis.video_duration = combined_analysis.get("duration", 0)
                analysis.analysis_confidence = combined_analysis.get("confidence", 0.8)
                analysis.mark_as_completed()
                await session.commit()
            
            # Clean up temporary file
            os.unlink(video_path)
            
            logger.info(f"Video analysis completed for video_id={video_id}")
            return {
                "success": True,
                "analysis_id": analysis.id,
                "results": analysis_result
            }
            
        except Exception as e:
            logger.error(f"Video analysis failed for video_id={video_id}: {e}")
            
            # Update analysis record with error
            if analysis_id:
                try:
                    async with AsyncSessionLocal() as session:
                        analysis = await session.get(VideoAnalysis, analysis_id)
                        if analysis:
                            analysis.mark_as_failed(str(e))
                            await session.commit()
                except Exception as db_error:
                    logger.error(f"Failed to update analysis record: {db_error}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_or_create_analysis(self, session, video_id: int, user_id: int) -> VideoAnalysis:
        """Get existing analysis or create new one."""
        from sqlalchemy import select
        
        # Check for existing analysis
        result = await session.execute(
            select(VideoAnalysis).filter(
                VideoAnalysis.video_id == video_id,
                VideoAnalysis.user_id == user_id
            )
        )
        existing_analysis = result.scalar_one_or_none()
        
        if existing_analysis:
            return existing_analysis
        
        # Create new analysis
        analysis = VideoAnalysis(
            user_id=user_id,
            video_id=video_id,
            status=AnalysisStatus.PENDING
        )
        session.add(analysis)
        await session.flush()
        return analysis
    
    async def _download_video(self, blob_name_or_url: str) -> str:
        """Download video file from storage to temporary location."""
        try:
            # Check if it's a full URL and extract blob name
            if blob_name_or_url.startswith('http'):
                # Extract blob name from GCS URL
                if "storage.googleapis.com/" in blob_name_or_url:
                    parts = blob_name_or_url.replace("https://storage.googleapis.com/", "").split("/", 1)
                    if len(parts) == 2:
                        blob_name = parts[1]
                        # Generate signed URL for the blob
                        signed_url = await self.storage_service.generate_signed_url(blob_name)
                    else:
                        signed_url = blob_name_or_url
                else:
                    signed_url = blob_name_or_url
            else:
                # Generate signed URL for download
                signed_url = await self.storage_service.generate_signed_url(blob_name_or_url)
            
            # Download file to temp location
            temp_path = os.path.join(self.temp_dir, f"video_{datetime.now().timestamp()}.mp4")
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(signed_url)
                response.raise_for_status()
                
                async with aiofiles.open(temp_path, 'wb') as f:
                    await f.write(response.content)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to download video {blob_name_or_url}: {e}")
            raise
    
    async def _load_coaching_prompt(self) -> str:
        """Load the coaching prompt template."""
        try:
            prompt_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "prompts", 
                "video_analysis_swing_coaching.txt"
            )
            
            async with aiofiles.open(prompt_path, 'r') as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Failed to load coaching prompt: {e}")
            # Return a basic prompt as fallback
            return """
            You are an expert golf instructor analyzing a video of a golf swing. 
            Please provide detailed coaching feedback in JSON format with the following structure:
            {
                "overall_score": <1-10>,
                "swing_phases": {...},
                "coaching_points": [...],
                "pose_analysis": {...},
                "summary": "<overall assessment>"
            }
            """
    
    async def _load_gemini_prompt(self) -> str:
        """Load the Gemini video analysis prompt template."""
        try:
            prompt_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "prompts", 
                "gemini_video_analysis.txt"
            )
            
            async with aiofiles.open(prompt_path, 'r') as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Failed to load Gemini prompt: {e}")
            # Return a basic prompt as fallback
            return """
GOLF SWING VIDEO ANALYSIS REQUEST

Please analyze this golf swing video for detailed coaching feedback.

VIDEO PROPERTIES:
- Duration: {duration} seconds  
- Original FPS: {fps}

{coaching_prompt}

IMPORTANT: 
1. Return ONLY valid JSON response - no markdown, no code blocks, no additional text. The response must be parseable with json.loads().
2. Focus on the major swing phases and body position changes throughout the video.
            """
    
    async def _analyze_with_gemini(self, video_path: str, coaching_prompt: str, pose_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze video using Google Gemini AI."""
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google Gemini AI library not available. Install google-generativeai package.")
        
        if not self.gemini_api_key:
            raise RuntimeError("Gemini API key not configured. Set GEMINI_API_KEY environment variable.")
        
        print("\n✅ GEMINI API AVAILABLE")
        print(f"   Using model: {self.model_name}")
        
        try:
            # Get video properties for context
            import cv2
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            # Upload video to Gemini using new v2 API
            logger.info(f"Uploading video to Gemini: {video_path}")
            print(f"\n📤 Uploading video to Gemini ({os.path.getsize(video_path) / 1024 / 1024:.1f}MB)...")
            upload_start = time.time()
            
            video_file = await self.client.aio.files.upload(file=video_path)
            
            # Wait for file to be processed
            processing_count = 0
            while video_file.state.name == "PROCESSING":
                processing_count += 1
                logger.info("Waiting for Gemini video processing...")
                print(f"⏳ Waiting for Gemini video processing... ({processing_count * 2}s elapsed)")
                await asyncio.sleep(2)
                video_file = await self.client.aio.files.get(name=video_file.name)
            
            upload_elapsed = time.time() - upload_start
            print(f"✅ Video uploaded and processed in {upload_elapsed:.1f}s")
            
            if video_file.state.name == "FAILED":
                print("❌ Gemini video processing FAILED")
                raise ValueError("Gemini video processing failed")
            
            # Use coaching prompt directly (no wrapper needed)
            print("\n🔧 FORMATTING PROMPT...")
            print(f"    Duration: {duration:.2f}")
            print(f"    Frame rate: {fps:.1f}")
            
            try:
                # First escape all curly braces that aren't our placeholders
                # This preserves the JSON example in the prompt
                escaped_prompt = coaching_prompt.replace('{', '{{').replace('}', '}}')
                # Then un-escape only our specific placeholders
                escaped_prompt = escaped_prompt.replace('{{duration}}', '{duration}')
                escaped_prompt = escaped_prompt.replace('{{frame_rate}}', '{frame_rate}')
                
                # Now format with our values
                enhanced_prompt = escaped_prompt.format(
                    duration=f"{duration:.2f}",
                    frame_rate=f"{fps:.1f}"
                )
                print(f"✅ Prompt formatted successfully ({len(enhanced_prompt)} chars)")
            except KeyError as ke:
                print(f"❌ KeyError during prompt formatting: {ke}")
                print(f"    Available keys in prompt: duration, frame_rate")
                print(f"    Error key: {repr(str(ke))}")
                raise
            
            # # Add pose analysis data if available
            # if pose_analysis and pose_analysis.get('success'):
            #     pose_data_summary = {
            #         'angle_analysis': pose_analysis.get('angle_analysis', {}),
            #         'biomechanical_efficiency': pose_analysis.get('biomechanical_efficiency', {}),
            #         'swing_phases': pose_analysis.get('swing_phases', {})
            #     }
            #     enhanced_prompt += f"\n\nPOSE ANALYSIS DATA:\n{json.dumps(pose_data_summary, indent=2)}"
            #     enhanced_prompt += "\n\nPlease incorporate this precise pose analysis data into your coaching feedback."
            
            # Log the prompt being sent to Gemini
            print("\n" + "="*80)
            print("🤖 GEMINI API CALL - Video Analysis")
            print("="*80)
            print(f"📤 SENDING PROMPT TO GEMINI ({len(enhanced_prompt)} chars):")
            print("-"*40)
            print(enhanced_prompt)
            print("-"*40)
            print(f"📹 Video file: {os.path.basename(video_path)}")
            print(f"⏱️  Duration: {duration:.2f}s, FPS: {fps:.1f}")
            print("="*80)
            
            # Generate analysis
            logger.info("Generating Gemini analysis...")
            api_start_time = time.time()
            
            print("\n🚀 CALLING GEMINI API...")
            print(f"    Video file: {video_file}")
            print(f"    Prompt length: {len(enhanced_prompt)} chars")
            
            try:
                # Combine generation config with safety settings
                full_config = {
                    **self.generation_config,
                    'safety_settings': self.safety_settings
                }
                
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=[video_file, enhanced_prompt],
                    config=full_config
                )
                print("✅ Gemini API call completed successfully")
            except Exception as api_error:
                print(f"❌ Gemini API call failed: {type(api_error).__name__}: {api_error}")
                print(f"    Error details: {repr(api_error)}")
                if hasattr(api_error, '__dict__'):
                    print(f"    Error attributes: {api_error.__dict__}")
                raise
            
            api_elapsed = time.time() - api_start_time
            
            # Log the raw response with careful error handling
            print(f"\n📥 GEMINI RESPONSE (received in {api_elapsed:.1f}s):")
            print("-"*40)
            
            try:
                # Try to access response.text
                response_text = response.text
                print(f"✅ Successfully accessed response.text")
                print(f"Raw response text ({len(response_text)} chars):")
                print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                print(f"First 50 chars repr: {repr(response_text[:50])}")
            except Exception as e:
                print(f"❌ ERROR accessing response.text: {type(e).__name__}: {e}")
                print(f"Response object: {response}")
                print(f"Response type: {type(response)}")
                print(f"Response attributes: {dir(response)}")
                # Try alternative ways to get the text
                if hasattr(response, '_result'):
                    print(f"Response._result: {response._result}")
                raise
            
            print("-"*40)
            
            # CRITICAL DEBUG: Capture raw response before ANY processing
            print("\n🔍 RAW RESPONSE DEBUG BEFORE ANY PROCESSING:")
            print(f"Type of response: {type(response)}")
            print(f"Type of response_text: {type(response_text)}")
            print(f"Length: {len(response_text)}")
            print(f"First 100 chars repr: {repr(response_text[:100])}")
            print(f"Last 100 chars repr: {repr(response_text[-100:])}")
            
            # Check if response_text is actually a string
            if not isinstance(response_text, str):
                print(f"⚠️ WARNING: response_text is not a string! Type: {type(response_text)}")
                print(f"⚠️ response_text value: {repr(response_text)}")
            
            # Save raw response for inspection BEFORE parsing
            self._save_raw_response(response_text, "gemini_video_analysis")
            
            # Parse response - strip whitespace and handle formatting issues
            try:
                # Just strip leading/trailing whitespace, don't remove all newlines
                clean_response = response_text.strip()
                
                # Remove markdown code blocks if present
                if clean_response.startswith('```json'):
                    clean_response = clean_response.replace('```json', '').replace('```', '').strip()
                
                # Additional cleanup for common issues
                if clean_response.startswith('"swings"'):
                    # If response starts with "swings", it might be missing the opening brace
                    clean_response = '{' + clean_response
                
                # Log what we're trying to parse
                print(f"🔍 Attempting to parse JSON ({len(clean_response)} chars):")
                print(f"    First 100 chars: {repr(clean_response[:100])}")
                
                # Try to fix common JSON issues
                if clean_response.endswith('} }] }'):
                    # Fix extra spaces in JSON
                    clean_response = clean_response[:-6] + '}]}'
                elif clean_response.endswith('} ] }'):
                    # Fix extra spaces in JSON
                    clean_response = clean_response[:-5] + '}]}'
                
                analysis_result = json.loads(clean_response)
                
                # Validate frame numbers and swing count
                self._validate_analysis_result(analysis_result, duration, fps, frame_count)
                
                # Gemini sometimes returns multiple swings even for short videos
                # Log if we got unexpected number of swings
                num_swings = len(analysis_result.get('swings', []))
                if num_swings > 1:
                    logger.warning(f"Gemini returned {num_swings} swings for a {duration:.1f}s video - using only first swing")
                    print(f"⚠️ Gemini returned {num_swings} swings for a {duration:.1f}s video - using only first swing")
                    # Keep only the first swing
                    analysis_result['swings'] = analysis_result['swings'][:1]
                
                # Convert frame numbers to timestamps
                self._convert_frames_to_timestamps(analysis_result, fps)
                
                # Clean up analysis to match prompt specification (remove impact phase)
                self._clean_analysis_phases(analysis_result)
                
                logger.info("Successfully parsed Gemini JSON response")
                print("\n✅ SUCCESSFULLY PARSED JSON RESPONSE")
                print(f"📊 Analysis contains: {list(analysis_result.keys())}")
                print("="*80)
            except json.JSONDecodeError as e:
                logger.error(f"Gemini JSON parsing failed: {e}")
                print(f"\n❌ JSON PARSING FAILED: {e}")
                print(f"📄 Raw response length: {len(response_text)} chars")
                print(f"📄 First 200 chars: {repr(response_text[:200])}")
                print(f"📄 Last 200 chars: {repr(response_text[-200:])}")
                print(f"📄 Cleaned response first 200 chars: {repr(clean_response[:200])}")
                print("="*80)
                # Don't fall back to mock - raise the actual error with detailed info
                raise ValueError(f"Gemini JSON parsing failed: {e}. Raw response: {repr(response_text[:100])}")
            
            # Clean up uploaded file
            try:
                await self.client.aio.files.delete(name=video_file.name)
                logger.info("Cleaned up uploaded video file from Gemini")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup Gemini file: {cleanup_error}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            print(f"\n💥 EXCEPTION CAUGHT IN GEMINI ANALYSIS:")
            print(f"    Exception type: {type(e)}")
            print(f"    Exception message: {repr(str(e))}")
            print(f"    Full exception: {repr(e)}")
            raise RuntimeError(f"Gemini video analysis failed: {e}")
    
    
    async def get_analysis_status(self, analysis_id: int, user_id: int) -> Dict[str, Any]:
        """Get the status of an analysis."""
        try:
            async with AsyncSessionLocal() as session:
                analysis = await session.get(VideoAnalysis, analysis_id)
                
                if not analysis or analysis.user_id != user_id:
                    raise ValueError("Analysis not found or access denied")
                
                return {
                    "analysis_id": analysis_id,
                    "status": analysis.status.value,
                    "created_at": analysis.created_at.isoformat(),
                    "processing_started_at": analysis.processing_started_at.isoformat() if analysis.processing_started_at else None,
                    "processing_completed_at": analysis.processing_completed_at.isoformat() if analysis.processing_completed_at else None,
                    "error_message": analysis.error_message,
                    "is_completed": analysis.is_completed,
                    "is_failed": analysis.is_failed,
                    "is_processing": analysis.is_processing
                }
                
        except Exception as e:
            logger.error(f"Failed to get analysis status: {e}")
            raise
    
    async def get_analysis_results(self, analysis_id: int, user_id: int) -> Dict[str, Any]:
        """Get the results of a completed analysis."""
        try:
            async with AsyncSessionLocal() as session:
                analysis = await session.get(VideoAnalysis, analysis_id)
                
                if not analysis or analysis.user_id != user_id:
                    raise ValueError("Analysis not found or access denied")
                
                if not analysis.is_completed:
                    raise ValueError("Analysis not completed yet")
                
                return {
                    "analysis_id": analysis_id,
                    "status": analysis.status.value,
                    "ai_analysis": analysis.ai_analysis,
                    "video_duration": analysis.video_duration,
                    "analysis_confidence": analysis.analysis_confidence,
                    "created_at": analysis.created_at.isoformat(),
                    "completed_at": analysis.processing_completed_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get analysis results: {e}")
            raise


    async def generate_coaching_script(self, swing_analysis: Dict[str, Any], video_duration: float) -> Dict[str, Any]:
        """Generate sports commentator style coaching script from swing analysis."""
        try:
            # Load the coaching script prompt
            prompt_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "prompts",
                "coaching_script_commentary.txt"
            )
            
            async with aiofiles.open(prompt_path, 'r') as f:
                prompt_template = await f.read()
            
            # Prepare analysis data for the prompt
            analysis_data = {
                "swing_phases": swing_analysis.get("phases", []),
                "overall_score": swing_analysis.get("overall_score", 7),
                "strengths": swing_analysis.get("strengths", []),
                "improvements": swing_analysis.get("improvements", []),
                "key_coaching_points": swing_analysis.get("key_coaching_points", [])
            }
            
            # Format the prompt with proper escaping
            # First escape all curly braces in the template
            escaped_template = prompt_template.replace('{', '{{').replace('}', '}}')
            # Then un-escape only our specific placeholders
            escaped_template = escaped_template.replace('{{analysis_data}}', '{analysis_data}')
            escaped_template = escaped_template.replace('{{video_duration}}', '{video_duration}')
            escaped_template = escaped_template.replace('{{swing_phases}}', '{swing_phases}')
            escaped_template = escaped_template.replace('{{overall_score}}', '{overall_score}')
            
            formatted_prompt = escaped_template.format(
                analysis_data=json.dumps(analysis_data, indent=2),
                video_duration=video_duration,
                swing_phases=len(analysis_data["swing_phases"]),
                overall_score=analysis_data["overall_score"]
            )
            
            # Use Gemini to generate the coaching script if available
            if GEMINI_AVAILABLE and self.gemini_api_key:
                try:
                    # Log the coaching script prompt
                    print("\n" + "="*80)
                    print("🎙️ GEMINI API CALL - Coaching Script Generation")
                    print("="*80)
                    print(f"📤 SENDING PROMPT TO GEMINI ({len(formatted_prompt)} chars):")
                    print("-"*40)
                    print(formatted_prompt[:800] + "..." if len(formatted_prompt) > 800 else formatted_prompt)
                    print("-"*40)
                    
                    api_start_time = time.time()
                    # Combine generation config with safety settings
                    full_config = {
                        **self.generation_config,
                        'safety_settings': self.safety_settings
                    }
                    
                    response = await self.client.aio.models.generate_content(
                        model=self.model_name,
                        contents=[formatted_prompt],
                        config=full_config
                    )
                    api_elapsed = time.time() - api_start_time
                    
                    # Log the response
                    print(f"\n📥 GEMINI RESPONSE (received in {api_elapsed:.1f}s):")
                    print("-"*40)
                    print(f"Raw response text ({len(response.text)} chars):")
                    print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
                    print("-"*40)
                    
                    # Save raw response for inspection
                    self._save_raw_response(response.text, "gemini_coaching_script")
                    
                    script_result = json.loads(response.text)
                    logger.info("Generated coaching script using Gemini AI")
                    
                    # Add missing fields expected by the test
                    script_result['success'] = True
                    script_result['processing_time'] = api_elapsed
                    script_result['total_statements'] = len(script_result.get('statements', []))
                    
                    print("\n✅ SUCCESSFULLY PARSED COACHING SCRIPT")
                    print(f"📊 Script contains {script_result.get('total_statements', 0)} statements")
                    print(f"⏱️ Total duration: {script_result.get('total_duration', 0)}s")
                    print("="*80)
                    
                    return script_result
                except Exception as e:
                    logger.error(f"Gemini coaching script generation failed: {e}")
                    raise RuntimeError(f"Gemini coaching script generation failed: {e}")
            else:
                raise RuntimeError("Gemini AI not configured for coaching script generation")
            
        except Exception as e:
            logger.error(f"Coaching script generation failed: {e}")
            raise
    
    
    def _save_raw_response(self, response_text: str, response_type: str):
        """Save raw LLM response to file for inspection."""
        try:
            # Create test_results directory if it doesn't exist
            test_results_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "test_results"
            )
            os.makedirs(test_results_dir, exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_llm_response_{response_type}_{timestamp}.txt"
            filepath = os.path.join(test_results_dir, filename)
            
            # Save raw response
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"LLM Response Type: {response_type}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Response Length: {len(response_text)} characters\n")
                f.write("="*80 + "\n")
                f.write(response_text)
            
            print(f"💾 Raw LLM response saved: {filename}")
            
        except Exception as e:
            logger.warning(f"Failed to save raw LLM response: {e}")


    def _convert_frames_to_timestamps(self, analysis_result: Dict[str, Any], fps: float) -> None:
        """Convert frame numbers to timestamps using video FPS."""
        try:
            swings = analysis_result.get('swings', [])
            for swing in swings:
                phases = swing.get('phases', {})
                
                for phase_name, phase_data in phases.items():
                    # Convert start_frame and end_frame to start and end timestamps
                    if 'start_frame' in phase_data and 'end_frame' in phase_data:
                        start_frame = float(phase_data['start_frame'])
                        end_frame = float(phase_data['end_frame'])
                        
                        # Convert to timestamps
                        start_timestamp = start_frame / fps
                        end_timestamp = end_frame / fps
                        
                        # Replace frame numbers with timestamps
                        phase_data['start'] = start_timestamp
                        phase_data['end'] = end_timestamp
                        
                        # Remove frame number fields
                        del phase_data['start_frame']
                        del phase_data['end_frame']
                        
                        logger.info(f"Converted {phase_name}: frames {start_frame}-{end_frame} → timestamps {start_timestamp:.2f}-{end_timestamp:.2f}s")
                    
        except Exception as e:
            logger.warning(f"Failed to convert frames to timestamps: {e}")

    def _validate_analysis_result(self, analysis_result: Dict[str, Any], duration: float, fps: float, frame_count: int) -> None:
        """Validate analysis result for realistic frame numbers and swing count."""
        try:
            swings = analysis_result.get('swings', [])
            
            for swing_idx, swing in enumerate(swings):
                phases = swing.get('phases', {})
                
                for phase_name, phase_data in phases.items():
                    start_frame = phase_data.get('start_frame', 0)
                    end_frame = phase_data.get('end_frame', 0)
                    
                    # Check if frame numbers are realistic
                    if start_frame > frame_count:
                        logger.warning(f"Swing {swing_idx} {phase_name} start_frame {start_frame} exceeds video length {frame_count} frames")
                        # Cap to video length
                        phase_data['start_frame'] = min(start_frame, frame_count)
                    
                    if end_frame > frame_count:
                        logger.warning(f"Swing {swing_idx} {phase_name} end_frame {end_frame} exceeds video length {frame_count} frames")
                        # Cap to video length  
                        phase_data['end_frame'] = min(end_frame, frame_count)
                    
                    # Check logical ordering
                    if start_frame >= end_frame:
                        logger.warning(f"Swing {swing_idx} {phase_name} has invalid frame range: {start_frame}-{end_frame}")
            
            # Warn if too many swings for video duration
            if len(swings) > 1 and duration < 10:
                logger.warning(f"Gemini returned {len(swings)} swings for {duration:.1f}s video - this may be incorrect")
                
        except Exception as e:
            logger.warning(f"Failed to validate analysis result: {e}")

    async def _analyze_video_async_parts(self, video_blob_name: str) -> Dict[str, Any]:
        """Async parts of video analysis that can be called from sync context."""
        try:
            # Download video file
            video_path = await self._download_video(video_blob_name)
            
            # Perform pose analysis
            pose_analysis_result = {}
            if self.pose_analysis_service:
                logger.info("Starting pose analysis...")
                pose_analysis_result = await self.pose_analysis_service.analyze_video_pose(video_path)
                logger.info("Pose analysis completed")
            
            # Load coaching prompts
            coaching_prompt = await self._load_coaching_prompt()
            
            # Analyze video with Gemini
            analysis_result = await self._analyze_with_gemini(video_path, coaching_prompt, pose_analysis_result)
            
            # Clean up temporary file
            os.unlink(video_path)
            
            return {
                'analysis_result': analysis_result,
                'pose_analysis': pose_analysis_result
            }
            
        except Exception as e:
            logger.error(f"Async video analysis parts failed: {e}")
            raise
    
    def _clean_analysis_phases(self, analysis_result: Dict[str, Any]) -> None:
        """Remove impact phase and ensure only 4 phases as specified in prompt."""
        try:
            swings = analysis_result.get('swings', [])
            for swing in swings:
                phases = swing.get('phases', {})
                
                # Remove impact phase if present
                if 'impact' in phases:
                    logger.info("Removing 'impact' phase to match prompt specification")
                    del phases['impact']
                
                # Ensure we only have the 4 specified phases
                allowed_phases = ['setup', 'backswing', 'downswing', 'follow_through']
                phases_to_remove = [p for p in phases.keys() if p not in allowed_phases]
                
                for phase_to_remove in phases_to_remove:
                    logger.info(f"Removing unexpected phase '{phase_to_remove}'")
                    del phases[phase_to_remove]
                    
        except Exception as e:
            logger.warning(f"Failed to clean analysis phases: {e}")


# Global service instance
video_analysis_service = None

def get_video_analysis_service():
    """Get the global video analysis service instance."""
    global video_analysis_service
    if video_analysis_service is None:
        video_analysis_service = VideoAnalysisService()
    return video_analysis_service