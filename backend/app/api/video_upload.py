"""
FastAPI endpoints for video upload and management using Google Cloud Storage.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.database.config import get_db
from app.models.video import Video, VideoStatus
from app.services.storage_service import get_storage_service
from app.services.video_analysis_service import get_clean_video_analysis_service
from app.config.storage import storage_config
from app.config.api import API_VERSION_PREFIX

router = APIRouter(prefix=f"{API_VERSION_PREFIX}/videos", tags=["videos"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=dict)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a video file to Google Cloud Storage."""
    try:
        logger.info(f"Received upload request - file: {file.filename}, user_id: {user_id}")
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size
        file_size = 0
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > storage_config.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {storage_config.max_file_size / 1024 / 1024}MB"
            )
        
        # Create video record in database
        video = Video(
            user_id=user_id,
            title=title,
            description=description,
            original_filename=file.filename,
            file_size=file_size,
            status=VideoStatus.UPLOADING
        )
        
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # Reset file pointer and upload to GCS
        await file.seek(0)
        
        # Upload directly with the file object
        upload_result = await get_storage_service().upload_video(
            file=file.file,
            filename=file.filename,
            user_id=user_id,
            video_id=video.id,
            content_type=file.content_type or 'video/mp4'
        )
        
        if upload_result["success"]:
            # Update video record with storage info
            video.video_url = upload_result["public_url"]
            video.video_blob_name = upload_result.get("blob_name", upload_result["public_url"].split("/")[-1])
            video.mark_as_uploaded()
            
            db.commit()
            db.refresh(video)
            
            # Auto-trigger background analysis using the clean analysis service
            logger.info(f"Auto-triggering background analysis for video_id={video.id}")
            try:
                analysis_service = get_clean_video_analysis_service()
                background_tasks.add_task(
                    analysis_service.analyze_video_from_storage,
                    video.id,
                    user_id
                )
                logger.info(f"Background analysis task queued for video_id={video.id}")
            except Exception as e:
                logger.error(f"Failed to queue background analysis for video_id={video.id}: {e}")
                # Don't fail the upload if analysis queueing fails
            
            return {
                "success": True,
                "video_id": video.id,
                "video_url": video.video_url,
                "file_size": video.file_size,
                "status": video.status.value,
                "analysis_status": "queued",
                "upload_result": upload_result
            }
        else:
            # Update video record with error
            video.mark_as_failed(upload_result["error"])
            db.commit()
            
            raise HTTPException(
                status_code=500,
                detail=f"Upload failed: {upload_result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@router.post("/{video_id}/thumbnail")
async def upload_thumbnail(
    video_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a thumbnail for a video."""
    try:
        # Get video record
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Read thumbnail data
        thumbnail_data = await file.read()
        
        # Upload thumbnail to GCS
        upload_result = await get_storage_service().upload_thumbnail(
            thumbnail_data=thumbnail_data,
            user_id=video.user_id,
            video_id=video_id,
            format="jpeg"
        )
        
        if upload_result["success"]:
            # Update video record
            video.thumbnail_url = upload_result["public_url"]
            db.commit()
            
            return {
                "success": True,
                "thumbnail_url": video.thumbnail_url,
                "size": upload_result["size"]
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Thumbnail upload failed: {upload_result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Thumbnail upload error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{video_id}/signed-url")
async def get_signed_url(
    video_id: int,
    expiration_hours: Optional[int] = 24,
    db: Session = Depends(get_db)
):
    """Get a signed URL for private video access."""
    try:
        # Get video record
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Extract blob name from video URL
        blob_name = video.video_url.split("/")[-1]
        
        # Generate signed URL
        signed_url = await get_storage_service().generate_signed_url(
            blob_name=blob_name,
            expiration_hours=expiration_hours
        )
        
        return {
            "signed_url": signed_url,
            "expires_in_hours": expiration_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signed URL generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{video_id}/metadata")
async def get_video_metadata(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Get video metadata from storage."""
    try:
        # Get video record
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Extract blob name from video URL
        blob_name = video.video_url.split("/")[-1]
        
        # Get storage metadata
        metadata = await get_storage_service().get_file_metadata(blob_name)
        
        if metadata:
            return {
                "video_id": video_id,
                "storage_metadata": metadata,
                "database_metadata": {
                    "title": video.title,
                    "description": video.description,
                    "duration": video.duration,
                    "file_size": video.file_size,
                    "status": video.status.value,
                    "created_at": video.created_at,
                    "updated_at": video.updated_at
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Storage metadata not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Delete a video and all associated files."""
    try:
        # Get video record
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Extract blob names
        video_blob = video.video_url.split("/")[-1] if video.video_url else None
        thumbnail_blob = video.thumbnail_url.split("/")[-1] if video.thumbnail_url else None
        
        # Delete files from storage
        deleted_files = []
        if video_blob:
            if await get_storage_service().delete_file(video_blob):
                deleted_files.append("video")
        
        if thumbnail_blob:
            if await get_storage_service().delete_file(thumbnail_blob):
                deleted_files.append("thumbnail")
        
        # Soft delete video record
        video.soft_delete()
        db.commit()
        
        return {
            "success": True,
            "video_id": video_id,
            "deleted_files": deleted_files,
            "status": "deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video deletion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}")
async def list_user_videos(
    user_id: int,
    file_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all videos for a user."""
    try:
        # Get videos from database
        videos = db.query(Video).filter(
            Video.user_id == user_id,
            Video.status != VideoStatus.DELETED
        ).all()
        
        # Get storage files
        storage_files = await get_storage_service().list_user_files(user_id, file_type)
        
        return {
            "user_id": user_id,
            "video_count": len(videos),
            "videos": [
                {
                    "id": video.id,
                    "title": video.title,
                    "description": video.description,
                    "status": video.status.value,
                    "video_url": video.video_url,
                    "thumbnail_url": video.thumbnail_url,
                    "file_size": video.file_size,
                    "duration": video.duration,
                    "created_at": video.created_at,
                    "is_favorite": video.is_favorite
                }
                for video in videos
            ],
            "storage_files": storage_files
        }
        
    except Exception as e:
        logger.error(f"User videos listing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cleanup-temp")
async def cleanup_temp_files(days_old: Optional[int] = None):
    """Clean up temporary files (admin endpoint)."""
    try:
        deleted_count = await get_storage_service().cleanup_temp_files(days_old)
        
        return {
            "success": True,
            "deleted_files": deleted_count,
            "days_old": days_old or storage_config.auto_delete_temp_days
        }
        
    except Exception as e:
        logger.error(f"Temp cleanup error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")