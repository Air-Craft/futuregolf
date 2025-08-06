"""
Test configuration and fixtures for FutureGolf application.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import tempfile
import os
from typing import Generator, Dict, Any

# Import application components
from app.main import app
from app.database.config import get_db, Base
from app.models.user import User, SubscriptionTier
from app.models.video import Video, VideoStatus
from app.models.video_analysis import VideoAnalysis
from app.services.auth_utils import auth_utils
from app.services.storage_service import storage_service


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Create test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "subscription_tier": SubscriptionTier.TRIAL
    }


@pytest.fixture
def sample_user(db_session: Session, sample_user_data: Dict[str, Any]) -> User:
    """Create a sample user in the database."""
    user = User(
        email=sample_user_data["email"],
        hashed_password=auth_utils.hash_password(sample_user_data["password"]),
        first_name=sample_user_data["first_name"],
        last_name=sample_user_data["last_name"],
        subscription_tier=sample_user_data["subscription_tier"],
        is_verified=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_pro_user(db_session: Session) -> User:
    """Create a sample pro user in the database."""
    user = User(
        email="pro@example.com",
        hashed_password=auth_utils.hash_password("ProPassword123!"),
        first_name="Pro",
        last_name="User",
        subscription_tier=SubscriptionTier.PRO,
        is_verified=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_video(db_session: Session, sample_user: User) -> Video:
    """Create a sample video in the database."""
    video = Video(
        user_id=sample_user.id,
        original_filename="test_video.mov",
        file_size=1024 * 1024,  # 1MB
        duration=30.0,
        status=VideoStatus.UPLOADED,
        blob_name="test_blob_name.mp4",
        public_url="https://example.com/test_video.mov"
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
def sample_video_analysis(db_session: Session, sample_user: User, sample_video: Video) -> VideoAnalysis:
    """Create a sample video analysis in the database."""
    analysis = VideoAnalysis(
        user_id=sample_user.id,
        video_id=sample_video.id,
        analysis_type="swing_analysis",
        analysis_data={
            "swing_speed": 120.5,
            "swing_plane": "slightly inside",
            "impact_position": "good",
            "follow_through": "excellent"
        },
        coaching_feedback="Great swing! Keep working on your follow-through.",
        status="completed"
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


@pytest.fixture
def auth_headers(sample_user: User) -> Dict[str, str]:
    """Create authentication headers for testing."""
    access_token = auth_utils.create_access_token(
        data={"user_id": sample_user.id, "email": sample_user.email}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def pro_auth_headers(sample_pro_user: User) -> Dict[str, str]:
    """Create authentication headers for pro user testing."""
    access_token = auth_utils.create_access_token(
        data={"user_id": sample_pro_user.id, "email": sample_pro_user.email}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def invalid_auth_headers() -> Dict[str, str]:
    """Create invalid authentication headers for testing."""
    return {"Authorization": "Bearer invalid_token"}


@pytest.fixture
def expired_auth_headers(sample_user: User) -> Dict[str, str]:
    """Create expired authentication headers for testing."""
    # Create token with past expiration
    access_token = auth_utils.create_access_token(
        data={"user_id": sample_user.id, "email": sample_user.email},
        expires_delta=timedelta(minutes=-10)  # Expired 10 minutes ago
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_storage_service():
    """Mock storage service for testing."""
    with patch('services.storage_service.storage_service') as mock_service:
        mock_service.upload_video.return_value = {
            "success": True,
            "blob_name": "test_blob_name.mp4",
            "public_url": "https://example.com/test_video.mov",
            "file_size": 1024 * 1024,
            "content_type": "video/mp4"
        }
        
        mock_service.upload_thumbnail.return_value = {
            "success": True,
            "blob_name": "test_thumbnail.jpg",
            "public_url": "https://example.com/test_thumbnail.jpg",
            "size": 50 * 1024
        }
        
        mock_service.delete_file.return_value = True
        mock_service.generate_signed_url.return_value = "https://example.com/signed_url"
        
        yield mock_service


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    with patch('services.email_service.email_service') as mock_service:
        mock_service.send_verification_email.return_value = True
        mock_service.send_password_reset_email.return_value = True
        mock_service.send_welcome_email.return_value = True
        
        yield mock_service


@pytest.fixture
def mock_oauth_service():
    """Mock OAuth service for testing."""
    with patch('services.oauth_service.oauth_service') as mock_service:
        mock_service.verify_google_token.return_value = {
            "sub": "google_user_id",
            "email": "oauth@example.com",
            "given_name": "OAuth",
            "family_name": "User",
            "picture": "https://example.com/picture.jpg"
        }
        
        mock_service.verify_microsoft_token.return_value = {
            "sub": "microsoft_user_id",
            "email": "oauth@example.com",
            "given_name": "OAuth",
            "family_name": "User"
        }
        
        yield mock_service


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test video content")
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def sample_video_file():
    """Create a sample video file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        # Write some dummy video content
        tmp.write(b"fake video content for testing")
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def jwt_secret():
    """JWT secret key for testing."""
    return "test_secret_key_for_testing_only"


@pytest.fixture(autouse=True)
def set_test_environment():
    """Set test environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ.update({
        "TESTING": "true",
        "DATABASE_URL": "sqlite:///./test.db",
        "JWT_SECRET_KEY": "test_secret_key_for_testing_only",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "GOOGLE_CLIENT_ID": "test_google_client_id",
        "GOOGLE_CLIENT_SECRET": "test_google_client_secret",
        "MICROSOFT_CLIENT_ID": "test_microsoft_client_id",
        "MICROSOFT_CLIENT_SECRET": "test_microsoft_client_secret",
        "STORAGE_BUCKET_NAME": "test-bucket",
        "GOOGLE_CLOUD_PROJECT": "test-project"
    })
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def async_client(db_session: Session):
    """Create async test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_gcs_client():
    """Mock Google Cloud Storage client."""
    with patch('google.cloud.storage.Client') as mock_client:
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Configure mock blob
        mock_blob.upload_from_file.return_value = None
        mock_blob.upload_from_string.return_value = None
        mock_blob.delete.return_value = None
        mock_blob.generate_signed_url.return_value = "https://example.com/signed_url"
        mock_blob.size = 1024 * 1024
        mock_blob.content_type = "video/mp4"
        mock_blob.time_created = datetime.utcnow()
        mock_blob.updated = datetime.utcnow()
        mock_blob.metadata = {}
        
        yield mock_client


# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file before tests run
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_file = os.path.join(backend_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Pytest configuration
def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Base URL of live server to test against (e.g., http://localhost:8001). If not provided, uses fixture server."
    )
    parser.addoption(
        "--no-cleanup",
        action="store_true",
        default=False,
        help="Don't cleanup extracted frames after test. Also reuse existing frames if present."
    )


@pytest.fixture
def base_url(request):
    """Get base URL from command line"""
    return request.config.getoption("--base-url")


@pytest.fixture
def live_server_mode(base_url):
    """Check if we're in live server mode"""
    return base_url is not None


@pytest.fixture
def no_cleanup(request):
    """Get no-cleanup flag from command line"""
    return request.config.getoption("--no-cleanup")


def pytest_configure(config):
    """Configure pytest markers and environment."""
    # Log environment loading status
    api_keys = ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY']
    found_keys = [key for key in api_keys if os.getenv(key)]
    
    if found_keys:
        print(f"✅ Found API keys: {', '.join(found_keys)}")
    else:
        print("⚠️  WARNING: No AI API keys found in environment")
    
    # Configure markers
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication test"
    )
    config.addinivalue_line(
        "markers", "storage: mark test as storage test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as database test"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring AI API key"
    )