"""
Clean Video Analysis API - Simplified polling-based endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import logging

from database.config import get_db_session
from models.user import User
from models.video import Video
from models.video_analysis import VideoAnalysis
from middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/video-analysis",
    tags=["video-analysis"]
)


@router.get("/video/{video_id}")
async def get_video_analysis(
    video_id: int,
    # current_user: User = Depends(get_current_user),  # TODO: Re-enable auth
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get video analysis results - Main polling endpoint for iOS
    
    Returns:
    - If analysis is complete: Full analysis JSON
    - If analysis is in progress: Status with progress
    - If analysis failed: Error details
    - If no analysis started: Not found
    """
    try:
        # Get video
        video = await db.get(Video, video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # TODO: Re-enable user check when auth is implemented
        # if video.user_id != current_user.id:
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Get analysis
        result = await db.execute(
            select(VideoAnalysis).filter(
                VideoAnalysis.video_id == video_id,
                VideoAnalysis.user_id == video.user_id
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            # No analysis found - this shouldn't happen with auto-analysis
            return {
                "success": False,
                "message": "Analysis not started",
                "status": "not_started",
                "video_id": video_id
            }
        
        if analysis.is_completed and analysis.ai_analysis:
            # Analysis complete - return full results (same format as analyze_video.py)
            return {
                "success": True,
                "analysis": {
                    "id": analysis.id,
                    "status": "completed",
                    "ai_analysis": analysis.ai_analysis,  # Contains the full JSON from Gemini
                    "video_duration": analysis.video_duration,
                    "analysis_confidence": analysis.analysis_confidence,
                    "created_at": analysis.created_at.isoformat(),
                    "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
                }
            }
        elif analysis.is_failed:
            # Analysis failed
            return {
                "success": False,
                "analysis": {
                    "id": analysis.id,
                    "status": "failed",
                    "error_message": analysis.error_message,
                    "created_at": analysis.created_at.isoformat(),
                    "failed_at": analysis.failed_at.isoformat() if analysis.failed_at else None
                }
            }
        else:
            # Analysis in progress
            return {
                "success": True,
                "analysis": {
                    "id": analysis.id,
                    "status": "processing" if analysis.is_processing else "pending",
                    "message": "Analysis in progress" if analysis.is_processing else "Analysis queued",
                    "created_at": analysis.created_at.isoformat(),
                    "started_at": analysis.started_at.isoformat() if analysis.started_at else None
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video analysis for video_id={video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis")


@router.get("/status/{video_id}")
async def get_analysis_status(
    video_id: int,
    # current_user: User = Depends(get_current_user),  # TODO: Re-enable auth
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get analysis status only (lightweight polling endpoint)
    """
    try:
        # Get video
        video = await db.get(Video, video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get analysis
        result = await db.execute(
            select(VideoAnalysis).filter(
                VideoAnalysis.video_id == video_id,
                VideoAnalysis.user_id == video.user_id
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            return {
                "video_id": video_id,
                "status": "not_started",
                "message": "Analysis not started"
            }
        
        if analysis.is_completed:
            return {
                "video_id": video_id,
                "analysis_id": analysis.id,
                "status": "completed",
                "message": "Analysis completed successfully"
            }
        elif analysis.is_failed:
            return {
                "video_id": video_id,
                "analysis_id": analysis.id,
                "status": "failed",
                "message": f"Analysis failed: {analysis.error_message}"
            }
        else:
            return {
                "video_id": video_id,
                "analysis_id": analysis.id,
                "status": "processing" if analysis.is_processing else "pending",
                "message": "Analysis in progress" if analysis.is_processing else "Analysis queued"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis status for video_id={video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@router.get("/user/analyses")
async def get_user_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all analyses for the current user
    """
    try:
        result = await db.execute(
            select(VideoAnalysis).filter(
                VideoAnalysis.user_id == current_user.id
            ).order_by(VideoAnalysis.created_at.desc())
        )
        analyses = result.scalars().all()
        
        return {
            "user_id": current_user.id,
            "analyses": [
                {
                    "id": analysis.id,
                    "video_id": analysis.video_id,
                    "status": analysis.status.value,
                    "created_at": analysis.created_at.isoformat(),
                    "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
                    "video_duration": analysis.video_duration,
                    "analysis_confidence": analysis.analysis_confidence
                }
                for analysis in analyses
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get user analyses: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analyses")


@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete an analysis record
    """
    try:
        analysis = await db.get(VideoAnalysis, analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        await db.delete(analysis)
        await db.commit()
        
        return {
            "success": True,
            "message": "Analysis deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete analysis")