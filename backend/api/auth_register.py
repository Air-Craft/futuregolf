"""
User registration endpoints for FutureGolf API.
Handles user registration, email verification, and related functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.config import get_db
from models.user import User
from api.schemas import (
    UserCreate, RegistrationResponse, EmailVerificationRequest, 
    VerificationResponse, ResendVerificationRequest, BaseResponse
)
from services.auth_utils import auth_utils
from services.email_service import email_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", response_model=RegistrationResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user with email verification."""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered"
            )
        
        # Validate password strength
        password_validation = auth_utils.validate_password_strength(user_data.password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_validation["message"]
            )
        
        # Hash password
        hashed_password = auth_utils.hash_password(user_data.password)
        
        # Generate verification token
        verification_token = auth_utils.generate_verification_token()
        verification_expires = auth_utils.create_verification_token_expiry()
        
        # Create user
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_verified=False,
            verification_token=verification_token,
            verification_token_expires=verification_expires
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send verification email
        verification_sent = email_service.send_verification_email(
            user.email,
            user.first_name,
            verification_token
        )
        
        if not verification_sent:
            logger.warning(f"Failed to send verification email to {user.email}")
        
        return RegistrationResponse(
            user_id=user.id,
            email=user.email,
            verification_sent=verification_sent,
            message="Registration successful. Please check your email for verification."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/verify-email", response_model=VerificationResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify user email with verification token."""
    try:
        # Find user by verification token
        user = db.query(User).filter(
            User.verification_token == verification_data.token,
            User.is_verified == False
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Check if token has expired
        if auth_utils.is_token_expired(user.verification_token_expires):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired"
            )
        
        # Mark user as verified
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        
        db.commit()
        db.refresh(user)
        
        # Send welcome email
        welcome_sent = email_service.send_welcome_email(
            user.email,
            user.first_name
        )
        
        if not welcome_sent:
            logger.warning(f"Failed to send welcome email to {user.email}")
        
        return VerificationResponse(
            user_id=user.id,
            email=user.email,
            is_verified=True,
            message="Email verified successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/resend-verification", response_model=BaseResponse)
async def resend_verification_email(
    resend_data: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """Resend verification email to user."""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == resend_data.email).first()
        
        if not user:
            # Don't reveal if email exists for security
            return BaseResponse(
                success=True,
                message="If the email address exists, a verification email has been sent."
            )
        
        # Check if user is already verified
        if user.is_verified:
            return BaseResponse(
                success=True,
                message="Email address is already verified."
            )
        
        # Generate new verification token
        verification_token = auth_utils.generate_verification_token()
        verification_expires = auth_utils.create_verification_token_expiry()
        
        # Update user with new token
        user.verification_token = verification_token
        user.verification_token_expires = verification_expires
        
        db.commit()
        
        # Send verification email
        verification_sent = email_service.send_verification_email(
            user.email,
            user.first_name,
            verification_token
        )
        
        if not verification_sent:
            logger.warning(f"Failed to resend verification email to {user.email}")
        
        return BaseResponse(
            success=True,
            message="If the email address exists, a verification email has been sent."
        )
        
    except Exception as e:
        logger.error(f"Resend verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )


@router.get("/verify-token/{token}", response_model=BaseResponse)
async def verify_token_validity(
    token: str,
    db: Session = Depends(get_db)
):
    """Check if verification token is valid."""
    try:
        # Find user by verification token
        user = db.query(User).filter(
            User.verification_token == token,
            User.is_verified == False
        ).first()
        
        if not user:
            return BaseResponse(
                success=False,
                message="Invalid verification token"
            )
        
        # Check if token has expired
        if auth_utils.is_token_expired(user.verification_token_expires):
            return BaseResponse(
                success=False,
                message="Verification token has expired"
            )
        
        return BaseResponse(
            success=True,
            message="Verification token is valid"
        )
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation failed"
        )