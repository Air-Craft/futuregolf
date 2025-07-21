"""
User model for FutureGolf application.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.config import Base
import enum


class SubscriptionTier(enum.Enum):
    """Enum for subscription tiers."""
    TRIAL = "trial"
    PRO = "pro"
    FREE = "free"


class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # OAuth fields
    google_id = Column(String(255), unique=True, nullable=True)
    microsoft_id = Column(String(255), unique=True, nullable=True)
    linkedin_id = Column(String(255), unique=True, nullable=True)
    
    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    profile_picture_url = Column(Text, nullable=True)
    
    # Subscription fields
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.TRIAL)
    trial_analyses_used = Column(Integer, default=0)
    trial_analysis_limit = Column(Integer, default=3)
    monthly_video_minutes_used = Column(Integer, default=0)
    monthly_video_minutes_limit = Column(Integer, default=60)  # 1 hour for pro users
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset fields
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Email verification fields
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    video_analyses = relationship("VideoAnalysis", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', tier='{self.subscription_tier.value}')>"
    
    @property
    def full_name(self):
        """Return full name if both first and last names exist."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    def can_analyze_video(self):
        """Check if user can analyze more videos based on their subscription."""
        if self.subscription_tier == SubscriptionTier.TRIAL:
            return self.trial_analyses_used < self.trial_analysis_limit
        elif self.subscription_tier == SubscriptionTier.PRO:
            return self.monthly_video_minutes_used < self.monthly_video_minutes_limit
        return False
    
    def increment_trial_usage(self):
        """Increment trial analysis usage."""
        if self.subscription_tier == SubscriptionTier.TRIAL:
            self.trial_analyses_used += 1
    
    def add_video_minutes(self, minutes):
        """Add video minutes to monthly usage."""
        if self.subscription_tier == SubscriptionTier.PRO:
            self.monthly_video_minutes_used += minutes
    
    def reset_monthly_usage(self):
        """Reset monthly usage counters."""
        self.monthly_video_minutes_used = 0