"""
Video model for storing user video uploads and metadata.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.config import Base
import enum


class VideoStatus(enum.Enum):
    """Enum for video upload and processing status."""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class Video(Base):
    """Model for storing user video uploads and metadata."""
    
    __tablename__ = "videos"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Video metadata
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # File information
    original_filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    duration = Column(Float, nullable=True)  # Duration in seconds
    frame_rate = Column(Float, nullable=True)  # Frames per second
    resolution = Column(String(50), nullable=True)  # e.g., "1920x1080"
    
    # Storage information
    video_url = Column(Text, nullable=False)  # URL to original video
    video_blob_name = Column(Text, nullable=True)  # GCS blob name for video
    thumbnail_url = Column(Text, nullable=True)  # URL to video thumbnail
    thumbnail_blob_name = Column(Text, nullable=True)  # GCS blob name for thumbnail
    processed_video_url = Column(Text, nullable=True)  # URL to processed video
    processed_blob_name = Column(Text, nullable=True)  # GCS blob name for processed video
    
    # Video processing status
    status = Column(Enum(VideoStatus), default=VideoStatus.UPLOADING)
    upload_progress = Column(Float, default=0.0)  # Upload progress 0-100
    
    # Technical metadata stored as JSONB
    technical_metadata = Column(JSONB, nullable=True)  # Video codec, bitrate, etc.
    
    # Recording context
    recording_location = Column(String(255), nullable=True)  # Where video was recorded
    recording_conditions = Column(JSONB, nullable=True)  # Weather, lighting, etc.
    
    # User preferences
    is_saved = Column(Boolean, default=True)  # Whether user saved this video
    is_exported = Column(Boolean, default=False)  # Whether user exported to photos
    is_favorite = Column(Boolean, default=False)  # Whether user marked as favorite
    
    # Privacy settings
    is_private = Column(Boolean, default=True)  # Whether video is private
    
    # Quality assessment
    quality_score = Column(Float, nullable=True)  # Video quality score 0-1
    position_quality = Column(JSONB, nullable=True)  # Quality of golfer positioning
    
    # Processing information
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Usage tracking
    view_count = Column(Integer, default=0)  # How many times user viewed
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    user = relationship("User", back_populates="videos")
    analysis = relationship("VideoAnalysis", back_populates="video", uselist=False)
    
    def __repr__(self):
        return f"<Video(id={self.id}, user_id={self.user_id}, title='{self.title}', status='{self.status.value}')>"
    
    @property
    def is_ready(self):
        """Check if video is ready for viewing."""
        return self.status == VideoStatus.READY
    
    @property
    def is_processing(self):
        """Check if video is currently processing."""
        return self.status in [VideoStatus.UPLOADING, VideoStatus.PROCESSING]
    
    @property
    def is_failed(self):
        """Check if video processing failed."""
        return self.status == VideoStatus.FAILED
    
    @property
    def is_deleted(self):
        """Check if video is soft-deleted."""
        return self.status == VideoStatus.DELETED or self.deleted_at is not None
    
    @property
    def has_analysis(self):
        """Check if video has been analyzed."""
        return self.analysis is not None
    
    @property
    def duration_minutes(self):
        """Get video duration in minutes."""
        if self.duration:
            return self.duration / 60
        return 0
    
    @property
    def file_size_mb(self):
        """Get file size in MB."""
        if self.file_size:
            return self.file_size / (1024 * 1024)
        return 0
    
    def mark_as_uploaded(self):
        """Mark video as successfully uploaded."""
        self.status = VideoStatus.UPLOADED
        self.upload_progress = 100.0
    
    def mark_as_processing(self):
        """Mark video as processing."""
        self.status = VideoStatus.PROCESSING
        self.processing_started_at = func.now()
    
    def mark_as_ready(self):
        """Mark video as ready for viewing."""
        self.status = VideoStatus.READY
        self.processing_completed_at = func.now()
    
    def mark_as_failed(self, error_message):
        """Mark video processing as failed."""
        self.status = VideoStatus.FAILED
        self.error_message = error_message
        self.processing_completed_at = func.now()
    
    def soft_delete(self):
        """Soft delete the video."""
        self.status = VideoStatus.DELETED
        self.deleted_at = func.now()
        self.is_saved = False
    
    def increment_view_count(self):
        """Increment view count and update last viewed timestamp."""
        self.view_count += 1
        self.last_viewed_at = func.now()
    
    def toggle_favorite(self):
        """Toggle favorite status."""
        self.is_favorite = not self.is_favorite
    
    def export_to_photos(self):
        """Mark video as exported to photos."""
        self.is_exported = True