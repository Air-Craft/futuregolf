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
import tempfile
import aiofiles
import uuid as uuid_lib
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import select

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

from app.core.providers.vision_gemini import GeminiVisionProvider
from app.database.config import AsyncSessionLocal
from app.models.video import Video
from app.models.video_analysis import VideoAnalysis, AnalysisStatus
from app.services.storage_service import get_storage_service


class AnalysisOrchestrator:
    """Orchestrates the video analysis workflow for UUID-based flow"""
    
    def __init__(self):
        self.vision_service = CleanVideoAnalysisService()
        self.storage_service = get_storage_service()
        logger.info("AnalysisOrchestrator initialized")
    
    async def create_analysis_entry(self, user_id: int) -> str:
        """Create a new analysis entry and return UUID"""
        async with AsyncSessionLocal() as session:
            analysis = VideoAnalysis(
                user_id=user_id,
                status=AnalysisStatus.PENDING,  # Use PENDING for awaiting video
                uuid=uuid_lib.uuid4()
            )
            session.add(analysis)
            await session.commit()
            return str(analysis.uuid)
    
    async def attach_video_to_analysis(self, uuid: str, video_blob_name: str) -> bool:
        """Attach uploaded video to analysis entry"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(VideoAnalysis).filter(VideoAnalysis.uuid == uuid_lib.UUID(uuid))
            )
            analysis = result.scalar_one_or_none()
            
            if not analysis:
                logger.error(f"Analysis not found: {uuid}")
                return False
            
            analysis.originalVideoURL = video_blob_name
            analysis.status = AnalysisStatus.PROCESSING  # Use PROCESSING for analysis in progress
            await session.commit()
            return True
    
    async def start_background_analysis(self, uuid: str):
        """Start background analysis task"""
        asyncio.create_task(self.analyze_video_background(uuid))
    
    async def analyze_video_background(self, uuid: str):
        """
        Background task to analyze video.
        
        Steps:
        1. Set status to ANALYZING
        2. Download video from GCS processing folder
        3. Submit to LLM with retry logic
        4. On success: move to processed folder, update DB
        5. On failure: update status and error description
        """
        temp_video_path = None
        
        try:
            logger.info(f"Starting background analysis for UUID: {uuid}")
            
            # Get analysis record
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(VideoAnalysis).filter(VideoAnalysis.uuid == uuid_lib.UUID(uuid))
                )
                analysis = result.scalar_one_or_none()
                
                if not analysis:
                    logger.error(f"Analysis not found: {uuid}")
                    return
                
                # Update status to PROCESSING
                analysis.status = AnalysisStatus.PROCESSING
                analysis.processing_started_at = datetime.utcnow()
                await session.commit()
                
                original_video_url = analysis.originalVideoURL
                user_id = analysis.user_id
                analysis_id = analysis.id
            
            # Extract blob name from URL
            if original_video_url.startswith("gcs://"):
                parts = original_video_url.replace("gcs://", "").split("/", 1)
                if len(parts) > 1:
                    source_blob_name = parts[1]
                else:
                    raise ValueError(f"Invalid GCS URL: {original_video_url}")
            else:
                source_blob_name = original_video_url
            
            # Download video from GCS
            logger.info(f"Downloading video from GCS: {source_blob_name}")
            temp_video_path = await self.vision_service.download_video_from_storage(source_blob_name)
            
            # Analyze video with retry logic
            max_retries = 3
            analysis_result = None
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Analyzing video, attempt {attempt + 1}/{max_retries}")
                    analysis_result = await self.vision_service.analyze_video_file(temp_video_path)
                    break
                except Exception as e:
                    logger.error(f"Analysis attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            if not analysis_result:
                raise RuntimeError("Failed to analyze video after all retries")
            
            # Move video from processing to processed folder
            dest_blob_name = f"processed/{uuid}_original"
            logger.info(f"Moving video from {source_blob_name} to {dest_blob_name}")
            
            move_success = await self.storage_service.move_file(source_blob_name, dest_blob_name)
            if not move_success:
                logger.warning(f"Failed to move video to processed folder")
            
            # Update analysis record with results
            async with AsyncSessionLocal() as session:
                analysis = await session.get(VideoAnalysis, analysis_id)
                if analysis:
                    analysis.originalVideoURL = f"gcs://{self.storage_service.config.bucket_name}/{dest_blob_name}"
                    analysis.processedVideoURL = analysis.originalVideoURL  # Same for now
                    analysis.analysisJSON = analysis_result
                    analysis.ai_analysis = analysis_result  # Keep legacy field updated
                    analysis.video_duration = analysis_result.get('_metadata', {}).get('video_duration', 0)
                    analysis.analysis_confidence = 0.9
                    analysis.status = AnalysisStatus.COMPLETED  # Use COMPLETED which exists in DB
                    analysis.processing_completed_at = datetime.utcnow()
                    await session.commit()
                    
                    logger.info(f"Analysis completed successfully for UUID: {uuid}")
            
        except Exception as e:
            logger.error(f"Background analysis failed for UUID {uuid}: {e}")
            
            # Update analysis record with error
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(VideoAnalysis).filter(VideoAnalysis.uuid == uuid_lib.UUID(uuid))
                )
                analysis = result.scalar_one_or_none()
                
                if analysis:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.errorDescription = str(e)
                    analysis.error_message = str(e)
                    analysis.processing_completed_at = datetime.utcnow()
                    await session.commit()
        
        finally:
            # Clean up temporary file
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.unlink(temp_video_path)
                    logger.info(f"Cleaned up temporary file: {temp_video_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")


class CleanVideoAnalysisService:
    """Clean video analysis service using the GeminiVisionProvider"""
    
    def __init__(self, model_name="gemini-1.5-flash"):
        self.model_name = model_name
        self.vision_provider = GeminiVisionProvider(model_name=self.model_name)
        
        try:
            self.storage_service = get_storage_service()
        except Exception as e:
            logger.warning(f"Storage service not available: {e}")
            self.storage_service = None
        
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
            
            # Analyze video using the vision provider
            analysis_result = await self.vision_provider.analyze_video(video_path, enhanced_prompt)
            
            api_elapsed = analysis_result.get('_metadata', {}).get('analysis_duration', 0)
            logger.info(f"Gemini response received in {api_elapsed:.1f}s")
            
            # Add additional metadata
            analysis_result['_metadata']['video_duration'] = duration
            analysis_result['_metadata']['video_fps'] = fps
            analysis_result['_metadata']['frame_count'] = frame_count
            
            return analysis_result
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise
    
    async def download_video_from_storage(self, video_blob_name: str) -> str:
        """Download video from storage to temporary file"""
        if not self.storage_service:
            raise RuntimeError("Storage service not available")
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Get blob and download
            blob = self.storage_service.bucket.blob(video_blob_name)
            blob.download_to_filename(temp_path)
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