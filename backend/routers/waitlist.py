from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..db import get_db
from ..models.waitlist import WaitlistEntry
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/waitlist", tags=["waitlist"])


class WaitlistRequest(BaseModel):
    email: EmailStr


class WaitlistResponse(BaseModel):
    success: bool
    message: str


@router.post("", response_model=WaitlistResponse)
async def join_waitlist(
    request: Request,
    waitlist_request: WaitlistRequest,
    db: Session = Depends(get_db)
):
    try:
        # Extract metadata
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        referrer = request.headers.get("referer", "")
        
        # Create waitlist entry
        entry = WaitlistEntry(
            email=waitlist_request.email.lower(),
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer
        )
        
        db.add(entry)
        db.commit()
        
        logger.info(f"New waitlist signup: {waitlist_request.email}")
        
        return WaitlistResponse(
            success=True,
            message="Thanks! We'll notify you when Golf Swing Analysis AI launches."
        )
        
    except IntegrityError:
        # Email already exists
        db.rollback()
        return WaitlistResponse(
            success=True,  # Don't reveal that email already exists
            message="Thanks! We'll notify you when Golf Swing Analysis AI launches."
        )
        
    except Exception as e:
        logger.error(f"Error adding to waitlist: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to join waitlist")