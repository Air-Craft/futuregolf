"""
User profile management endpoints for FutureGolf API.
Handles user profile updates, statistics, and account management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.user import User
from app.models.video import Video
from app.models.video_analysis import VideoAnalysis
from app.api.schemas import (
    UserResponse, UserUpdate, ProfileUpdateRequest, ProfilePictureUploadResponse,
    UserProfileResponse, UserStatistics, BaseResponse, EmailValidationRequest,
    EmailValidationResponse
)
from app.services.auth_utils import auth_utils
from app.services.email_service import email_service
from app.middleware.auth_middleware import get_current_user
from datetime import datetime, timedelta
import logging
from app.config.api import API_VERSION_PREFIX

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{API_VERSION_PREFIX}/user", tags=["user-profile"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile information."""
    try:
        # Get user statistics
        video_count = db.query(Video).filter(Video.user_id == current_user.id).count()
        analysis_count = db.query(VideoAnalysis).filter(VideoAnalysis.user_id == current_user.id).count()
        
        # Get videos and analyses from this month
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        videos_this_month = db.query(Video).filter(
            Video.user_id == current_user.id,
            Video.created_at >= current_month_start
        ).count()
        
        analyses_this_month = db.query(VideoAnalysis).filter(
            VideoAnalysis.user_id == current_user.id,
            VideoAnalysis.created_at >= current_month_start
        ).count()
        
        # Get last video upload and analysis
        last_video = db.query(Video).filter(
            Video.user_id == current_user.id
        ).order_by(Video.created_at.desc()).first()
        
        last_analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.user_id == current_user.id
        ).order_by(VideoAnalysis.created_at.desc()).first()
        
        # Calculate account age
        account_age_days = (datetime.utcnow() - current_user.created_at).days
        
        statistics = UserStatistics(
            total_videos=video_count,
            total_analyses=analysis_count,
            videos_this_month=videos_this_month,
            analyses_this_month=analyses_this_month,
            minutes_analyzed_this_month=current_user.monthly_video_minutes_used,
            subscription_tier=current_user.subscription_tier,
            trial_analyses_remaining=current_user.trial_analysis_limit - current_user.trial_analyses_used if current_user.subscription_tier.value == "trial" else None,
            monthly_minutes_remaining=current_user.monthly_video_minutes_limit - current_user.monthly_video_minutes_used if current_user.subscription_tier.value == "pro" else None,
            account_age_days=account_age_days,
            last_video_upload=last_video.created_at if last_video else None,
            last_analysis=last_analysis.created_at if last_analysis else None
        )
        
        # Get user permissions
        permissions = {
            "can_upload_video": current_user.can_analyze_video(),
            "can_analyze_video": current_user.can_analyze_video(),
            "max_video_length": 300 if current_user.subscription_tier.value != "pro" else 1800,
            "can_access_premium_features": current_user.subscription_tier.value == "pro",
            "can_export_data": current_user.subscription_tier.value == "pro",
            "can_share_videos": True,
            "subscription_tier": current_user.subscription_tier.value,
            "trial_analyses_remaining": current_user.trial_analysis_limit - current_user.trial_analyses_used if current_user.subscription_tier.value == "trial" else None,
            "monthly_minutes_remaining": current_user.monthly_video_minutes_limit - current_user.monthly_video_minutes_used if current_user.subscription_tier.value == "pro" else None
        }
        
        return UserProfileResponse(
            user=UserResponse.from_orm(current_user),
            permissions=permissions,
            statistics=statistics.dict()
        )
        
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_update: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information."""
    try:
        # Update profile fields
        if profile_update.first_name is not None:
            current_user.first_name = profile_update.first_name
        
        if profile_update.last_name is not None:
            current_user.last_name = profile_update.last_name
        
        if profile_update.profile_picture_url is not None:
            current_user.profile_picture_url = profile_update.profile_picture_url
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Profile updated for user {current_user.email}")
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/upload-profile-picture", response_model=ProfilePictureUploadResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture (placeholder - implement with actual storage)."""
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        
        # In a real implementation, you would:
        # 1. Upload to your storage service (e.g., Google Cloud Storage)
        # 2. Generate a public URL
        # 3. Update the user's profile_picture_url
        
        # For now, we'll just create a placeholder URL
        profile_picture_url = f"https://example.com/profile-pictures/{current_user.id}/{file.filename}"
        
        # Update user's profile picture URL
        current_user.profile_picture_url = profile_picture_url
        db.commit()
        
        logger.info(f"Profile picture uploaded for user {current_user.email}")
        
        return ProfilePictureUploadResponse(
            profile_picture_url=profile_picture_url,
            message="Profile picture updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload profile picture error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )


@router.get("/statistics", response_model=UserStatistics)
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics."""
    try:
        # Get user statistics
        video_count = db.query(Video).filter(Video.user_id == current_user.id).count()
        analysis_count = db.query(VideoAnalysis).filter(VideoAnalysis.user_id == current_user.id).count()
        
        # Get videos and analyses from this month
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        videos_this_month = db.query(Video).filter(
            Video.user_id == current_user.id,
            Video.created_at >= current_month_start
        ).count()
        
        analyses_this_month = db.query(VideoAnalysis).filter(
            VideoAnalysis.user_id == current_user.id,
            VideoAnalysis.created_at >= current_month_start
        ).count()
        
        # Get last video upload and analysis
        last_video = db.query(Video).filter(
            Video.user_id == current_user.id
        ).order_by(Video.created_at.desc()).first()
        
        last_analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.user_id == current_user.id
        ).order_by(VideoAnalysis.created_at.desc()).first()
        
        # Calculate account age
        account_age_days = (datetime.utcnow() - current_user.created_at).days
        
        return UserStatistics(
            total_videos=video_count,
            total_analyses=analysis_count,
            videos_this_month=videos_this_month,
            analyses_this_month=analyses_this_month,
            minutes_analyzed_this_month=current_user.monthly_video_minutes_used,
            subscription_tier=current_user.subscription_tier,
            trial_analyses_remaining=current_user.trial_analysis_limit - current_user.trial_analyses_used if current_user.subscription_tier.value == "trial" else None,
            monthly_minutes_remaining=current_user.monthly_video_minutes_limit - current_user.monthly_video_minutes_used if current_user.subscription_tier.value == "pro" else None,
            account_age_days=account_age_days,
            last_video_upload=last_video.created_at if last_video else None,
            last_analysis=last_analysis.created_at if last_analysis else None
        )
        
    except Exception as e:
        logger.error(f"Get user statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )


@router.post("/validate-email", response_model=EmailValidationResponse)
async def validate_email_availability(
    email_data: EmailValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate email availability for profile update."""
    try:
        # Check if email is the same as current user's email
        if email_data.email == current_user.email:
            return EmailValidationResponse(
                is_valid=True,
                is_available=True,
                message="Email is valid and available"
            )
        
        # Check if email is already in use by another user
        existing_user = db.query(User).filter(
            User.email == email_data.email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            return EmailValidationResponse(
                is_valid=True,
                is_available=False,
                message="Email is already in use by another account"
            )
        
        return EmailValidationResponse(
            is_valid=True,
            is_available=True,
            message="Email is valid and available"
        )
        
    except Exception as e:
        logger.error(f"Email validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email validation failed"
        )


@router.put("/email", response_model=BaseResponse)
async def update_user_email(
    email_data: EmailValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user email address (requires re-verification)."""
    try:
        # Check if email is different from current email
        if email_data.email == current_user.email:
            return BaseResponse(
                success=True,
                message="Email address is already set to this value"
            )
        
        # Check if email is already in use
        existing_user = db.query(User).filter(
            User.email == email_data.email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already in use"
            )
        
        # Generate new verification token
        verification_token = auth_utils.generate_verification_token()
        verification_expires = auth_utils.create_verification_token_expiry()
        
        # Update user email and mark as unverified
        current_user.email = email_data.email
        current_user.is_verified = False
        current_user.verification_token = verification_token
        current_user.verification_token_expires = verification_expires
        
        db.commit()
        
        # Send verification email to new address
        email_sent = email_service.send_verification_email(
            email_data.email,
            current_user.first_name,
            verification_token
        )
        
        if not email_sent:
            logger.warning(f"Failed to send verification email to {email_data.email}")
        
        logger.info(f"Email updated for user {current_user.id} to {email_data.email}")
        
        return BaseResponse(
            success=True,
            message="Email address updated. Please check your new email for verification."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update email error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email address"
        )


@router.delete("/account", response_model=BaseResponse)
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account (soft delete)."""
    try:
        # Mark user as inactive instead of hard delete
        current_user.is_active = False
        current_user.email = f"deleted_{current_user.id}_{current_user.email}"
        
        db.commit()
        
        logger.info(f"Account deleted for user {current_user.id}")
        
        return BaseResponse(
            success=True,
            message="Account has been deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Delete account error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.get("/linked-accounts", response_model=dict)
async def get_linked_accounts(
    current_user: User = Depends(get_current_user)
):
    """Get list of linked OAuth accounts."""
    try:
        linked_accounts = {
            "google": {
                "linked": bool(current_user.google_id),
                "id": current_user.google_id
            },
            "microsoft": {
                "linked": bool(current_user.microsoft_id),
                "id": current_user.microsoft_id
            },
            "linkedin": {
                "linked": bool(current_user.linkedin_id),
                "id": current_user.linkedin_id
            }
        }
        
        return {
            "success": True,
            "linked_accounts": linked_accounts,
            "has_password": bool(current_user.hashed_password)
        }
        
    except Exception as e:
        logger.error(f"Get linked accounts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get linked accounts"
        )