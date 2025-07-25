"""
API endpoints for video analysis functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import logging

from database.config import get_db_session
from models.user import User
from models.video import Video
from models.video_analysis import VideoAnalysis
from middleware.auth_middleware import get_current_user
from services.video_analysis_service import get_video_analysis_service
from api.schemas import VideoAnalysisResponse, VideoAnalysisStatusResponse, VideoAnalysisResultsResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/video-analysis",
    tags=["video-analysis"]
)

# Get service instance
video_analysis_service = get_video_analysis_service()


@router.post("/analyze/{video_id}")
async def analyze_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    # current_user: User = Depends(get_current_user),  # TODO: Re-enable auth
    db: AsyncSession = Depends(get_db_session)
):
    """
    Start video analysis for a specific video.
    
    Args:
        video_id: The ID of the video to analyze
        background_tasks: FastAPI background tasks
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Dict with analysis initiation details
    """
    try:
        # Verify video exists and belongs to user
        video = await db.get(Video, video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # TODO: Re-enable user check when auth is implemented
        # if video.user_id != current_user.id:
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if analysis already exists
        existing_analysis = await db.execute(
            select(VideoAnalysis).filter(
                VideoAnalysis.video_id == video_id,
                VideoAnalysis.user_id == video.user_id  # Use video's user_id
            )
        )
        analysis = existing_analysis.scalar_one_or_none()
        
        if analysis and analysis.is_completed:
            return {
                "success": True,
                "message": "Analysis already completed",
                "analysis_id": analysis.id,
                "status": "completed"
            }
        
        if analysis and analysis.is_processing:
            return {
                "success": True,
                "message": "Analysis already in progress",
                "analysis_id": analysis.id,
                "status": "processing"
            }
        
        # Start background analysis
        background_tasks.add_task(
            video_analysis_service.analyze_video_sync,
            video_id,
            video.user_id  # Use video's user_id instead of current_user
        )
        
        return {
            "success": True,
            "message": "Video analysis started",
            "video_id": video_id,
            "status": "started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start video analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")


@router.get("/status/{analysis_id}")
async def get_analysis_status(
    analysis_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a video analysis.
    
    Args:
        analysis_id: The ID of the analysis
        current_user: The authenticated user
        
    Returns:
        Dict with analysis status
    """
    try:
        status = await video_analysis_service.get_analysis_status(
            analysis_id, 
            current_user.id
        )
        
        return {
            "success": True,
            "status": status
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get analysis status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis status")


@router.get("/results/{analysis_id}")
async def get_analysis_results(
    analysis_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get the results of a completed video analysis.
    
    Args:
        analysis_id: The ID of the analysis
        current_user: The authenticated user
        
    Returns:
        Dict with analysis results
    """
    try:
        results = await video_analysis_service.get_analysis_results(
            analysis_id, 
            current_user.id
        )
        
        return {
            "success": True,
            "results": results
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get analysis results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis results")


@router.get("/video/{video_id}")
async def get_video_analysis(
    video_id: int,
    # current_user: User = Depends(get_current_user),  # TODO: Re-enable auth
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get analysis for a specific video.
    
    Args:
        video_id: The ID of the video
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Dict with video analysis if exists
    """
    try:
        # Verify video exists and belongs to user
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
                VideoAnalysis.user_id == video.user_id  # Use video's user_id
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            return {
                "success": True,
                "message": "No analysis found for this video",
                "analysis": None
            }
        
        return {
            "success": True,
            "analysis": {
                "id": analysis.id,
                "status": analysis.status.value,
                "created_at": analysis.created_at.isoformat(),
                "completed_at": analysis.processing_completed_at.isoformat() if analysis.processing_completed_at else None,
                "ai_analysis": analysis.ai_analysis if analysis.is_completed else None,
                "pose_analysis": analysis.pose_data if analysis.is_completed else None,
                "body_angles": analysis.body_position_data if analysis.is_completed else None,
                "biomechanical_scores": analysis.swing_metrics if analysis.is_completed else None,
                "confidence": analysis.analysis_confidence if analysis.is_completed else None,
                "error_message": analysis.error_message if analysis.is_failed else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video analysis")


@router.get("/user/analyses")
async def get_user_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all analyses for the current user.
    
    Args:
        current_user: The authenticated user
        db: Database session
        
    Returns:
        List of user's analyses
    """
    try:
        result = await db.execute(
            select(VideoAnalysis).filter(
                VideoAnalysis.user_id == video.user_id  # Use video's user_id
            ).order_by(VideoAnalysis.created_at.desc())
        )
        analyses = result.scalars().all()
        
        return {
            "success": True,
            "analyses": [
                {
                    "id": analysis.id,
                    "video_id": analysis.video_id,
                    "status": analysis.status.value,
                    "created_at": analysis.created_at.isoformat(),
                    "completed_at": analysis.processing_completed_at.isoformat() if analysis.processing_completed_at else None,
                    "confidence": analysis.analysis_confidence if analysis.is_completed else None,
                    "has_results": analysis.is_completed,
                    "error_message": analysis.error_message if analysis.is_failed else None
                }
                for analysis in analyses
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get user analyses: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user analyses")


@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a video analysis.
    
    Args:
        analysis_id: The ID of the analysis to delete
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Success confirmation
    """
    try:
        # Get analysis
        analysis = await db.get(VideoAnalysis, analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete analysis
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


@router.get("/pose-analysis/{analysis_id}")
async def get_pose_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed pose analysis data for a specific analysis.
    
    Args:
        analysis_id: The ID of the analysis
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Dict with detailed pose analysis data
    """
    try:
        # Get analysis
        analysis = await db.get(VideoAnalysis, analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not analysis.is_completed:
            raise HTTPException(status_code=400, detail="Analysis not completed yet")
        
        # Extract pose analysis data
        pose_data = analysis.pose_data or {}
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "pose_analysis": {
                "angle_analysis": pose_data.get("angle_analysis", {}),
                "swing_phases": pose_data.get("swing_phases", {}),
                "biomechanical_efficiency": pose_data.get("biomechanical_efficiency", {}),
                "frame_by_frame_status": pose_data.get("frame_by_frame_status", []),
                "recommendations": pose_data.get("recommendations", []),
                "optimal_ranges": pose_data.get("optimal_ranges", {}),
                "analysis_metadata": pose_data.get("analysis_metadata", {})
            },
            "body_angles": analysis.body_position_data or {},
            "biomechanical_scores": analysis.swing_metrics or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pose analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pose analysis")


@router.get("/body-angles/{analysis_id}")
async def get_body_angles(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get body angle analysis for a specific analysis.
    
    Args:
        analysis_id: The ID of the analysis
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Dict with body angle analysis
    """
    try:
        # Get analysis
        analysis = await db.get(VideoAnalysis, analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not analysis.is_completed:
            raise HTTPException(status_code=400, detail="Analysis not completed yet")
        
        body_angles = analysis.body_position_data or {}
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "body_angles": body_angles,
            "optimal_ranges": {
                "spine_angle": {"min": 30, "max": 45},
                "shoulder_tilt": {"min": 5, "max": 15},
                "hip_rotation": {"min": 30, "max": 45},
                "head_movement": {"lateral": 50, "vertical": 25}
            },
            "swing_phases": ["setup", "backswing_top", "impact", "follow_through"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get body angles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get body angles")


@router.get("/biomechanical-scores/{analysis_id}")
async def get_biomechanical_scores(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get biomechanical efficiency scores for a specific analysis.
    
    Args:
        analysis_id: The ID of the analysis
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Dict with biomechanical efficiency scores
    """
    try:
        # Get analysis
        analysis = await db.get(VideoAnalysis, analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not analysis.is_completed:
            raise HTTPException(status_code=400, detail="Analysis not completed yet")
        
        biomechanical_scores = analysis.swing_metrics or {}
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "biomechanical_scores": biomechanical_scores,
            "score_descriptions": {
                "overall_score": "Overall swing efficiency and biomechanical correctness",
                "kinetic_chain_score": "Efficiency of energy transfer through the kinetic chain",
                "power_transfer_score": "Effectiveness of power transfer from ground to club",
                "balance_score": "Balance and stability throughout the swing"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get biomechanical scores: {e}")
        raise HTTPException(status_code=500, detail="Failed to get biomechanical scores")