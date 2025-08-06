"""
Authentication middleware for FutureGolf application.
Handles JWT token validation and user authentication.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.user import User
from app.services.auth_utils import auth_utils
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class AuthMiddleware:
    """Authentication middleware class."""
    
    @staticmethod
    def get_current_user_from_token(token: str, db: Session) -> Optional[User]:
        """Get current user from JWT token."""
        try:
            # Decode token
            payload = auth_utils.decode_token(token)
            if not payload:
                return None
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Get user ID from payload
            user_id = payload.get("user_id")
            if not user_id:
                return None
            
            # Get user from database
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Check if user is active
            if not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    @staticmethod
    def get_current_user_optional(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> Optional[User]:
        """Get current user from token (optional - doesn't raise error if no token)."""
        if not credentials:
            return None
        
        return AuthMiddleware.get_current_user_from_token(credentials.credentials, db)
    
    @staticmethod
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        """Get current user from token (required - raises error if no valid token)."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = AuthMiddleware.get_current_user_from_token(credentials.credentials, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    @staticmethod
    def get_current_verified_user(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Get current verified user (requires email verification)."""
        if not current_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required"
            )
        return current_user
    
    @staticmethod
    def get_current_active_user(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Get current active user (already checked in get_current_user)."""
        return current_user
    
    @staticmethod
    def require_subscription_tier(required_tier: str):
        """Decorator to require specific subscription tier."""
        def dependency(current_user: User = Depends(get_current_verified_user)) -> User:
            if current_user.subscription_tier.value != required_tier:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Subscription tier '{required_tier}' required"
                )
            return current_user
        return dependency
    
    @staticmethod
    def require_admin():
        """Decorator to require admin privileges."""
        def dependency(current_user: User = Depends(get_current_verified_user)) -> User:
            # Add admin check logic here if you have admin roles
            # For now, we'll just return the user
            return current_user
        return dependency
    
    @staticmethod
    def validate_refresh_token(token: str, db: Session) -> Optional[User]:
        """Validate refresh token and return user."""
        try:
            # Decode token
            payload = auth_utils.decode_token(token)
            if not payload:
                return None
            
            # Check token type
            if payload.get("type") != "refresh":
                return None
            
            # Get user ID from payload
            user_id = payload.get("user_id")
            if not user_id:
                return None
            
            # Get user from database
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Check if user is active
            if not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Refresh token validation error: {e}")
            return None
    
    @staticmethod
    def validate_api_key(api_key: str, db: Session) -> Optional[User]:
        """Validate API key and return associated user."""
        # This would be implemented if you have API key authentication
        # For now, we'll just return None
        return None
    
    @staticmethod
    def get_user_permissions(user: User) -> Dict[str, Any]:
        """Get user permissions based on subscription tier."""
        permissions = {
            "can_upload_video": user.can_analyze_video(),
            "can_analyze_video": user.can_analyze_video(),
            "max_video_length": 300,  # 5 minutes default
            "can_access_premium_features": False,
            "can_export_data": False,
            "can_share_videos": True,
            "subscription_tier": user.subscription_tier.value
        }
        
        if user.subscription_tier.value == "pro":
            permissions.update({
                "max_video_length": 1800,  # 30 minutes
                "can_access_premium_features": True,
                "can_export_data": True,
                "monthly_analysis_limit": user.monthly_video_minutes_limit
            })
        elif user.subscription_tier.value == "trial":
            permissions.update({
                "trial_analyses_remaining": user.trial_analysis_limit - user.trial_analyses_used
            })
        
        return permissions
    
    @staticmethod
    def check_rate_limit(user: User, action: str) -> bool:
        """Check if user has exceeded rate limits for specific actions."""
        # This would implement rate limiting logic
        # For now, we'll just return True
        return True


# Create middleware instance
auth_middleware = AuthMiddleware()

# Common dependency functions
get_current_user = auth_middleware.get_current_user
get_current_user_optional = auth_middleware.get_current_user_optional
get_current_verified_user = auth_middleware.get_current_verified_user
get_current_active_user = auth_middleware.get_current_active_user
require_subscription_tier = auth_middleware.require_subscription_tier
require_admin = auth_middleware.require_admin