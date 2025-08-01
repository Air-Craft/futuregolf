"""
Clean Video Analysis Service - Based on analyze_video.py logic
This service provides the same functionality as analyze_video.py but integrated with the API.
"""

import os
import json
import logging
import asyncio
import time
import cv2
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Gemini AI not available. Install google-genai package.")

from database.config import AsyncSessionLocal
from models.video_analysis import VideoAnalysis, AnalysisStatus
from models.video import Video
from services.storage_service import get_storage_service
import aiofiles
import tempfile

logger = logging.getLogger(__name__)


class CleanVideoAnalysisService:
    """Clean video analysis service using the same logic as analyze_video.py"""
    
    def __init__(self, model_name="gemini-2.5-flash"):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        
        try:
            self.storage_service = get_storage_service()
        except Exception as e:
            logger.warning(f"Storage service not available: {e}")
            self.storage_service = None
        
        if not GEMINI_AVAILABLE:
            logger.error("Google Gemini AI not available")
            raise RuntimeError("Google Gemini AI not available. Install google-genai package.")
        
        if not self.gemini_api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise RuntimeError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini AI with new v2 API (exact same as analyze_video.py)
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
        
        # Generation config (exact same as analyze_video.py)
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            safety_settings=self.safety_settings
        )
        
        logger.info(f"Clean VideoAnalysisService initialized with model: {self.model_name}")
    
    async def load_prompt(self) -> str:
        """Load the coaching prompt template (exact same as analyze_video.py)"""
        try:
            prompt_path = os.path.join(
                os.path.dirname(__file__), 
                "..",
                "prompts", 
                "video_analysis_swing_coaching.txt"
            )
            
            async with aiofiles.open(prompt_path, 'r') as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Failed to load coaching prompt: {e}")
            raise RuntimeError(f"Failed to load coaching prompt: {e}")
    
    async def analyze_video_file(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze video file - exact same logic as analyze_video.py but returns parsed JSON
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        logger.info(f"Analyzing video: {video_path}")
        
        try:
            # Get video properties (exact same as analyze_video.py)
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            logger.info(f"Video properties: Duration={duration:.2f}s, FPS={fps:.1f}, Frames={frame_count}")
            
            # Load prompt (exact same as analyze_video.py)
            logger.info("Loading coaching prompt...")
            coaching_prompt = await self.load_prompt()
            
            # Format prompt (exact same as analyze_video.py)
            try:
                escaped_prompt = coaching_prompt.replace('{', '{{').replace('}', '}}')
                escaped_prompt = escaped_prompt.replace('{{duration}}', '{duration}')
                escaped_prompt = escaped_prompt.replace('{{frame_rate}}', '{frame_rate}')
                
                enhanced_prompt = escaped_prompt.format(
                    duration=f"{duration:.2f}",
                    frame_rate=f"{fps:.1f}"
                )
                logger.info(f"Prompt formatted successfully ({len(enhanced_prompt)} chars)")
            except KeyError as ke:
                logger.error(f"KeyError during prompt formatting: {ke}")
                raise RuntimeError(f"Prompt formatting failed: {ke}")
            
            # Upload video to Gemini (exact same as analyze_video.py)
            file_size_mb = os.path.getsize(video_path) / 1024 / 1024
            logger.info(f"Uploading video to Gemini ({file_size_mb:.1f}MB)...")
            upload_start = time.time()
            
            video_file = await self.client.aio.files.upload(file=video_path)
            
            # Wait for processing (exact same as analyze_video.py)
            processing_count = 0
            while video_file.state.name == "PROCESSING":
                processing_count += 1
                if processing_count > 30:  # Max 60 seconds wait
                    raise RuntimeError("Gemini video processing timeout")
                logger.info(f"Waiting for Gemini video processing... ({processing_count * 2}s elapsed)")
                await asyncio.sleep(2)
                video_file = await self.client.aio.files.get(name=video_file.name)
            
            upload_elapsed = time.time() - upload_start
            logger.info(f"Video uploaded and processed in {upload_elapsed:.1f}s")
            
            if video_file.state.name == "FAILED":
                raise RuntimeError("Gemini video processing FAILED")
            
            # Generate analysis (exact same as analyze_video.py)
            logger.info(f"Calling Gemini API with model: {self.model_name}")
            api_start_time = time.time()
            
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=[video_file, enhanced_prompt],
                    config=self.generation_config
                )
                logger.info("Gemini API call completed successfully")
            except Exception as api_error:
                logger.error(f"Gemini API call failed: {type(api_error).__name__}: {api_error}")
                raise RuntimeError(f"Gemini API call failed: {api_error}")
            
            api_elapsed = time.time() - api_start_time
            logger.info(f"Gemini response received in {api_elapsed:.1f}s")
            
            # Parse response (exact same validation as analyze_video.py)
            try:
                response_text = response.text
                logger.info(f"Response length: {len(response_text)} characters")
                
                # Parse JSON
                parsed_result = json.loads(response_text.strip())
                logger.info("Response is valid JSON")
                logger.info(f"JSON structure: {list(parsed_result.keys())}")
                
                # Add metadata
                parsed_result['_metadata'] = {
                    'analysis_duration': api_elapsed,
                    'video_duration': duration,
                    'video_fps': fps,
                    'frame_count': frame_count,
                    'model_used': self.model_name,
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
                
                return parsed_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Response is not valid JSON: {e}")
                logger.error(f"Raw response: {response_text[:500]}...")
                raise RuntimeError(f"Invalid JSON response from Gemini: {e}")
            except Exception as e:
                logger.error(f"Error accessing response text: {e}")
                raise RuntimeError(f"Error processing Gemini response: {e}")
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise
        finally:
            # Clean up Gemini file
            try:
                if 'video_file' in locals():
                    await self.client.aio.files.delete(name=video_file.name)
                    logger.info("Cleaned up uploaded Gemini file")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup Gemini file: {cleanup_error}")
    
    async def download_video_from_storage(self, video_blob_name: str) -> str:
        """Download video from storage to temporary file"""
        if not self.storage_service:
            raise RuntimeError("Storage service not available")
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Download from storage
            await self.storage_service.download_file(video_blob_name, temp_path)
            logger.info(f"Downloaded video from storage: {video_blob_name} -> {temp_path}")
            return temp_path
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            logger.error(f"Failed to download video {video_blob_name}: {e}")
            raise
    
    async def analyze_video_from_storage(self, video_id: int, user_id: int) -> Dict[str, Any]:
        """
        Complete analysis flow: get video from DB, download from storage, analyze, save results
        """
        analysis_id = None
        temp_video_path = None
        
        try:
            # Use database session
            async with AsyncSessionLocal() as session:
                # Get video record
                video = await session.get(Video, video_id)
                if not video or video.user_id != user_id:
                    raise ValueError("Video not found or access denied")
                
                # Get or create analysis record
                from sqlalchemy import select
                result = await session.execute(
                    select(VideoAnalysis).filter(
                        VideoAnalysis.video_id == video_id,
                        VideoAnalysis.user_id == user_id
                    )
                )
                analysis = result.scalar_one_or_none()
                
                if not analysis:
                    analysis = VideoAnalysis(
                        user_id=user_id,
                        video_id=video_id,
                        status=AnalysisStatus.PENDING
                    )
                    session.add(analysis)
                
                # Mark as processing
                analysis.start_processing()
                await session.commit()
                analysis_id = analysis.id
                
                # Get video storage location
                video_blob_name = video.video_blob_name or video.video_url
                
            logger.info(f"Starting analysis for video_id={video_id}, user_id={user_id}, analysis_id={analysis_id}")
            
            # Download video from storage
            temp_video_path = await self.download_video_from_storage(video_blob_name)
            
            # Analyze video (using exact analyze_video.py logic)
            analysis_result = await self.analyze_video_file(temp_video_path)
            
            # Save results to database
            async with AsyncSessionLocal() as session:
                analysis = await session.get(VideoAnalysis, analysis_id)
                if analysis:
                    analysis.ai_analysis = analysis_result
                    analysis.video_duration = analysis_result.get('_metadata', {}).get('video_duration', 0)
                    analysis.analysis_confidence = 0.9  # High confidence since we got valid JSON
                    analysis.mark_as_completed()
                    await session.commit()
                    
            logger.info(f"Video analysis completed successfully for video_id={video_id}")
            return {
                "success": True,
                "analysis_id": analysis_id,
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
            
            raise
        finally:
            # Clean up temporary video file
            if temp_video_path and os.path.exists(temp_video_path):
                os.unlink(temp_video_path)
                logger.info("Cleaned up temporary video file")


# Service instance
_service_instance = None

def get_clean_video_analysis_service() -> CleanVideoAnalysisService:
    """Get singleton instance of the clean video analysis service"""
    global _service_instance
    if _service_instance is None:
        _service_instance = CleanVideoAnalysisService()
    return _service_instance