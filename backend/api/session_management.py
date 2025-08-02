"""
Session management endpoints for FutureGolf API.
Handles user sessions, device management, and security features.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.config import get_db
from models.user import User
from api.schemas import (
    SessionListResponse, SessionInfo, LogoutResponse, BaseResponse
)
from middleware.auth_middleware import get_current_user
from services.auth_utils import auth_utils
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from config.api import API_VERSION_PREFIX

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{API_VERSION_PREFIX}/sessions", tags=["sessions"])

# In-memory session storage (in production, use Redis or database)
# This is a simplified implementation for demonstration
active_sessions = {}


class SessionManager:
    """Session management utility class."""
    
    @staticmethod
    def create_session(user_id: int, device_info: str, ip_address: str, user_agent: str) -> dict:
        """Create a new user session."""
        session_id = auth_utils.generate_verification_token()
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "device_info": device_info,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "is_active": True
        }
        
        # Store session (in production, use Redis with expiration)
        if user_id not in active_sessions:
            active_sessions[user_id] = {}
        active_sessions[user_id][session_id] = session_data
        
        return session_data
    
    @staticmethod
    def get_user_sessions(user_id: int) -> List[dict]:
        """Get all active sessions for a user."""
        if user_id not in active_sessions:
            return []
        
        # Clean up expired sessions
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session_data in active_sessions[user_id].items():
            # Consider session expired if no activity for 7 days
            if (current_time - session_data["last_activity"]).days > 7:
                expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            del active_sessions[user_id][session_id]
        
        return list(active_sessions[user_id].values())
    
    @staticmethod
    def update_session_activity(user_id: int, session_id: str):
        """Update session last activity."""
        if user_id in active_sessions and session_id in active_sessions[user_id]:
            active_sessions[user_id][session_id]["last_activity"] = datetime.utcnow()
    
    @staticmethod
    def terminate_session(user_id: int, session_id: str) -> bool:
        """Terminate a specific session."""
        if user_id in active_sessions and session_id in active_sessions[user_id]:
            del active_sessions[user_id][session_id]
            return True
        return False
    
    @staticmethod
    def terminate_all_sessions(user_id: int) -> int:
        """Terminate all sessions for a user."""
        if user_id in active_sessions:
            session_count = len(active_sessions[user_id])
            active_sessions[user_id] = {}
            return session_count
        return 0
    
    @staticmethod
    def get_session_info(user_id: int, session_id: str) -> Optional[dict]:
        """Get specific session information."""
        if user_id in active_sessions and session_id in active_sessions[user_id]:
            return active_sessions[user_id][session_id]
        return None


session_manager = SessionManager()


@router.get("/", response_model=SessionListResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Get all active sessions for the current user."""
    try:
        sessions = session_manager.get_user_sessions(current_user.id)
        
        # Convert to response format
        session_list = []
        for session_data in sessions:
            session_info = SessionInfo(
                session_id=session_data["session_id"],
                user_id=session_data["user_id"],
                device_info=session_data.get("device_info", "Unknown device"),
                ip_address=session_data.get("ip_address", "Unknown IP"),
                user_agent=session_data.get("user_agent", "Unknown agent"),
                created_at=session_data["created_at"],
                last_activity=session_data["last_activity"],
                is_active=session_data["is_active"]
            )
            session_list.append(session_info)
        
        return SessionListResponse(
            sessions=session_list,
            total_count=len(session_list)
        )
        
    except Exception as e:
        logger.error(f"Get user sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user sessions"
        )


@router.post("/create", response_model=BaseResponse)
async def create_session(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Create a new session for the current user."""
    try:
        # Get device info from request
        device_info = request.headers.get("user-agent", "Unknown device")
        ip_address = request.client.host if request.client else "Unknown IP"
        user_agent = request.headers.get("user-agent", "Unknown agent")
        
        # Create session
        session_data = session_manager.create_session(
            current_user.id,
            device_info,
            ip_address,
            user_agent
        )
        
        logger.info(f"Session created for user {current_user.email}")
        
        return BaseResponse(
            success=True,
            message="Session created successfully"
        )
        
    except Exception as e:
        logger.error(f"Create session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.delete("/{session_id}", response_model=BaseResponse)
async def terminate_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Terminate a specific session."""
    try:
        # Terminate session
        terminated = session_manager.terminate_session(current_user.id, session_id)
        
        if not terminated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"Session {session_id} terminated for user {current_user.email}")
        
        return BaseResponse(
            success=True,
            message="Session terminated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Terminate session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate session"
        )


@router.delete("/", response_model=LogoutResponse)
async def terminate_all_sessions(
    current_user: User = Depends(get_current_user)
):
    """Terminate all sessions for the current user."""
    try:
        # Terminate all sessions
        terminated_count = session_manager.terminate_all_sessions(current_user.id)
        
        logger.info(f"All sessions terminated for user {current_user.email}")
        
        return LogoutResponse(
            success=True,
            message="All sessions terminated successfully",
            sessions_terminated=terminated_count
        )
        
    except Exception as e:
        logger.error(f"Terminate all sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate all sessions"
        )


@router.get("/{session_id}", response_model=dict)
async def get_session_info(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get information about a specific session."""
    try:
        session_info = session_manager.get_session_info(current_user.id, session_id)
        
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {
            "success": True,
            "session": SessionInfo(
                session_id=session_info["session_id"],
                user_id=session_info["user_id"],
                device_info=session_info.get("device_info", "Unknown device"),
                ip_address=session_info.get("ip_address", "Unknown IP"),
                user_agent=session_info.get("user_agent", "Unknown agent"),
                created_at=session_info["created_at"],
                last_activity=session_info["last_activity"],
                is_active=session_info["is_active"]
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session information"
        )


@router.put("/{session_id}/activity", response_model=BaseResponse)
async def update_session_activity(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Update session activity timestamp."""
    try:
        session_manager.update_session_activity(current_user.id, session_id)
        
        return BaseResponse(
            success=True,
            message="Session activity updated"
        )
        
    except Exception as e:
        logger.error(f"Update session activity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session activity"
        )


@router.get("/security/suspicious", response_model=dict)
async def get_suspicious_activity(
    current_user: User = Depends(get_current_user)
):
    """Get suspicious activity for the current user."""
    try:
        sessions = session_manager.get_user_sessions(current_user.id)
        
        # Simple suspicious activity detection
        suspicious_sessions = []
        unique_ips = set()
        
        for session in sessions:
            ip_address = session.get("ip_address", "Unknown IP")
            unique_ips.add(ip_address)
            
            # Flag sessions from unusual locations or devices
            # This is a simplified example
            if "Unknown" in session.get("device_info", ""):
                suspicious_sessions.append(session)
        
        return {
            "success": True,
            "suspicious_sessions": suspicious_sessions,
            "unique_ip_count": len(unique_ips),
            "total_sessions": len(sessions),
            "message": f"Found {len(suspicious_sessions)} potentially suspicious sessions"
        }
        
    except Exception as e:
        logger.error(f"Get suspicious activity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suspicious activity"
        )


@router.post("/security/logout-all-except-current", response_model=LogoutResponse)
async def logout_all_except_current(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Logout from all sessions except the current one."""
    try:
        # Get current session info
        current_ip = request.client.host if request.client else "Unknown IP"
        current_user_agent = request.headers.get("user-agent", "Unknown agent")
        
        sessions = session_manager.get_user_sessions(current_user.id)
        terminated_count = 0
        
        # Terminate all sessions except the current one
        for session in sessions:
            # Simple matching - in production, you'd use session tokens
            if (session.get("ip_address") != current_ip or 
                session.get("user_agent") != current_user_agent):
                session_manager.terminate_session(current_user.id, session["session_id"])
                terminated_count += 1
        
        logger.info(f"Logged out from {terminated_count} sessions for user {current_user.email}")
        
        return LogoutResponse(
            success=True,
            message="Logged out from all other sessions",
            sessions_terminated=terminated_count
        )
        
    except Exception as e:
        logger.error(f"Logout all except current error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout from other sessions"
        )