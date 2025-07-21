"""
Database utility functions for FutureGolf application.
This module provides common database operations and helper functions.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import json

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.config import SessionLocal, engine, logger
from models import User, Video, VideoAnalysis, Subscription, Payment, UsageRecord
from models.user import SubscriptionTier
from models.video import VideoStatus
from models.video_analysis import AnalysisStatus
from models.subscription import SubscriptionStatus, PaymentStatus
from sqlalchemy import text, and_, or_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseUtils:
    """Utility class for common database operations."""
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create_user(db: Session, email: str, hashed_password: str, **kwargs) -> User:
        """Create a new user."""
        user = User(
            email=email,
            hashed_password=hashed_password,
            **kwargs
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_videos(db: Session, user_id: int, status: Optional[VideoStatus] = None, 
                       limit: int = 50, offset: int = 0) -> List[Video]:
        """Get user's videos with optional filtering."""
        query = db.query(Video).filter(Video.user_id == user_id)
        
        if status:
            query = query.filter(Video.status == status)
        
        return query.order_by(Video.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_video_by_id(db: Session, video_id: int, user_id: Optional[int] = None) -> Optional[Video]:
        """Get video by ID with optional user validation."""
        query = db.query(Video).filter(Video.id == video_id)
        
        if user_id:
            query = query.filter(Video.user_id == user_id)
        
        return query.first()
    
    @staticmethod
    def create_video(db: Session, user_id: int, video_url: str, **kwargs) -> Video:
        """Create a new video record."""
        video = Video(
            user_id=user_id,
            video_url=video_url,
            **kwargs
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        return video
    
    @staticmethod
    def get_video_analysis(db: Session, video_id: int) -> Optional[VideoAnalysis]:
        """Get video analysis by video ID."""
        return db.query(VideoAnalysis).filter(VideoAnalysis.video_id == video_id).first()
    
    @staticmethod
    def create_video_analysis(db: Session, user_id: int, video_id: int, **kwargs) -> VideoAnalysis:
        """Create a new video analysis record."""
        analysis = VideoAnalysis(
            user_id=user_id,
            video_id=video_id,
            **kwargs
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
    
    @staticmethod
    def get_user_subscription(db: Session, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription."""
        return db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()
    
    @staticmethod
    def create_subscription(db: Session, user_id: int, tier: str, **kwargs) -> Subscription:
        """Create a new subscription."""
        subscription = Subscription(
            user_id=user_id,
            tier=tier,
            **kwargs
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription
    
    @staticmethod
    def get_usage_for_billing_period(db: Session, user_id: int, 
                                   start_date: datetime, end_date: datetime) -> List[UsageRecord]:
        """Get usage records for a specific billing period."""
        return db.query(UsageRecord).filter(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.billing_period_start >= start_date,
                UsageRecord.billing_period_end <= end_date
            )
        ).all()
    
    @staticmethod
    def create_usage_record(db: Session, user_id: int, usage_type: str, 
                          quantity: float, unit: str, **kwargs) -> UsageRecord:
        """Create a new usage record."""
        usage = UsageRecord(
            user_id=user_id,
            usage_type=usage_type,
            quantity=quantity,
            unit=unit,
            **kwargs
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
        return usage


class UserUtils:
    """Utility functions for user operations."""
    
    @staticmethod
    def can_user_analyze_video(db: Session, user_id: int) -> Tuple[bool, str]:
        """Check if user can analyze a video based on their subscription."""
        user = DatabaseUtils.get_user_by_id(db, user_id)
        if not user:
            return False, "User not found"
        
        if user.subscription_tier == SubscriptionTier.TRIAL:
            if user.trial_analyses_used >= user.trial_analysis_limit:
                return False, "Trial analysis limit reached"
            return True, "Trial analysis available"
        
        elif user.subscription_tier == SubscriptionTier.PRO:
            if user.monthly_video_minutes_used >= user.monthly_video_minutes_limit:
                return False, "Monthly video minutes limit reached"
            return True, "Pro subscription active"
        
        return False, "Invalid subscription tier"
    
    @staticmethod
    def increment_user_usage(db: Session, user_id: int, video_duration_minutes: float = 0):
        """Increment user's usage counters."""
        user = DatabaseUtils.get_user_by_id(db, user_id)
        if not user:
            return False
        
        if user.subscription_tier == SubscriptionTier.TRIAL:
            user.trial_analyses_used += 1
        elif user.subscription_tier == SubscriptionTier.PRO:
            user.monthly_video_minutes_used += video_duration_minutes
        
        db.commit()
        return True
    
    @staticmethod
    def reset_user_monthly_usage(db: Session, user_id: int):
        """Reset user's monthly usage counters."""
        user = DatabaseUtils.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.monthly_video_minutes_used = 0
        db.commit()
        return True
    
    @staticmethod
    def upgrade_user_to_pro(db: Session, user_id: int):
        """Upgrade user to pro tier."""
        user = DatabaseUtils.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.subscription_tier = SubscriptionTier.PRO
        user.monthly_video_minutes_used = 0
        user.monthly_video_minutes_limit = 60
        db.commit()
        return True


class VideoUtils:
    """Utility functions for video operations."""
    
    @staticmethod
    def get_user_video_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """Get user's video statistics."""
        stats = {
            "total_videos": 0,
            "ready_videos": 0,
            "processing_videos": 0,
            "failed_videos": 0,
            "analyzed_videos": 0,
            "total_duration_minutes": 0,
            "favorite_videos": 0
        }
        
        # Get all user videos
        videos = db.query(Video).filter(Video.user_id == user_id).all()
        
        stats["total_videos"] = len(videos)
        
        for video in videos:
            if video.status == VideoStatus.READY:
                stats["ready_videos"] += 1
            elif video.status in [VideoStatus.PROCESSING, VideoStatus.UPLOADING]:
                stats["processing_videos"] += 1
            elif video.status == VideoStatus.FAILED:
                stats["failed_videos"] += 1
            
            if video.has_analysis:
                stats["analyzed_videos"] += 1
            
            if video.is_favorite:
                stats["favorite_videos"] += 1
            
            if video.duration:
                stats["total_duration_minutes"] += video.duration / 60
        
        return stats
    
    @staticmethod
    def get_recent_videos(db: Session, user_id: int, days: int = 7) -> List[Video]:
        """Get user's recent videos."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.query(Video).filter(
            and_(
                Video.user_id == user_id,
                Video.created_at >= cutoff_date
            )
        ).order_by(Video.created_at.desc()).all()
    
    @staticmethod
    def soft_delete_video(db: Session, video_id: int, user_id: int) -> bool:
        """Soft delete a video."""
        video = DatabaseUtils.get_video_by_id(db, video_id, user_id)
        if not video:
            return False
        
        video.soft_delete()
        db.commit()
        return True
    
    @staticmethod
    def toggle_video_favorite(db: Session, video_id: int, user_id: int) -> bool:
        """Toggle video favorite status."""
        video = DatabaseUtils.get_video_by_id(db, video_id, user_id)
        if not video:
            return False
        
        video.toggle_favorite()
        db.commit()
        return True


class AnalysisUtils:
    """Utility functions for video analysis operations."""
    
    @staticmethod
    def get_user_analysis_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """Get user's analysis statistics."""
        stats = {
            "total_analyses": 0,
            "completed_analyses": 0,
            "failed_analyses": 0,
            "pending_analyses": 0,
            "average_analysis_duration": 0
        }
        
        analyses = db.query(VideoAnalysis).filter(VideoAnalysis.user_id == user_id).all()
        
        stats["total_analyses"] = len(analyses)
        
        analysis_durations = []
        
        for analysis in analyses:
            if analysis.status == AnalysisStatus.COMPLETED:
                stats["completed_analyses"] += 1
            elif analysis.status == AnalysisStatus.FAILED:
                stats["failed_analyses"] += 1
            elif analysis.status in [AnalysisStatus.PENDING, AnalysisStatus.PROCESSING]:
                stats["pending_analyses"] += 1
            
            if analysis.analysis_duration:
                analysis_durations.append(analysis.analysis_duration)
        
        if analysis_durations:
            stats["average_analysis_duration"] = sum(analysis_durations) / len(analysis_durations)
        
        return stats
    
    @staticmethod
    def get_recent_analyses(db: Session, user_id: int, days: int = 7) -> List[VideoAnalysis]:
        """Get user's recent analyses."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.query(VideoAnalysis).filter(
            and_(
                VideoAnalysis.user_id == user_id,
                VideoAnalysis.created_at >= cutoff_date
            )
        ).order_by(VideoAnalysis.created_at.desc()).all()


class SubscriptionUtils:
    """Utility functions for subscription operations."""
    
    @staticmethod
    def get_subscription_stats(db: Session) -> Dict[str, Any]:
        """Get overall subscription statistics."""
        stats = {
            "total_subscriptions": 0,
            "active_subscriptions": 0,
            "trial_subscriptions": 0,
            "pro_subscriptions": 0,
            "cancelled_subscriptions": 0,
            "expired_subscriptions": 0
        }
        
        subscriptions = db.query(Subscription).all()
        
        stats["total_subscriptions"] = len(subscriptions)
        
        for subscription in subscriptions:
            if subscription.status == SubscriptionStatus.ACTIVE:
                stats["active_subscriptions"] += 1
            elif subscription.status == SubscriptionStatus.TRIAL:
                stats["trial_subscriptions"] += 1
            elif subscription.status == SubscriptionStatus.CANCELLED:
                stats["cancelled_subscriptions"] += 1
            elif subscription.status == SubscriptionStatus.EXPIRED:
                stats["expired_subscriptions"] += 1
            
            if subscription.tier == "pro":
                stats["pro_subscriptions"] += 1
        
        return stats
    
    @staticmethod
    def get_expiring_subscriptions(db: Session, days: int = 7) -> List[Subscription]:
        """Get subscriptions expiring within N days."""
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        
        return db.query(Subscription).filter(
            and_(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date <= cutoff_date
            )
        ).all()


class DatabaseHealth:
    """Database health and monitoring utilities."""
    
    @staticmethod
    def check_connection() -> bool:
        """Check if database connection is healthy."""
        try:
            with get_db_session() as db:
                db.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    @staticmethod
    def get_table_sizes(db: Session) -> Dict[str, int]:
        """Get the size of each table."""
        tables = ["users", "videos", "video_analyses", "subscriptions", "payments", "usage_records"]
        sizes = {}
        
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                sizes[table] = result.fetchone()[0]
            except Exception as e:
                logger.warning(f"Could not get size for table {table}: {e}")
                sizes[table] = -1
        
        return sizes
    
    @staticmethod
    def get_database_size(db: Session) -> Dict[str, str]:
        """Get database size information."""
        try:
            result = db.execute(text("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    pg_size_pretty(pg_total_relation_size('users')) as users_table_size,
                    pg_size_pretty(pg_total_relation_size('videos')) as videos_table_size,
                    pg_size_pretty(pg_total_relation_size('video_analyses')) as analyses_table_size
            """))
            
            row = result.fetchone()
            return {
                "database_size": row[0],
                "users_table_size": row[1],
                "videos_table_size": row[2],
                "analyses_table_size": row[3]
            }
        except Exception as e:
            logger.error(f"Could not get database size: {e}")
            return {}
    
    @staticmethod
    def get_active_connections(db: Session) -> int:
        """Get number of active database connections."""
        try:
            result = db.execute(text("""
                SELECT COUNT(*) 
                FROM pg_stat_activity 
                WHERE state = 'active'
            """))
            return result.fetchone()[0]
        except Exception as e:
            logger.error(f"Could not get active connections: {e}")
            return -1


# Convenience functions for common operations
def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email (convenience function)."""
    with get_db_session() as db:
        return DatabaseUtils.get_user_by_email(db, email)


def get_user_videos(user_id: int, status: Optional[VideoStatus] = None) -> List[Video]:
    """Get user videos (convenience function)."""
    with get_db_session() as db:
        return DatabaseUtils.get_user_videos(db, user_id, status)


def get_video_with_analysis(video_id: int) -> Optional[Tuple[Video, VideoAnalysis]]:
    """Get video with its analysis (convenience function)."""
    with get_db_session() as db:
        video = DatabaseUtils.get_video_by_id(db, video_id)
        if not video:
            return None
        
        analysis = DatabaseUtils.get_video_analysis(db, video_id)
        return video, analysis


def check_database_health() -> Dict[str, Any]:
    """Check overall database health (convenience function)."""
    health = {
        "connection": DatabaseHealth.check_connection(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if health["connection"]:
        with get_db_session() as db:
            health["table_sizes"] = DatabaseHealth.get_table_sizes(db)
            health["database_sizes"] = DatabaseHealth.get_database_size(db)
            health["active_connections"] = DatabaseHealth.get_active_connections(db)
    
    return health


if __name__ == "__main__":
    # Example usage and testing
    print("Database Utils Test")
    print("=" * 30)
    
    # Test connection
    if DatabaseHealth.check_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
        sys.exit(1)
    
    # Test health check
    health = check_database_health()
    print(f"Database health: {health}")
    
    # Test table sizes
    with get_db_session() as db:
        sizes = DatabaseHealth.get_table_sizes(db)
        print(f"Table sizes: {sizes}")
    
    print("Database utils test completed!")