"""
Database testing script for FutureGolf application.
This script tests database connectivity and basic CRUD operations.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import asyncio

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.config import engine, SessionLocal, logger
from app.models import User, Video, VideoAnalysis, Subscription, Payment, UsageRecord
from app.models.user import SubscriptionTier
from app.models.video import VideoStatus
from app.models.video_analysis import AnalysisStatus
from app.models.subscription import SubscriptionStatus, PaymentStatus
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)


class DatabaseTester:
    """Database testing class with comprehensive test scenarios."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.test_results = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if success else "FAIL"
        logger.info(f"{test_name}: {status} - {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_connection(self):
        """Test basic database connection."""
        try:
            result = self.db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            success = row[0] == 1
            self.log_test("Database Connection", success, "Connection successful")
            return success
        except Exception as e:
            self.log_test("Database Connection", False, f"Connection failed: {e}")
            return False
    
    def test_table_creation(self):
        """Test if all required tables exist."""
        try:
            required_tables = [
                "users", "videos", "video_analyses", "subscriptions", 
                "payments", "usage_records"
            ]
            
            result = self.db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = ANY(:tables)
            """), {"tables": required_tables})
            
            existing_tables = [row[0] for row in result.fetchall()]
            missing_tables = set(required_tables) - set(existing_tables)
            
            if missing_tables:
                self.log_test("Table Creation", False, f"Missing tables: {missing_tables}")
                return False
            else:
                self.log_test("Table Creation", True, "All required tables exist")
                return True
                
        except Exception as e:
            self.log_test("Table Creation", False, f"Error checking tables: {e}")
            return False
    
    def test_user_crud(self):
        """Test User model CRUD operations."""
        try:
            # Create
            test_user = User(
                email="test@example.com",
                hashed_password="hashed_password",
                first_name="Test",
                last_name="User",
                subscription_tier=SubscriptionTier.TRIAL
            )
            self.db.add(test_user)
            self.db.commit()
            
            # Read
            user = self.db.query(User).filter(User.email == "test@example.com").first()
            if not user:
                raise Exception("User not found after creation")
            
            # Update
            user.first_name = "Updated"
            self.db.commit()
            
            # Verify update
            updated_user = self.db.query(User).filter(User.id == user.id).first()
            if updated_user.first_name != "Updated":
                raise Exception("User update failed")
            
            # Delete
            self.db.delete(user)
            self.db.commit()
            
            # Verify deletion
            deleted_user = self.db.query(User).filter(User.id == user.id).first()
            if deleted_user:
                raise Exception("User deletion failed")
            
            self.log_test("User CRUD", True, "All operations successful")
            return True
            
        except Exception as e:
            self.log_test("User CRUD", False, f"Error: {e}")
            return False
    
    def test_video_crud(self):
        """Test Video model CRUD operations."""
        try:
            # Create user first
            test_user = User(
                email="video_test@example.com",
                hashed_password="hashed_password",
                subscription_tier=SubscriptionTier.PRO
            )
            self.db.add(test_user)
            self.db.commit()
            
            # Create video
            test_video = Video(
                user_id=test_user.id,
                title="Test Video",
                description="Test video description",
                video_url="https://example.com/video.mp4",
                duration=30.0,
                status=VideoStatus.UPLOADED
            )
            self.db.add(test_video)
            self.db.commit()
            
            # Read
            video = self.db.query(Video).filter(Video.title == "Test Video").first()
            if not video:
                raise Exception("Video not found after creation")
            
            # Update
            video.title = "Updated Video"
            self.db.commit()
            
            # Test relationships
            if video.user.email != "video_test@example.com":
                raise Exception("User relationship failed")
            
            # Clean up
            self.db.delete(video)
            self.db.delete(test_user)
            self.db.commit()
            
            self.log_test("Video CRUD", True, "All operations successful")
            return True
            
        except Exception as e:
            self.log_test("Video CRUD", False, f"Error: {e}")
            return False
    
    def test_video_analysis_crud(self):
        """Test VideoAnalysis model CRUD operations."""
        try:
            # Create user and video first
            test_user = User(
                email="analysis_test@example.com",
                hashed_password="hashed_password",
                subscription_tier=SubscriptionTier.PRO
            )
            self.db.add(test_user)
            self.db.commit()
            
            test_video = Video(
                user_id=test_user.id,
                title="Analysis Test Video",
                video_url="https://example.com/video.mp4",
                duration=30.0,
                status=VideoStatus.READY
            )
            self.db.add(test_video)
            self.db.commit()
            
            # Create analysis
            test_analysis = VideoAnalysis(
                user_id=test_user.id,
                video_id=test_video.id,
                status=AnalysisStatus.COMPLETED,
                analysis_duration=25.0,
                pose_data={"test": "data"},
                swing_metrics={"tempo": 1.2}
            )
            self.db.add(test_analysis)
            self.db.commit()
            
            # Read
            analysis = self.db.query(VideoAnalysis).filter(
                VideoAnalysis.video_id == test_video.id
            ).first()
            
            if not analysis:
                raise Exception("Analysis not found after creation")
            
            # Test relationships
            if analysis.user.email != "analysis_test@example.com":
                raise Exception("User relationship failed")
            
            if analysis.video.title != "Analysis Test Video":
                raise Exception("Video relationship failed")
            
            # Clean up
            self.db.delete(analysis)
            self.db.delete(test_video)
            self.db.delete(test_user)
            self.db.commit()
            
            self.log_test("VideoAnalysis CRUD", True, "All operations successful")
            return True
            
        except Exception as e:
            self.log_test("VideoAnalysis CRUD", False, f"Error: {e}")
            return False
    
    def test_subscription_crud(self):
        """Test Subscription model CRUD operations."""
        try:
            # Create user first
            test_user = User(
                email="subscription_test@example.com",
                hashed_password="hashed_password",
                subscription_tier=SubscriptionTier.PRO
            )
            self.db.add(test_user)
            self.db.commit()
            
            # Create subscription
            test_subscription = Subscription(
                user_id=test_user.id,
                status=SubscriptionStatus.ACTIVE,
                tier="pro",
                price=9.99,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            self.db.add(test_subscription)
            self.db.commit()
            
            # Read
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == test_user.id
            ).first()
            
            if not subscription:
                raise Exception("Subscription not found after creation")
            
            # Test methods
            if not subscription.is_active:
                raise Exception("is_active property failed")
            
            # Clean up
            self.db.delete(subscription)
            self.db.delete(test_user)
            self.db.commit()
            
            self.log_test("Subscription CRUD", True, "All operations successful")
            return True
            
        except Exception as e:
            self.log_test("Subscription CRUD", False, f"Error: {e}")
            return False
    
    def test_payment_crud(self):
        """Test Payment model CRUD operations."""
        try:
            # Create user and subscription first
            test_user = User(
                email="payment_test@example.com",
                hashed_password="hashed_password",
                subscription_tier=SubscriptionTier.PRO
            )
            self.db.add(test_user)
            self.db.commit()
            
            test_subscription = Subscription(
                user_id=test_user.id,
                status=SubscriptionStatus.ACTIVE,
                tier="pro",
                price=9.99,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            self.db.add(test_subscription)
            self.db.commit()
            
            # Create payment
            test_payment = Payment(
                subscription_id=test_subscription.id,
                amount=9.99,
                status=PaymentStatus.COMPLETED,
                payment_method="card"
            )
            self.db.add(test_payment)
            self.db.commit()
            
            # Read
            payment = self.db.query(Payment).filter(
                Payment.subscription_id == test_subscription.id
            ).first()
            
            if not payment:
                raise Exception("Payment not found after creation")
            
            # Test relationships
            if payment.subscription.user.email != "payment_test@example.com":
                raise Exception("Subscription relationship failed")
            
            # Clean up
            self.db.delete(payment)
            self.db.delete(test_subscription)
            self.db.delete(test_user)
            self.db.commit()
            
            self.log_test("Payment CRUD", True, "All operations successful")
            return True
            
        except Exception as e:
            self.log_test("Payment CRUD", False, f"Error: {e}")
            return False
    
    def test_usage_record_crud(self):
        """Test UsageRecord model CRUD operations."""
        try:
            # Create user, subscription, and video first
            test_user = User(
                email="usage_test@example.com",
                hashed_password="hashed_password",
                subscription_tier=SubscriptionTier.PRO
            )
            self.db.add(test_user)
            self.db.commit()
            
            test_subscription = Subscription(
                user_id=test_user.id,
                status=SubscriptionStatus.ACTIVE,
                tier="pro",
                price=9.99,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            self.db.add(test_subscription)
            self.db.commit()
            
            test_video = Video(
                user_id=test_user.id,
                title="Usage Test Video",
                video_url="https://example.com/video.mp4",
                duration=30.0,
                status=VideoStatus.READY
            )
            self.db.add(test_video)
            self.db.commit()
            
            # Create usage record
            test_usage = UsageRecord(
                user_id=test_user.id,
                subscription_id=test_subscription.id,
                video_id=test_video.id,
                usage_type="analysis",
                quantity=1,
                unit="count",
                billing_period_start=datetime.utcnow(),
                billing_period_end=datetime.utcnow() + timedelta(days=30)
            )
            self.db.add(test_usage)
            self.db.commit()
            
            # Read
            usage = self.db.query(UsageRecord).filter(
                UsageRecord.user_id == test_user.id
            ).first()
            
            if not usage:
                raise Exception("Usage record not found after creation")
            
            # Test relationships
            if usage.user.email != "usage_test@example.com":
                raise Exception("User relationship failed")
            
            # Clean up
            self.db.delete(usage)
            self.db.delete(test_video)
            self.db.delete(test_subscription)
            self.db.delete(test_user)
            self.db.commit()
            
            self.log_test("UsageRecord CRUD", True, "All operations successful")
            return True
            
        except Exception as e:
            self.log_test("UsageRecord CRUD", False, f"Error: {e}")
            return False
    
    def test_database_indexes(self):
        """Test if database indexes are created properly."""
        try:
            # Query to check indexes
            result = self.db.execute(text("""
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND indexname LIKE 'idx_%'
            """))
            
            indexes = [(row[0], row[1]) for row in result.fetchall()]
            
            if len(indexes) == 0:
                self.log_test("Database Indexes", False, "No custom indexes found")
                return False
            
            self.log_test("Database Indexes", True, f"Found {len(indexes)} custom indexes")
            return True
            
        except Exception as e:
            self.log_test("Database Indexes", False, f"Error checking indexes: {e}")
            return False
    
    def test_database_constraints(self):
        """Test if database constraints are working."""
        try:
            # Test unique constraint on email
            user1 = User(
                email="constraint_test@example.com",
                hashed_password="password1",
                subscription_tier=SubscriptionTier.TRIAL
            )
            self.db.add(user1)
            self.db.commit()
            
            user2 = User(
                email="constraint_test@example.com",  # Same email
                hashed_password="password2",
                subscription_tier=SubscriptionTier.TRIAL
            )
            self.db.add(user2)
            
            try:
                self.db.commit()
                # If we get here, constraint didn't work
                self.log_test("Database Constraints", False, "Unique constraint on email failed")
                return False
            except Exception:
                # This is expected - unique constraint should prevent duplicate emails
                self.db.rollback()
                
                # Clean up
                self.db.delete(user1)
                self.db.commit()
                
                self.log_test("Database Constraints", True, "Unique constraint on email working")
                return True
                
        except Exception as e:
            self.log_test("Database Constraints", False, f"Error testing constraints: {e}")
            return False
    
    def run_all_tests(self):
        """Run all database tests."""
        logger.info("Starting database tests...")
        logger.info("=" * 50)
        
        tests = [
            self.test_connection,
            self.test_table_creation,
            self.test_user_crud,
            self.test_video_crud,
            self.test_video_analysis_crud,
            self.test_subscription_crud,
            self.test_payment_crud,
            self.test_usage_record_crud,
            self.test_database_indexes,
            self.test_database_constraints
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {e}")
                failed += 1
        
        logger.info("=" * 50)
        logger.info(f"Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            logger.info("All database tests passed!")
            return True
        else:
            logger.error(f"{failed} tests failed!")
            return False


def main():
    """Main function to run database tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FutureGolf Database Tests")
    parser.add_argument("--test", choices=[
        "connection", "tables", "user", "video", "analysis", 
        "subscription", "payment", "usage", "indexes", "constraints", "all"
    ], default="all", help="Specific test to run")
    
    args = parser.parse_args()
    
    with DatabaseTester() as tester:
        if args.test == "all":
            success = tester.run_all_tests()
        else:
            test_methods = {
                "connection": tester.test_connection,
                "tables": tester.test_table_creation,
                "user": tester.test_user_crud,
                "video": tester.test_video_crud,
                "analysis": tester.test_video_analysis_crud,
                "subscription": tester.test_subscription_crud,
                "payment": tester.test_payment_crud,
                "usage": tester.test_usage_record_crud,
                "indexes": tester.test_database_indexes,
                "constraints": tester.test_database_constraints
            }
            
            success = test_methods[args.test]()
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()