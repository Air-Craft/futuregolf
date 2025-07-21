"""
Password management endpoints for FutureGolf API.
Handles password reset, change, and validation functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.config import get_db
from models.user import User
from api.schemas import (
    PasswordResetRequest, PasswordResetConfirm, PasswordChangeRequest,
    PasswordValidationRequest, PasswordValidationResponse, BaseResponse
)
from services.auth_utils import auth_utils
from services.email_service import email_service
from middleware.auth_middleware import get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["password"])


@router.post("/request-password-reset", response_model=BaseResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset email."""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == reset_request.email).first()
        
        # Don't reveal if email exists for security
        if not user:
            return BaseResponse(
                success=True,
                message="If the email address exists, a password reset link has been sent."
            )
        
        # Check if user is active
        if not user.is_active:
            return BaseResponse(
                success=True,
                message="If the email address exists, a password reset link has been sent."
            )
        
        # Generate reset token
        reset_token = auth_utils.generate_reset_token()
        reset_token_expires = auth_utils.create_reset_token_expiry()
        
        # Update user with reset token
        user.reset_token = reset_token
        user.reset_token_expires = reset_token_expires
        
        db.commit()
        
        # Send password reset email
        email_sent = email_service.send_password_reset_email(
            user.email,
            user.first_name,
            reset_token
        )
        
        if not email_sent:
            logger.warning(f"Failed to send password reset email to {user.email}")
        
        logger.info(f"Password reset requested for user {user.email}")
        
        return BaseResponse(
            success=True,
            message="If the email address exists, a password reset link has been sent."
        )
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


@router.post("/reset-password", response_model=BaseResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using reset token."""
    try:
        # Find user by reset token
        user = db.query(User).filter(User.reset_token == reset_data.token).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Check if token has expired
        if auth_utils.is_token_expired(user.reset_token_expires):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Validate new password
        password_validation = auth_utils.validate_password_strength(reset_data.new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_validation["message"]
            )
        
        # Hash new password
        hashed_password = auth_utils.hash_password(reset_data.new_password)
        
        # Update user password and clear reset token
        user.hashed_password = hashed_password
        user.reset_token = None
        user.reset_token_expires = None
        
        db.commit()
        
        # Send password changed notification
        email_sent = email_service.send_password_changed_notification(
            user.email,
            user.first_name
        )
        
        if not email_sent:
            logger.warning(f"Failed to send password changed notification to {user.email}")
        
        logger.info(f"Password reset completed for user {user.email}")
        
        return BaseResponse(
            success=True,
            message="Password has been reset successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password (requires current password)."""
    try:
        # Check if user has a current password (OAuth users might not)
        if not current_user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No current password set. Please use password reset instead."
            )
        
        # Verify current password
        if not auth_utils.verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Check if new password is different from current
        if auth_utils.verify_password(password_data.new_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )
        
        # Validate new password
        password_validation = auth_utils.validate_password_strength(password_data.new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_validation["message"]
            )
        
        # Hash new password
        hashed_password = auth_utils.hash_password(password_data.new_password)
        
        # Update user password
        current_user.hashed_password = hashed_password
        
        db.commit()
        
        # Send password changed notification
        email_sent = email_service.send_password_changed_notification(
            current_user.email,
            current_user.first_name
        )
        
        if not email_sent:
            logger.warning(f"Failed to send password changed notification to {current_user.email}")
        
        logger.info(f"Password changed for user {current_user.email}")
        
        return BaseResponse(
            success=True,
            message="Password has been changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/validate-reset-token/{token}", response_model=BaseResponse)
async def validate_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """Validate password reset token."""
    try:
        # Find user by reset token
        user = db.query(User).filter(User.reset_token == token).first()
        
        if not user:
            return BaseResponse(
                success=False,
                message="Invalid reset token"
            )
        
        # Check if token has expired
        if auth_utils.is_token_expired(user.reset_token_expires):
            return BaseResponse(
                success=False,
                message="Reset token has expired"
            )
        
        return BaseResponse(
            success=True,
            message="Reset token is valid"
        )
        
    except Exception as e:
        logger.error(f"Reset token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation failed"
        )


@router.post("/validate-password", response_model=PasswordValidationResponse)
async def validate_password(
    password_data: PasswordValidationRequest
):
    """Validate password strength requirements."""
    try:
        validation_result = auth_utils.validate_password_strength(password_data.password)
        
        return PasswordValidationResponse(
            is_valid=validation_result["is_valid"],
            requirements=validation_result["requirements"],
            message=validation_result["message"]
        )
        
    except Exception as e:
        logger.error(f"Password validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password validation failed"
        )


@router.post("/set-password", response_model=BaseResponse)
async def set_password(
    password_data: PasswordValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set password for OAuth users who don't have one."""
    try:
        # Check if user already has a password
        if current_user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a password. Use change-password instead."
            )
        
        # Validate password
        password_validation = auth_utils.validate_password_strength(password_data.password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_validation["message"]
            )
        
        # Hash password
        hashed_password = auth_utils.hash_password(password_data.password)
        
        # Set user password
        current_user.hashed_password = hashed_password
        
        db.commit()
        
        # Send password changed notification
        email_sent = email_service.send_password_changed_notification(
            current_user.email,
            current_user.first_name
        )
        
        if not email_sent:
            logger.warning(f"Failed to send password set notification to {current_user.email}")
        
        logger.info(f"Password set for user {current_user.email}")
        
        return BaseResponse(
            success=True,
            message="Password has been set successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set password"
        )