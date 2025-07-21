"""
Google Cloud Storage configuration for FutureGolf application.
"""

import os
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)


class StorageConfig:
    """Configuration class for Google Cloud Storage."""
    
    def __init__(self):
        # Google Cloud project settings
        self.project_id = os.getenv("GCS_PROJECT_ID", "futuregolf")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Handle relative paths relative to backend directory
        if credentials_path and not os.path.isabs(credentials_path):
            # Get the backend directory (parent of config directory)
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.credentials_path = os.path.join(backend_dir, credentials_path)
            logger.info(f"Resolved credentials path: {self.credentials_path}")
        else:
            self.credentials_path = credentials_path
            logger.info(f"Using absolute credentials path: {self.credentials_path}")
        
        # Storage bucket settings
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "futuregolf-videos")
        self.location = os.getenv("GCS_BUCKET_LOCATION", "us-central1")
        
        # Storage class settings
        self.default_storage_class = os.getenv("GCS_DEFAULT_STORAGE_CLASS", "STANDARD")
        self.archive_storage_class = os.getenv("GCS_ARCHIVE_STORAGE_CLASS", "COLDLINE")
        
        # File organization settings
        self.video_folder = "videos"
        self.thumbnail_folder = "thumbnails"
        self.processed_folder = "processed"
        self.temp_folder = "temp"
        
        # Upload settings
        self.max_file_size = int(os.getenv("MAX_VIDEO_SIZE_MB", "500")) * 1024 * 1024  # 500MB default
        self.chunk_size = int(os.getenv("UPLOAD_CHUNK_SIZE", "8192"))  # 8KB default
        self.resumable_threshold = int(os.getenv("RESUMABLE_THRESHOLD_MB", "50")) * 1024 * 1024  # 50MB
        
        # CDN settings
        self.cdn_enabled = os.getenv("GCS_CDN_ENABLED", "true").lower() == "true"
        self.cdn_base_url = os.getenv("GCS_CDN_BASE_URL", "")
        
        # Security settings
        self.signed_url_expiration = int(os.getenv("SIGNED_URL_EXPIRATION_HOURS", "24"))
        self.allowed_video_types = [
            "video/mp4", "video/quicktime", "video/x-msvideo", 
            "video/webm", "video/ogg", "video/3gpp"
        ]
        
        # Lifecycle management
        self.auto_delete_temp_days = int(os.getenv("AUTO_DELETE_TEMP_DAYS", "7"))
        self.auto_archive_days = int(os.getenv("AUTO_ARCHIVE_DAYS", "90"))
        
        # Validation
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration settings."""
        if not self.project_id:
            raise ValueError("GCS_PROJECT_ID environment variable is required")
        
        if not self.credentials_path:
            logger.warning("No Google Cloud credentials found. Ensure service account is configured.")
        elif not os.path.exists(self.credentials_path):
            logger.error(f"Google Cloud credentials file not found at: {self.credentials_path}")
    
    def get_storage_client(self) -> storage.Client:
        """Get Google Cloud Storage client."""
        try:
            if self.credentials_path:
                return storage.Client.from_service_account_json(
                    self.credentials_path, 
                    project=self.project_id
                )
            else:
                # Use default credentials (service account, etc.)
                return storage.Client(project=self.project_id)
        except Exception as e:
            logger.error(f"Failed to create storage client: {e}")
            raise
    
    def get_bucket(self) -> storage.Bucket:
        """Get or create the storage bucket."""
        client = self.get_storage_client()
        bucket = client.bucket(self.bucket_name)
        
        # Check if bucket exists, create if not
        try:
            bucket.reload()
        except GoogleCloudError:
            logger.info(f"Creating bucket: {self.bucket_name}")
            bucket = client.create_bucket(
                self.bucket_name,
                location=self.location
            )
            bucket.storage_class = self.default_storage_class
            bucket.patch()
            self._configure_bucket_lifecycle(bucket)
        
        return bucket
    
    def _configure_bucket_lifecycle(self, bucket: storage.Bucket):
        """Configure bucket lifecycle rules."""
        lifecycle_rules = [
            {
                "action": {"type": "Delete"},
                "condition": {
                    "age": self.auto_delete_temp_days,
                    "matchesPrefix": [f"{self.temp_folder}/"]
                }
            },
            {
                "action": {"type": "SetStorageClass", "storageClass": self.archive_storage_class},
                "condition": {
                    "age": self.auto_archive_days,
                    "matchesPrefix": [f"{self.video_folder}/"]
                }
            }
        ]
        
        bucket.lifecycle_rules = lifecycle_rules
        bucket.patch()
        logger.info("Bucket lifecycle rules configured")
    
    def get_file_path(self, user_id: int, video_id: int, file_type: str, filename: str) -> str:
        """Generate standardized file path."""
        folder_map = {
            "video": self.video_folder,
            "thumbnail": self.thumbnail_folder,
            "processed": self.processed_folder,
            "temp": self.temp_folder
        }
        
        folder = folder_map.get(file_type, self.video_folder)
        return f"{folder}/user_{user_id}/video_{video_id}/{filename}"
    
    def get_public_url(self, blob_name: str) -> str:
        """Get public URL for a file."""
        if self.cdn_enabled and self.cdn_base_url:
            return f"{self.cdn_base_url}/{blob_name}"
        else:
            return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
    
    def is_valid_video_type(self, content_type: str) -> bool:
        """Check if content type is allowed."""
        return content_type.lower() in self.allowed_video_types


# Global configuration instance
storage_config = StorageConfig()