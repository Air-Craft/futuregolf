"""
Google Cloud Storage service for handling video uploads and management.
"""

import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, BinaryIO, Tuple, List
import logging
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError, NotFound
from app.config.storage import storage_config

logger = logging.getLogger(__name__)


class StorageService:
    """Service for handling video storage operations."""
    
    def __init__(self):
        self.config = storage_config
        self.client = self.config.get_storage_client()
        self.bucket = self.config.get_bucket()
    
    async def upload_video(
        self, 
        file: BinaryIO, 
        filename: str, 
        user_id: int, 
        video_id: int,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a video file to Google Cloud Storage."""
        try:
            # Validate file type
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
            
            if not self.config.is_valid_video_type(content_type):
                raise ValueError(f"Invalid video type: {content_type}")
            
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Generate storage path
            blob_name = self.config.get_file_path(
                user_id, video_id, "video", unique_filename
            )
            
            # Create blob
            blob = self.bucket.blob(blob_name)
            blob.content_type = content_type
            
            # Add metadata
            blob.metadata = {
                "user_id": str(user_id),
                "video_id": str(video_id),
                "original_filename": filename,
                "uploaded_at": datetime.utcnow().isoformat(),
                "file_type": "video"
            }
            
            # Upload file
            file.seek(0)
            file_size = len(file.read())
            file.seek(0)
            
            # Always use simple upload for now (golf videos are typically < 100MB)
            blob.upload_from_file(file, content_type=content_type)
            upload_result = {
                "blob_name": blob_name,
                "size": file_size,
                "resumable": False
            }
            
            # Get public URL
            public_url = self.config.get_public_url(blob_name)
            
            return {
                "success": True,
                "blob_name": blob_name,
                "public_url": public_url,
                "file_size": file_size,
                "content_type": content_type,
                "upload_result": upload_result
            }
            
        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    
    async def upload_thumbnail(
        self, 
        thumbnail_data: bytes, 
        user_id: int, 
        video_id: int,
        format: str = "jpeg"
    ) -> Dict[str, Any]:
        """Upload video thumbnail."""
        try:
            # Generate filename
            filename = f"thumbnail_{uuid.uuid4()}.{format}"
            blob_name = self.config.get_file_path(
                user_id, video_id, "thumbnail", filename
            )
            
            # Create blob
            blob = self.bucket.blob(blob_name)
            blob.content_type = f"image/{format}"
            
            # Add metadata
            blob.metadata = {
                "user_id": str(user_id),
                "video_id": str(video_id),
                "file_type": "thumbnail",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Upload thumbnail
            blob.upload_from_string(thumbnail_data, content_type=f"image/{format}")
            
            return {
                "success": True,
                "blob_name": blob_name,
                "public_url": self.config.get_public_url(blob_name),
                "size": len(thumbnail_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to upload thumbnail: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_processed_video(
        self, 
        processed_data: bytes, 
        user_id: int, 
        video_id: int,
        processing_type: str = "analysis"
    ) -> Dict[str, Any]:
        """Upload processed video with overlays."""
        try:
            # Generate filename
            filename = f"processed_{processing_type}_{uuid.uuid4()}.mp4"
            blob_name = self.config.get_file_path(
                user_id, video_id, "processed", filename
            )
            
            # Create blob
            blob = self.bucket.blob(blob_name)
            blob.content_type = "video/mp4"
            
            # Add metadata
            blob.metadata = {
                "user_id": str(user_id),
                "video_id": str(video_id),
                "file_type": "processed_video",
                "processing_type": processing_type,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Upload processed video
            blob.upload_from_string(processed_data, content_type="video/mp4")
            
            return {
                "success": True,
                "blob_name": blob_name,
                "public_url": self.config.get_public_url(blob_name),
                "size": len(processed_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to upload processed video: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_signed_url(self, blob_name: str, expiration_hours: int = None) -> str:
        """Generate signed URL for private video access."""
        try:
            if expiration_hours is None:
                expiration_hours = self.config.signed_url_expiration
            
            blob = self.bucket.blob(blob_name)
            
            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(hours=expiration_hours),
                method="GET"
            )
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise
    
    async def delete_file(self, blob_name: str) -> bool:
        """Delete a file from storage."""
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Deleted file: {blob_name}")
            return True
            
        except NotFound:
            logger.warning(f"File not found for deletion: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {blob_name}: {e}")
            return False
    
    async def get_file_metadata(self, blob_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a file."""
        try:
            blob = self.bucket.blob(blob_name)
            blob.reload()
            
            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created,
                "updated": blob.updated,
                "metadata": blob.metadata,
                "public_url": self.config.get_public_url(blob_name)
            }
            
        except NotFound:
            logger.warning(f"File not found: {blob_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None
    
    async def list_user_files(self, user_id: int, file_type: str = None) -> List[Dict[str, Any]]:
        """List all files for a user."""
        try:
            prefix = f"user_{user_id}/"
            if file_type:
                folder_map = {
                    "video": self.config.video_folder,
                    "thumbnail": self.config.thumbnail_folder,
                    "processed": self.config.processed_folder
                }
                folder = folder_map.get(file_type)
                if folder:
                    prefix = f"{folder}/{prefix}"
            
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "created": blob.time_created,
                    "public_url": self.config.get_public_url(blob.name),
                    "metadata": blob.metadata
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list user files: {e}")
            return []
    
    async def cleanup_temp_files(self, days_old: int = None) -> int:
        """Clean up temporary files older than specified days."""
        try:
            if days_old is None:
                days_old = self.config.auto_delete_temp_days
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            temp_prefix = f"{self.config.temp_folder}/"
            
            blobs = self.bucket.list_blobs(prefix=temp_prefix)
            deleted_count = 0
            
            for blob in blobs:
                if blob.time_created < cutoff_date:
                    blob.delete()
                    deleted_count += 1
                    logger.info(f"Deleted old temp file: {blob.name}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0


# Global service instance (lazy-loaded)
storage_service = None

def get_storage_service():
    """Get the global storage service instance, creating it if needed."""
    global storage_service
    if storage_service is None:
        storage_service = StorageService()
    return storage_service