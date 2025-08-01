"""
Synchronous video analysis functions for background tasks.
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from models.video_analysis import VideoAnalysis, AnalysisStatus
from models.video import Video

logger = logging.getLogger(__name__)

# Get database URL for sync operations
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Create sync engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def analyze_video_sync(video_analysis_service, video_id: int, user_id: int) -> None:
    """
    Synchronous video analysis for background tasks.
    This avoids async event loop conflicts.
    """
    try:
        analysis_id = None
        
        # Use sync database session
        with SessionLocal() as session:
            # Get video
            video = session.get(Video, video_id)
            if not video or video.user_id != user_id:
                raise ValueError("Video not found or access denied")
            
            # Get or create analysis record
            result = session.execute(
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
            
            analysis.start_processing()
            session.commit()
            analysis_id = analysis.id
            
            # Store video info - use video_url if blob_name is not set
            video_blob_name = video.video_blob_name or video.video_url
            
        logger.info(f"Starting sync video analysis for video_id={video_id}, user_id={user_id}")
        
        # Call the async analyze method in a controlled way
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the analysis parts that need async
            result = loop.run_until_complete(
                video_analysis_service._analyze_video_async_parts(video_blob_name)
            )
            
            # Update analysis with results using sync session
            with SessionLocal() as session:
                analysis = session.get(VideoAnalysis, analysis_id)
                if analysis:
                    analysis.ai_analysis = result.get('analysis_result', {})
                    analysis.pose_data = result.get('pose_analysis', {})
                    analysis.body_position_data = result.get('pose_analysis', {}).get('angle_analysis', {})
                    analysis.swing_metrics = result.get('pose_analysis', {}).get('biomechanical_efficiency', {})
                    analysis.video_duration = result.get('analysis_result', {}).get("duration", 0)
                    analysis.analysis_confidence = result.get('analysis_result', {}).get("confidence", 0.8)
                    analysis.mark_as_completed()
                    session.commit()
                    
            logger.info(f"Video analysis completed for video_id={video_id}")
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Sync video analysis failed for video_id={video_id}: {e}")
        
        # Update analysis record with error using sync session
        if analysis_id:
            try:
                with SessionLocal() as session:
                    analysis = session.get(VideoAnalysis, analysis_id)
                    if analysis:
                        analysis.mark_as_failed(str(e))
                        session.commit()
            except Exception as db_error:
                logger.error(f"Failed to update analysis record: {db_error}")