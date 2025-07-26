from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from .base import Base
import uuid


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String)
    user_agent = Column(String)
    referrer = Column(String)
    notified = Column(Boolean, default=False)