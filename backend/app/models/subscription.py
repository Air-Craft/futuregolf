"""
Subscription and usage tracking models for FutureGolf application.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Float, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.config import Base
import enum


class SubscriptionStatus(enum.Enum):
    """Enum for subscription status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"


class PaymentStatus(enum.Enum):
    """Enum for payment status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Subscription(Base):
    """Model for tracking user subscriptions."""
    
    __tablename__ = "subscriptions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Subscription details
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    tier = Column(String(50), nullable=False)  # trial, pro, etc.
    
    # Billing information
    price = Column(Float, nullable=True)  # Monthly price
    currency = Column(String(3), default="USD")
    
    # Subscription period
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    trial_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Payment provider information
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Auto-renewal
    auto_renew = Column(Boolean, default=True)
    
    # Cancellation information
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Usage limits
    monthly_video_limit = Column(Integer, nullable=True)  # Minutes per month
    analysis_limit = Column(Integer, nullable=True)  # Analyses per month
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    payments = relationship("Payment", back_populates="subscription")
    usage_records = relationship("UsageRecord", back_populates="subscription")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier='{self.tier}', status='{self.status.value}')>"
    
    @property
    def is_active(self):
        """Check if subscription is active."""
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def is_trial(self):
        """Check if subscription is in trial period."""
        return self.status == SubscriptionStatus.TRIAL
    
    @property
    def is_expired(self):
        """Check if subscription is expired."""
        return self.status == SubscriptionStatus.EXPIRED
    
    def cancel(self, reason=None):
        """Cancel the subscription."""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = func.now()
        self.cancellation_reason = reason
        self.auto_renew = False
    
    def renew(self, new_end_date):
        """Renew the subscription."""
        self.end_date = new_end_date
        self.status = SubscriptionStatus.ACTIVE
    
    def upgrade_to_pro(self):
        """Upgrade subscription to pro tier."""
        self.tier = "pro"
        self.monthly_video_limit = 60  # 1 hour
        self.analysis_limit = None  # Unlimited analyses


class Payment(Base):
    """Model for tracking subscription payments."""
    
    __tablename__ = "payments"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Payment provider information
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_charge_id = Column(String(255), nullable=True)
    
    # Payment metadata
    payment_method = Column(String(50), nullable=True)  # card, paypal, etc.
    description = Column(Text, nullable=True)
    
    # Failure information
    failure_code = Column(String(50), nullable=True)
    failure_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, subscription_id={self.subscription_id}, amount={self.amount}, status='{self.status.value}')>"
    
    def mark_as_paid(self):
        """Mark payment as completed."""
        self.status = PaymentStatus.COMPLETED
        self.paid_at = func.now()
    
    def mark_as_failed(self, failure_code, failure_message):
        """Mark payment as failed."""
        self.status = PaymentStatus.FAILED
        self.failure_code = failure_code
        self.failure_message = failure_message


class UsageRecord(Base):
    """Model for tracking user usage."""
    
    __tablename__ = "usage_records"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    
    # Usage details
    usage_type = Column(String(50), nullable=False)  # analysis, video_upload, etc.
    quantity = Column(Float, nullable=False)  # Minutes, count, etc.
    unit = Column(String(20), nullable=False)  # minutes, count, etc.
    
    # Billing period
    billing_period_start = Column(DateTime(timezone=True), nullable=False)
    billing_period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Usage metadata
    usage_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    subscription = relationship("Subscription", back_populates="usage_records")
    video = relationship("Video")
    
    def __repr__(self):
        return f"<UsageRecord(id={self.id}, user_id={self.user_id}, type='{self.usage_type}', quantity={self.quantity})>"