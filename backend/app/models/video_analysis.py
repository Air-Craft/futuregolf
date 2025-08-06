"""
VideoAnalysis model for storing AI analysis results.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.config import Base
import enum


class AnalysisStatus(enum.Enum):
    """Enum for analysis status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoAnalysis(Base):
    """Model for storing video analysis results and metadata."""
    
    __tablename__ = "video_analyses"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    
    # Analysis metadata
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    analysis_duration = Column(Float, nullable=True)  # Duration in seconds
    video_duration = Column(Float, nullable=True)  # Original video duration
    
    # Processing information
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Analysis results stored as JSONB
    pose_data = Column(JSONB, nullable=True)  # MediaPipe pose detection results
    swing_metrics = Column(JSONB, nullable=True)  # Calculated swing metrics
    ai_analysis = Column(JSONB, nullable=True)  # AI analysis from Gemini
    coaching_script = Column(JSONB, nullable=True)  # Generated coaching script with timestamps
    
    # Specific analysis fields
    shoulder_angle_data = Column(JSONB, nullable=True)  # Shoulder angle analysis
    head_alignment_data = Column(JSONB, nullable=True)  # Head alignment analysis
    body_position_data = Column(JSONB, nullable=True)  # Overall body position data
    
    # Visual feedback data
    angle_lines_data = Column(JSONB, nullable=True)  # Data for overlay lines
    color_indicators = Column(JSONB, nullable=True)  # Green/red color indicators
    key_moments = Column(JSONB, nullable=True)  # Key moments for summary report
    
    # Generated content URLs
    processed_video_url = Column(Text, nullable=True)  # URL to processed video with overlays
    summary_report_data = Column(JSONB, nullable=True)  # Data for scrollable summary report
    
    # Audio content
    coaching_audio_url = Column(Text, nullable=True)  # URL to generated coaching audio
    tts_timestamps = Column(JSONB, nullable=True)  # TTS playback timestamps
    
    # Practice recommendations
    practice_tips = Column(JSONB, nullable=True)  # Practice tips based on analysis
    improvement_areas = Column(JSONB, nullable=True)  # Areas for improvement
    
    # Quality metrics
    analysis_confidence = Column(Float, nullable=True)  # Confidence score 0-1
    video_quality_score = Column(Float, nullable=True)  # Video quality assessment
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="video_analyses")
    video = relationship("Video", back_populates="analysis")
    
    def __repr__(self):
        return f"<VideoAnalysis(id={self.id}, user_id={self.user_id}, status='{self.status.value}')>"
    
    @property
    def is_completed(self):
        """Check if analysis is completed."""
        return self.status == AnalysisStatus.COMPLETED
    
    @property
    def is_failed(self):
        """Check if analysis failed."""
        return self.status == AnalysisStatus.FAILED
    
    @property
    def is_processing(self):
        """Check if analysis is currently processing."""
        return self.status in [AnalysisStatus.PENDING, AnalysisStatus.PROCESSING]
    
    def get_coaching_script_for_timestamp(self, timestamp):
        """Get coaching script text for a specific timestamp."""
        if not self.coaching_script:
            return None
        
        # Find the appropriate coaching text for the given timestamp
        for script_item in self.coaching_script.get("scripts", []):
            start_time = script_item.get("start_time", 0)
            end_time = script_item.get("end_time", float("inf"))
            
            if start_time <= timestamp <= end_time:
                return script_item.get("text", "")
        
        return None
    
    def get_key_moments_summary(self):
        """Get a summary of key moments from the analysis."""
        if not self.key_moments:
            return []
        
        return self.key_moments.get("moments", [])
    
    def get_improvement_summary(self):
        """Get a summary of improvement areas."""
        if not self.improvement_areas:
            return []
        
        return self.improvement_areas.get("areas", [])
    
    def mark_as_completed(self):
        """Mark analysis as completed."""
        self.status = AnalysisStatus.COMPLETED
        self.processing_completed_at = func.now()
    
    def mark_as_failed(self, error_message):
        """Mark analysis as failed with error message."""
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        self.processing_completed_at = func.now()
    
    def start_processing(self):
        """Mark analysis as started processing."""
        self.status = AnalysisStatus.PROCESSING
        self.processing_started_at = func.now()