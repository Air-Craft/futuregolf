"""
OAuth service for FutureGolf application.
Handles OAuth authentication with Google, LinkedIn, and Microsoft.
"""

import os
import json
import secrets
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# OAuth Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = f"{BACKEND_URL}/api/v1/auth/oauth/google/callback"

# Microsoft OAuth
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_REDIRECT_URI = f"{BACKEND_URL}/api/v1/auth/oauth/microsoft/callback"

# LinkedIn OAuth
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = f"{BACKEND_URL}/api/v1/auth/oauth/linkedin/callback"


class OAuthProvider:
    """Base OAuth provider class."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state_storage = {}  # In production, use Redis or database
    
    def generate_state(self) -> str:
        """Generate and store OAuth state parameter."""
        state = secrets.token_urlsafe(32)
        self.state_storage[state] = {
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        return state
    
    def validate_state(self, state: str) -> bool:
        """Validate OAuth state parameter."""
        if state not in self.state_storage:
            return False
        
        state_data = self.state_storage[state]
        if datetime.utcnow() > state_data["expires_at"]:
            del self.state_storage[state]
            return False
        
        del self.state_storage[state]
        return True
    
    def get_authorization_url(self) -> Tuple[str, str]:
        """Get authorization URL and state. Must be implemented by subclasses."""
        raise NotImplementedError
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token. Must be implemented by subclasses."""
        raise NotImplementedError
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information using access token. Must be implemented by subclasses."""
        raise NotImplementedError


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider."""
    
    def __init__(self):
        super().__init__(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.scope = "openid email profile"
    
    def get_authorization_url(self) -> Tuple[str, str]:
        """Get Google authorization URL."""
        state = self.generate_state()
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        url = f"{self.auth_url}?{urlencode(params)}"
        return url, state
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange Google authorization code for access token."""
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Google token exchange error: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get Google user information."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Google user info error: {e}")
            return None


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft OAuth provider."""
    
    def __init__(self):
        super().__init__(MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_REDIRECT_URI)
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")
        self.auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.user_info_url = "https://graph.microsoft.com/v1.0/me"
        self.scope = "openid email profile User.Read"
    
    def get_authorization_url(self) -> Tuple[str, str]:
        """Get Microsoft authorization URL."""
        state = self.generate_state()
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "response_type": "code",
            "state": state,
            "response_mode": "query"
        }
        url = f"{self.auth_url}?{urlencode(params)}"
        return url, state
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange Microsoft authorization code for access token."""
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
                "scope": self.scope
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Microsoft token exchange error: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get Microsoft user information."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Microsoft user info error: {e}")
            return None


class LinkedInOAuthProvider(OAuthProvider):
    """LinkedIn OAuth provider."""
    
    def __init__(self):
        super().__init__(LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_REDIRECT_URI)
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.user_info_url = "https://api.linkedin.com/v2/userinfo"
        self.scope = "openid email profile"
    
    def get_authorization_url(self) -> Tuple[str, str]:
        """Get LinkedIn authorization URL."""
        state = self.generate_state()
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "response_type": "code",
            "state": state
        }
        url = f"{self.auth_url}?{urlencode(params)}"
        return url, state
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange LinkedIn authorization code for access token."""
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }
            
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"LinkedIn token exchange error: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get LinkedIn user information."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"LinkedIn user info error: {e}")
            return None


class OAuthService:
    """OAuth service for managing multiple providers."""
    
    def __init__(self):
        self.providers = {}
        
        # Initialize providers if credentials are available
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
            self.providers["google"] = GoogleOAuthProvider()
        
        if MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET:
            self.providers["microsoft"] = MicrosoftOAuthProvider()
        
        if LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET:
            self.providers["linkedin"] = LinkedInOAuthProvider()
    
    def get_provider(self, provider_name: str) -> Optional[OAuthProvider]:
        """Get OAuth provider by name."""
        return self.providers.get(provider_name)
    
    def get_available_providers(self) -> list:
        """Get list of available OAuth providers."""
        return list(self.providers.keys())
    
    def is_provider_configured(self, provider_name: str) -> bool:
        """Check if OAuth provider is configured."""
        return provider_name in self.providers
    
    def normalize_user_data(self, provider_name: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize user data from different providers."""
        normalized = {
            "provider": provider_name,
            "provider_id": None,
            "email": None,
            "first_name": None,
            "last_name": None,
            "full_name": None,
            "profile_picture_url": None,
            "is_verified": False
        }
        
        if provider_name == "google":
            normalized.update({
                "provider_id": user_data.get("id"),
                "email": user_data.get("email"),
                "first_name": user_data.get("given_name"),
                "last_name": user_data.get("family_name"),
                "full_name": user_data.get("name"),
                "profile_picture_url": user_data.get("picture"),
                "is_verified": user_data.get("verified_email", False)
            })
        
        elif provider_name == "microsoft":
            normalized.update({
                "provider_id": user_data.get("id"),
                "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                "first_name": user_data.get("givenName"),
                "last_name": user_data.get("surname"),
                "full_name": user_data.get("displayName"),
                "profile_picture_url": None,  # Would need separate API call
                "is_verified": True  # Microsoft emails are typically verified
            })
        
        elif provider_name == "linkedin":
            normalized.update({
                "provider_id": user_data.get("sub"),
                "email": user_data.get("email"),
                "first_name": user_data.get("given_name"),
                "last_name": user_data.get("family_name"),
                "full_name": user_data.get("name"),
                "profile_picture_url": user_data.get("picture"),
                "is_verified": user_data.get("email_verified", False)
            })
        
        return normalized


# Create singleton instance
oauth_service = OAuthService()