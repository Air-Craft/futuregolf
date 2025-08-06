"""
Authentication utilities for FutureGolf application.
Handles JWT token creation/validation, password hashing, and security utilities.
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Email verification and password reset token settings
EMAIL_TOKEN_EXPIRE_HOURS = int(os.getenv("EMAIL_TOKEN_EXPIRE_HOURS", "24"))
RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("RESET_TOKEN_EXPIRE_HOURS", "1"))


class AuthUtils:
    """Authentication utilities class."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            return None
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure verification token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure password reset token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_verification_token_expiry() -> datetime:
        """Create expiry time for email verification token."""
        return datetime.utcnow() + timedelta(hours=EMAIL_TOKEN_EXPIRE_HOURS)
    
    @staticmethod
    def create_reset_token_expiry() -> datetime:
        """Create expiry time for password reset token."""
        return datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
    
    @staticmethod
    def is_token_expired(expiry_time: datetime) -> bool:
        """Check if a token has expired."""
        return datetime.utcnow() > expiry_time
    
    @staticmethod
    def create_session_token(user_id: int, device_info: Optional[str] = None) -> str:
        """Create a session token for user session management."""
        data = {
            "user_id": user_id,
            "device_info": device_info,
            "session_id": secrets.token_urlsafe(16),
            "created_at": datetime.utcnow().isoformat()
        }
        return AuthUtils.create_access_token(data)
    
    @staticmethod
    def hash_oauth_state(state: str) -> str:
        """Hash OAuth state parameter for security."""
        return hashlib.sha256(state.encode()).hexdigest()
    
    @staticmethod
    def generate_oauth_state() -> str:
        """Generate a secure OAuth state parameter."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength and return requirements."""
        requirements = {
            "min_length": len(password) >= 8,
            "has_uppercase": any(c.isupper() for c in password),
            "has_lowercase": any(c.islower() for c in password),
            "has_digit": any(c.isdigit() for c in password),
            "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        }
        
        is_valid = all(requirements.values())
        
        return {
            "is_valid": is_valid,
            "requirements": requirements,
            "message": "Password meets all requirements" if is_valid else "Password does not meet strength requirements"
        }


# Create singleton instance
auth_utils = AuthUtils()