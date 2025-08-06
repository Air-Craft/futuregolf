"""
Pydantic schemas for FutureGolf API request/response validation.
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SubscriptionTierEnum(str, Enum):
    """Subscription tier enum."""
    TRIAL = "trial"
    PRO = "pro"
    FREE = "free"


# Base schemas
class BaseResponse(BaseModel):
    """Base response schema."""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseResponse):
    """Error response schema."""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


# User schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    is_verified: bool
    subscription_tier: SubscriptionTierEnum
    trial_analyses_used: int
    trial_analysis_limit: int
    monthly_video_minutes_used: int
    monthly_video_minutes_limit: int
    profile_picture_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User update schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserProfileResponse(BaseModel):
    """User profile response schema."""
    user: UserResponse
    permissions: Dict[str, Any]
    statistics: Dict[str, Any]


# Authentication schemas
class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseResponse):
    """Login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class TokenResponse(BaseResponse):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('New password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('New password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('New password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('New password must contain at least one special character')
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('New password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('New password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('New password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('New password must contain at least one special character')
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification request schema."""
    email: EmailStr


# OAuth schemas
class OAuthProvider(str, Enum):
    """OAuth provider enum."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    LINKEDIN = "linkedin"


class OAuthAuthUrlResponse(BaseResponse):
    """OAuth authorization URL response schema."""
    auth_url: str
    state: str
    provider: OAuthProvider


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request schema."""
    code: str
    state: str
    provider: OAuthProvider


class OAuthUserInfo(BaseModel):
    """OAuth user info schema."""
    provider: OAuthProvider
    provider_id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_verified: bool = False


# Session schemas
class SessionInfo(BaseModel):
    """Session info schema."""
    session_id: str
    user_id: int
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    is_active: bool


class SessionListResponse(BaseResponse):
    """Session list response schema."""
    sessions: List[SessionInfo]
    total_count: int


class LogoutRequest(BaseModel):
    """Logout request schema."""
    all_devices: bool = False


class LogoutResponse(BaseResponse):
    """Logout response schema."""
    sessions_terminated: int


# Registration schemas
class RegistrationResponse(BaseResponse):
    """Registration response schema."""
    user_id: int
    email: EmailStr
    verification_sent: bool
    message: str = "Registration successful. Please check your email for verification."


class VerificationResponse(BaseResponse):
    """Email verification response schema."""
    user_id: int
    email: EmailStr
    is_verified: bool
    message: str = "Email verified successfully"


# Profile schemas
class ProfileUpdateRequest(BaseModel):
    """Profile update request schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture_url: Optional[str] = None


class ProfilePictureUploadResponse(BaseResponse):
    """Profile picture upload response schema."""
    profile_picture_url: str
    message: str = "Profile picture updated successfully"


# Statistics schemas
class UserStatistics(BaseModel):
    """User statistics schema."""
    total_videos: int
    total_analyses: int
    videos_this_month: int
    analyses_this_month: int
    minutes_analyzed_this_month: int
    subscription_tier: SubscriptionTierEnum
    trial_analyses_remaining: Optional[int] = None
    monthly_minutes_remaining: Optional[int] = None
    account_age_days: int
    last_video_upload: Optional[datetime] = None
    last_analysis: Optional[datetime] = None


# Validation schemas
class PasswordValidationRequest(BaseModel):
    """Password validation request schema."""
    password: str


class PasswordValidationResponse(BaseResponse):
    """Password validation response schema."""
    is_valid: bool
    requirements: Dict[str, bool]
    message: str


class EmailValidationRequest(BaseModel):
    """Email validation request schema."""
    email: EmailStr


class EmailValidationResponse(BaseResponse):
    """Email validation response schema."""
    is_valid: bool
    is_available: bool
    message: str


# Configuration schemas
class AuthConfig(BaseModel):
    """Authentication configuration schema."""
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    email_verification_expire_hours: int = 24
    password_reset_expire_hours: int = 1
    max_failed_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30
    oauth_providers: List[OAuthProvider] = []


class AuthConfigResponse(BaseResponse):
    """Authentication configuration response schema."""
    config: AuthConfig


# Video Analysis schemas
class VideoAnalysisResponse(BaseResponse):
    """Video analysis response schema."""
    analysis_id: int
    video_id: int
    status: str
    message: str


class VideoAnalysisStatusResponse(BaseResponse):
    """Video analysis status response schema."""
    analysis_id: int
    status: str
    created_at: str
    processing_started_at: Optional[str] = None
    processing_completed_at: Optional[str] = None
    error_message: Optional[str] = None
    is_completed: bool
    is_failed: bool
    is_processing: bool


class CoachingPoint(BaseModel):
    """Coaching point schema."""
    timestamp: float
    category: str
    issue: str
    suggestion: str
    priority: str


class SwingPhase(BaseModel):
    """Swing phase schema."""
    start: float
    end: float


class SwingPhases(BaseModel):
    """Swing phases schema."""
    setup: SwingPhase
    backswing: SwingPhase
    downswing: SwingPhase
    impact: SwingPhase
    follow_through: SwingPhase


class PoseAnalysis(BaseModel):
    """Pose analysis schema."""
    shoulder_angle: str
    hip_rotation: str
    spine_angle: str
    head_position: str


class AnalysisResults(BaseModel):
    """Analysis results schema."""
    overall_score: int
    swing_phases: SwingPhases
    coaching_points: List[CoachingPoint]
    pose_analysis: PoseAnalysis
    summary: str
    confidence: float
    duration: float


class VideoAnalysisResultsResponse(BaseResponse):
    """Video analysis results response schema."""
    analysis_id: int
    status: str
    ai_analysis: AnalysisResults
    video_duration: float
    analysis_confidence: float
    created_at: str
    completed_at: str