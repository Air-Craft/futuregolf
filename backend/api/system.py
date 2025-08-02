"""System endpoints - health check, config, etc."""
from fastapi import APIRouter
from config.api import API_VERSION_PREFIX

router = APIRouter(prefix=API_VERSION_PREFIX, tags=["system"])

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "FutureGolf API"}

@router.get("/auth/config")
async def get_auth_config():
    """
    Get authentication configuration
    """
    return {
        "success": True,
        "config": {
            "password_min_length": 8,
            "password_require_uppercase": True,
            "password_require_lowercase": True,
            "password_require_digit": True,
            "password_require_special": True,
            "password_max_length": 128,
            "session_expiry_days": 30,
            "max_sessions_per_user": 10,
            "oauth_providers": ["google", "apple", "facebook"],
            "email_verification_required": True,
            "allow_multiple_accounts_same_email": False
        }
    }