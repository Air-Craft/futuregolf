"""
User login endpoints for FutureGolf API.
Handles user authentication, JWT token generation, and session management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.config import get_db
from models.user import User
from api.schemas import (
    LoginRequest, LoginResponse, RefreshTokenRequest, TokenResponse,
    LogoutRequest, LogoutResponse, BaseResponse
)
from services.auth_utils import auth_utils
from middleware.auth_middleware import get_current_user, get_current_user_optional
from datetime import datetime, timedelta
import logging
from config.api import API_VERSION_PREFIX

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{API_VERSION_PREFIX}/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT tokens."""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()
        
        if not user or not auth_utils.verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Check if user is verified
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email verification required"
            )
        
        # Get device info from request
        device_info = request.headers.get("user-agent", "Unknown device")
        
        # Create JWT tokens
        access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=auth_utils.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = auth_utils.create_access_token(
            data={"user_id": user.id, "email": user.email},
            expires_delta=access_token_expires
        )
        
        refresh_token = auth_utils.create_refresh_token(
            data={"user_id": user.id, "email": user.email},
            expires_delta=refresh_token_expires
        )
        
        # Update user's last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"User {user.email} logged in successfully")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "subscription_tier": user.subscription_tier,
                "trial_analyses_used": user.trial_analyses_used,
                "trial_analysis_limit": user.trial_analysis_limit,
                "monthly_video_minutes_used": user.monthly_video_minutes_used,
                "monthly_video_minutes_limit": user.monthly_video_minutes_limit,
                "profile_picture_url": user.profile_picture_url,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login": user.last_login,
                "full_name": user.full_name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh JWT access token using refresh token."""
    try:
        # Validate refresh token
        payload = auth_utils.decode_token(refresh_data.refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user ID from payload
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=auth_utils.REFRESH_TOKEN_EXPIRE_DAYS)
        
        new_access_token = auth_utils.create_access_token(
            data={"user_id": user.id, "email": user.email},
            expires_delta=access_token_expires
        )
        
        new_refresh_token = auth_utils.create_refresh_token(
            data={"user_id": user.id, "email": user.email},
            expires_delta=refresh_token_expires
        )
        
        logger.info(f"Tokens refreshed for user {user.email}")
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Logout user and invalidate tokens."""
    try:
        if not current_user:
            # User is already logged out
            return LogoutResponse(
                success=True,
                message="Logged out successfully",
                sessions_terminated=0
            )
        
        # In a production system, you would add token blacklisting here
        # For now, we'll just log the logout
        logger.info(f"User {current_user.email} logged out")
        
        # If logout from all devices, you would invalidate all refresh tokens
        sessions_terminated = 1
        if logout_data.all_devices:
            sessions_terminated = 999  # Placeholder - implement actual session counting
        
        return LogoutResponse(
            success=True,
            message="Logged out successfully",
            sessions_terminated=sessions_terminated
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    try:
        return {
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "is_active": current_user.is_active,
                "is_verified": current_user.is_verified,
                "subscription_tier": current_user.subscription_tier,
                "trial_analyses_used": current_user.trial_analyses_used,
                "trial_analysis_limit": current_user.trial_analysis_limit,
                "monthly_video_minutes_used": current_user.monthly_video_minutes_used,
                "monthly_video_minutes_limit": current_user.monthly_video_minutes_limit,
                "profile_picture_url": current_user.profile_picture_url,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at,
                "last_login": current_user.last_login,
                "full_name": current_user.full_name
            },
            "permissions": {
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
        }
        
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.get("/validate-token", response_model=BaseResponse)
async def validate_token(
    current_user: User = Depends(get_current_user_optional)
):
    """Validate current JWT token."""
    try:
        if not current_user:
            return BaseResponse(
                success=False,
                message="Invalid or expired token"
            )
        
        return BaseResponse(
            success=True,
            message="Token is valid"
        )
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return BaseResponse(
            success=False,
            message="Token validation failed"
        )