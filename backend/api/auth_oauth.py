"""
OAuth authentication endpoints for FutureGolf API.
Handles Google, LinkedIn, and Microsoft OAuth authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database.config import get_db
from models.user import User
from api.schemas import (
    OAuthAuthUrlResponse, OAuthProvider, LoginResponse, BaseResponse
)
from services.oauth_service import oauth_service
from services.auth_utils import auth_utils
from services.email_service import email_service
from middleware.auth_middleware import get_current_user
from datetime import datetime, timedelta
import logging
from config.api import API_VERSION_PREFIX

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{API_VERSION_PREFIX}/auth/oauth", tags=["oauth"])

# Frontend URL for redirects
FRONTEND_URL = "http://localhost:3000"


@router.get("/providers", response_model=dict)
async def get_oauth_providers():
    """Get list of available OAuth providers."""
    try:
        providers = oauth_service.get_available_providers()
        return {
            "success": True,
            "providers": providers,
            "message": f"Found {len(providers)} available OAuth providers"
        }
    except Exception as e:
        logger.error(f"Get OAuth providers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get OAuth providers"
        )


@router.get("/{provider}/auth-url", response_model=OAuthAuthUrlResponse)
async def get_oauth_auth_url(provider: OAuthProvider):
    """Get OAuth authorization URL for specified provider."""
    try:
        # Check if provider is configured
        if not oauth_service.is_provider_configured(provider.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider.value}' is not configured"
            )
        
        # Get provider instance
        oauth_provider = oauth_service.get_provider(provider.value)
        if not oauth_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider.value}' is not available"
            )
        
        # Get authorization URL
        auth_url, state = oauth_provider.get_authorization_url()
        
        return OAuthAuthUrlResponse(
            auth_url=auth_url,
            state=state,
            provider=provider
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth auth URL error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OAuth authorization URL"
        )


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: OAuthProvider,
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from provider."""
    try:
        # Check if provider is configured
        if not oauth_service.is_provider_configured(provider.value):
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=provider_not_configured",
                status_code=302
            )
        
        # Get provider instance
        oauth_provider = oauth_service.get_provider(provider.value)
        if not oauth_provider:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=provider_not_available",
                status_code=302
            )
        
        # Validate state parameter
        if not oauth_provider.validate_state(state):
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=invalid_state",
                status_code=302
            )
        
        # Exchange code for access token
        token_data = await oauth_provider.exchange_code_for_token(code)
        if not token_data:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=token_exchange_failed",
                status_code=302
            )
        
        # Get user info from provider
        user_info = await oauth_provider.get_user_info(token_data["access_token"])
        if not user_info:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=user_info_failed",
                status_code=302
            )
        
        # Normalize user data
        normalized_user = oauth_service.normalize_user_data(provider.value, user_info)
        
        # Check if user exists
        user = db.query(User).filter(User.email == normalized_user["email"]).first()
        
        if user:
            # Update OAuth ID if not set
            if provider.value == "google" and not user.google_id:
                user.google_id = normalized_user["provider_id"]
            elif provider.value == "microsoft" and not user.microsoft_id:
                user.microsoft_id = normalized_user["provider_id"]
            elif provider.value == "linkedin" and not user.linkedin_id:
                user.linkedin_id = normalized_user["provider_id"]
            
            # Update profile picture if not set
            if not user.profile_picture_url and normalized_user["profile_picture_url"]:
                user.profile_picture_url = normalized_user["profile_picture_url"]
            
            # Mark as verified if OAuth provider confirms email
            if normalized_user["is_verified"]:
                user.is_verified = True
            
            # Update last login
            user.last_login = datetime.utcnow()
            
        else:
            # Create new user
            user = User(
                email=normalized_user["email"],
                first_name=normalized_user["first_name"],
                last_name=normalized_user["last_name"],
                profile_picture_url=normalized_user["profile_picture_url"],
                is_verified=normalized_user["is_verified"],
                google_id=normalized_user["provider_id"] if provider.value == "google" else None,
                microsoft_id=normalized_user["provider_id"] if provider.value == "microsoft" else None,
                linkedin_id=normalized_user["provider_id"] if provider.value == "linkedin" else None,
                last_login=datetime.utcnow()
            )
            
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
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
        
        # Send welcome email if new user
        if not user.created_at or user.created_at.date() == datetime.utcnow().date():
            welcome_sent = email_service.send_welcome_email(
                user.email,
                user.first_name
            )
            if not welcome_sent:
                logger.warning(f"Failed to send welcome email to {user.email}")
        
        logger.info(f"User {user.email} authenticated via {provider.value}")
        
        # Redirect to frontend with tokens
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=authentication_failed",
            status_code=302
        )


@router.post("/{provider}/login", response_model=LoginResponse)
async def oauth_login(
    provider: OAuthProvider,
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Alternative OAuth login endpoint that returns JSON instead of redirect."""
    try:
        # Check if provider is configured
        if not oauth_service.is_provider_configured(provider.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider.value}' is not configured"
            )
        
        # Get provider instance
        oauth_provider = oauth_service.get_provider(provider.value)
        if not oauth_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider.value}' is not available"
            )
        
        # Validate state parameter
        if not oauth_provider.validate_state(state):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # Exchange code for access token
        token_data = await oauth_provider.exchange_code_for_token(code)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        # Get user info from provider
        user_info = await oauth_provider.get_user_info(token_data["access_token"])
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information"
            )
        
        # Normalize user data
        normalized_user = oauth_service.normalize_user_data(provider.value, user_info)
        
        # Check if user exists
        user = db.query(User).filter(User.email == normalized_user["email"]).first()
        
        if user:
            # Update OAuth ID if not set
            if provider.value == "google" and not user.google_id:
                user.google_id = normalized_user["provider_id"]
            elif provider.value == "microsoft" and not user.microsoft_id:
                user.microsoft_id = normalized_user["provider_id"]
            elif provider.value == "linkedin" and not user.linkedin_id:
                user.linkedin_id = normalized_user["provider_id"]
            
            # Update profile picture if not set
            if not user.profile_picture_url and normalized_user["profile_picture_url"]:
                user.profile_picture_url = normalized_user["profile_picture_url"]
            
            # Mark as verified if OAuth provider confirms email
            if normalized_user["is_verified"]:
                user.is_verified = True
            
            # Update last login
            user.last_login = datetime.utcnow()
            
        else:
            # Create new user
            user = User(
                email=normalized_user["email"],
                first_name=normalized_user["first_name"],
                last_name=normalized_user["last_name"],
                profile_picture_url=normalized_user["profile_picture_url"],
                is_verified=normalized_user["is_verified"],
                google_id=normalized_user["provider_id"] if provider.value == "google" else None,
                microsoft_id=normalized_user["provider_id"] if provider.value == "microsoft" else None,
                linkedin_id=normalized_user["provider_id"] if provider.value == "linkedin" else None,
                last_login=datetime.utcnow()
            )
            
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
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
        
        # Send welcome email if new user
        if not user.created_at or user.created_at.date() == datetime.utcnow().date():
            welcome_sent = email_service.send_welcome_email(
                user.email,
                user.first_name
            )
            if not welcome_sent:
                logger.warning(f"Failed to send welcome email to {user.email}")
        
        logger.info(f"User {user.email} authenticated via {provider.value}")
        
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
        logger.error(f"OAuth login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


@router.post("/{provider}/unlink", response_model=BaseResponse)
async def unlink_oauth_provider(
    provider: OAuthProvider,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlink OAuth provider from user account."""
    try:
        # Check if user has a password (can't unlink all OAuth if no password)
        if not current_user.hashed_password:
            # Check if user has other OAuth providers linked
            other_providers = []
            if provider.value != "google" and current_user.google_id:
                other_providers.append("google")
            if provider.value != "microsoft" and current_user.microsoft_id:
                other_providers.append("microsoft")
            if provider.value != "linkedin" and current_user.linkedin_id:
                other_providers.append("linkedin")
            
            if not other_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot unlink the only authentication method. Please set a password first."
                )
        
        # Unlink the provider
        if provider.value == "google":
            if not current_user.google_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google account is not linked"
                )
            current_user.google_id = None
        elif provider.value == "microsoft":
            if not current_user.microsoft_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Microsoft account is not linked"
                )
            current_user.microsoft_id = None
        elif provider.value == "linkedin":
            if not current_user.linkedin_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="LinkedIn account is not linked"
                )
            current_user.linkedin_id = None
        
        db.commit()
        
        logger.info(f"User {current_user.email} unlinked {provider.value}")
        
        return BaseResponse(
            success=True,
            message=f"{provider.value.capitalize()} account unlinked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth unlink error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink OAuth provider"
        )