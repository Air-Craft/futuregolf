"""
API endpoints for the refactored video analysis flow.
Implements UUID-based two-step upload process.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional
import logging
import uuid

from app.database.config import get_db_session
from app.models.user import User
from app.models.video_analysis import VideoAnalysis, AnalysisStatus
from app.middleware.auth_middleware import get_current_user
from app.config.api import API_VERSION_PREFIX
from app.services.storage_service import get_storage_service
from app.services.video_analysis_service import AnalysisOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{API_VERSION_PREFIX}/analysis",
    tags=["analysis"]
)

# Initialize the orchestrator
orchestrator = AnalysisOrchestrator()


@router.post("/create")
async def create_analysis(
    user_id: Optional[int] = None,  # TODO: Get from auth when re-enabled
    # current_user: User = Depends(get_current_user),  # TODO: Re-enable auth
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, str]:
    """
    Create a new analysis entry and return a UUID.
    
    Returns:
        Dict with uuid field
    """
    try:
        # TODO: Use current_user.id when auth is re-enabled
        if not user_id:
            user_id = 1  # Default for testing
        
        # Create new analysis entry
        analysis = VideoAnalysis(
            user_id=user_id,
            status=AnalysisStatus.PENDING,  # Use PENDING which exists in DB
            uuid=uuid.uuid4()
        )
        
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        logger.info(f"Created analysis entry with UUID: {analysis.uuid}")
        
        return {"uuid": str(analysis.uuid)}
        
    except Exception as e:
        logger.error(f"Failed to create analysis entry: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create analysis entry")


@router.put("/{uuid}/video")
async def upload_video_to_analysis(
    uuid: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    # current_user: User = Depends(get_current_user),  # TODO: Re-enable auth
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Attach a video file to a specific analysis entry.
    
    Args:
        uuid: Analysis UUID
        file: Video file to upload
        
    Returns:
        Success status and message
    """
    try:
        # Parse and validate UUID
        try:
            analysis_uuid = uuid_lib.UUID(uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")
        
        # Get analysis entry
        result = await db.execute(
            select(VideoAnalysis).filter(VideoAnalysis.uuid == analysis_uuid)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # TODO: Check user ownership when auth is re-enabled
        # if analysis.user_id != current_user.id:
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Check status (PENDING is our "awaiting video" state for now)
        if analysis.status != AnalysisStatus.PENDING:
            raise HTTPException(
                status_code=400, 
                detail=f"Analysis is in {analysis.status.value} state, cannot upload video"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Reset file pointer
        await file.seek(0)
        
        # Upload to GCS processing folder
        storage_service = get_storage_service()
        blob_name = f"processing/{str(analysis_uuid)}_original"
        
        upload_result = await storage_service.upload_video(
            file=file.file,
            filename=blob_name,
            user_id=analysis.user_id,
            video_id=0,  # We don't have a video record in this flow
            content_type=file.content_type or 'video/mp4'
        )
        
        if not upload_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload video: {upload_result.get('error', 'Unknown error')}"
            )
        
        # Update analysis record
        analysis.originalVideoURL = f"gcs://{storage_service.config.bucket_name}/{blob_name}"
        analysis.status = AnalysisStatus.PROCESSING  # Use PROCESSING for analysis in progress
        
        await db.commit()
        await db.refresh(analysis)  # Refresh to ensure we have the latest state
        
        # Get status value before exiting session context
        status_value = analysis.status.value
        
        # Spawn background task for analysis
        logger.info(f"Queuing background analysis for UUID: {analysis_uuid}")
        background_tasks.add_task(
            orchestrator.analyze_video_background,
            str(analysis_uuid)
        )
        
        return {
            "success": True,
            "message": "Video uploaded successfully, analysis started",
            "uuid": str(analysis_uuid),
            "status": status_value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload video for analysis {uuid}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to upload video")


@router.get("/{uuid}")
async def get_analysis(
    uuid: str,
    # current_user: User = Depends(get_current_user),  # TODO: Re-enable auth
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get analysis status and results.
    
    Args:
        uuid: Analysis UUID
        
    Returns:
        Complete analysis record as JSON
    """
    try:
        # Parse and validate UUID
        try:
            analysis_uuid = uuid_lib.UUID(uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")
        
        # Get analysis entry
        result = await db.execute(
            select(VideoAnalysis).filter(VideoAnalysis.uuid == analysis_uuid)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # TODO: Check user ownership when auth is re-enabled
        # if analysis.user_id != current_user.id:
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Build response based on status
        response = {
            "uuid": str(analysis.uuid),
            "status": analysis.status.value,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None
        }
        
        # Add URLs if available
        if analysis.originalVideoURL:
            response["originalVideoURL"] = analysis.originalVideoURL
        if analysis.processedVideoURL:
            response["processedVideoURL"] = analysis.processedVideoURL
        
        # Add analysis data based on status
        if analysis.status == AnalysisStatus.COMPLETED:
            response["analysisJSON"] = analysis.analysisJSON or analysis.ai_analysis
            response["video_duration"] = analysis.video_duration
            response["analysis_confidence"] = analysis.analysis_confidence
            response["completed_at"] = (
                analysis.processing_completed_at.isoformat() 
                if analysis.processing_completed_at else None
            )
        elif analysis.status == AnalysisStatus.FAILED:
            response["errorDescription"] = analysis.errorDescription or analysis.error_message
            response["failed_at"] = (
                analysis.processing_completed_at.isoformat() 
                if analysis.processing_completed_at else None
            )
        elif analysis.status == AnalysisStatus.PROCESSING:
            response["message"] = "Analysis in progress"
            if analysis.processing_started_at:
                response["started_at"] = analysis.processing_started_at.isoformat()
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis {uuid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis")


# Import uuid library at the top
import uuid as uuid_lib