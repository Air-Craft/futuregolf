"""
Integration tests for API endpoints with real database.
These tests use real Neon database.
"""

import pytest
import pytest_asyncio
import uuid
import io
import asyncio
from fastapi import UploadFile, BackgroundTasks
from sqlalchemy import select
from unittest.mock import patch, Mock, AsyncMock

from app.database.config import AsyncSessionLocal, async_engine
from app.models.video_analysis import VideoAnalysis, AnalysisStatus
from app.models.user import User


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_engine():
    """Clean up SQLAlchemy engine after each test to prevent event loop issues"""
    yield
    # Clean up connection pool after test
    from app.database.config import async_engine
    await async_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_user():
    """Create a test user for integration tests"""
    user_id = None
    
    try:
        # Create user
        async with AsyncSessionLocal() as session:
            user = User(
                email=f"api_test_{uuid.uuid4().hex}@example.com",
                hashed_password="hashed_password_test"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            user_id = user.id
        
        yield user_id
        
    finally:
        # Cleanup
        if user_id:
            try:
                async with AsyncSessionLocal() as session:
                    user = await session.get(User, user_id)
                    if user:
                        await session.delete(user)
                        await session.commit()
            except Exception as e:
                # Ignore cleanup errors
                pass


@pytest.fixture
def mock_storage():
    """Mock storage service for integration tests"""
    with patch('app.api.analysis.get_storage_service') as mock:
        storage = Mock()
        storage.config = Mock()
        storage.config.bucket_name = "test-bucket"
        storage.upload_video = AsyncMock(return_value={
            "success": True,
            "blob_name": "processing/test_uuid_original",
            "public_url": "https://storage.googleapis.com/test-bucket/processing/test_uuid_original"
        })
        storage.move_file = AsyncMock(return_value=True)
        mock.return_value = storage
        yield storage


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for integration tests"""
    with patch('app.api.analysis.AnalysisOrchestrator') as MockOrch:
        orchestrator = Mock()
        orchestrator.analyze_video_background = AsyncMock()
        MockOrch.return_value = orchestrator
        yield orchestrator


@pytest.mark.integration
@pytest.mark.requires_neon
@pytest.mark.asyncio
async def test_create_analysis_database_entry(test_user):
    """Test that create endpoint actually creates database entry"""
    from app.api.analysis import create_analysis
    
    # Call the endpoint function directly
    async with AsyncSessionLocal() as db:
        result = await create_analysis(user_id=test_user, db=db)
        
        assert "uuid" in result
        analysis_uuid = uuid.UUID(result["uuid"])
        
        # Verify in database
        query_result = await db.execute(
            select(VideoAnalysis).filter(VideoAnalysis.uuid == analysis_uuid)
        )
        analysis = query_result.scalar_one_or_none()
        
        assert analysis is not None
        assert analysis.status == AnalysisStatus.PENDING
        assert analysis.user_id == test_user
        
        # Cleanup
        await db.delete(analysis)
        await db.commit()


@pytest.mark.integration
@pytest.mark.requires_neon
@pytest.mark.asyncio
async def test_upload_video_to_analysis_success(test_user, mock_storage, mock_orchestrator):
    """Test successful video upload to analysis with real database"""
    from app.api.analysis import create_analysis, upload_video_to_analysis
    
    # Create analysis first
    async with AsyncSessionLocal() as db:
        result = await create_analysis(user_id=test_user, db=db)
        analysis_uuid = result["uuid"]
        
        # Create mock file with proper async support
        file_content = b"fake video content"
        file_io = io.BytesIO(file_content)
        file = UploadFile(
            filename="test.mp4",
            file=file_io,
            size=len(file_content)
        )
        
        # Create background tasks
        background_tasks = BackgroundTasks()
        
        # Upload video
        upload_result = await upload_video_to_analysis(
            uuid=analysis_uuid,
            background_tasks=background_tasks,
            file=file,
            db=db
        )
        
        assert upload_result["success"] is True
        assert upload_result["uuid"] == analysis_uuid
        assert upload_result["status"] == AnalysisStatus.PROCESSING.value
        
        # Verify database update
        query_result = await db.execute(
            select(VideoAnalysis).filter(VideoAnalysis.uuid == uuid.UUID(analysis_uuid))
        )
        analysis = query_result.scalar_one_or_none()
        
        assert analysis.status == AnalysisStatus.PROCESSING
        assert analysis.originalVideoURL is not None
        
        # Cleanup
        await db.delete(analysis)
        await db.commit()


@pytest.mark.integration
@pytest.mark.requires_neon
@pytest.mark.asyncio
async def test_get_analysis_complete_status(test_user):
    """Test GET /analysis/{uuid} with completed analysis"""
    from app.api.analysis import get_analysis
    
    # Create completed analysis
    async with AsyncSessionLocal() as db:
        analysis = VideoAnalysis(
            user_id=test_user,
            status=AnalysisStatus.COMPLETED,
            uuid=uuid.uuid4(),
            analysisJSON={"result": "test"},
            video_duration=10.5
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        # Get analysis
        result = await get_analysis(str(analysis.uuid), db=db)
        
        assert result["uuid"] == str(analysis.uuid)
        assert result["status"] == "COMPLETED"
        assert result["analysisJSON"] == {"result": "test"}
        
        # Cleanup
        await db.delete(analysis)
        await db.commit()


@pytest.mark.integration
@pytest.mark.requires_neon
@pytest.mark.asyncio
async def test_get_analysis_failed_status(test_user):
    """Test GET /analysis/{uuid} with failed analysis"""
    from app.api.analysis import get_analysis
    
    # Create failed analysis
    async with AsyncSessionLocal() as db:
        analysis = VideoAnalysis(
            user_id=test_user,
            status=AnalysisStatus.FAILED,
            uuid=uuid.uuid4(),
            errorDescription="Test error"
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        # Get analysis
        result = await get_analysis(str(analysis.uuid), db=db)
        
        assert result["uuid"] == str(analysis.uuid)
        assert result["status"] == "FAILED"
        assert result["errorDescription"] == "Test error"
        
        # Cleanup
        await db.delete(analysis)
        await db.commit()


@pytest.mark.integration
@pytest.mark.requires_neon
@pytest.mark.asyncio
async def test_get_analysis_processing_status(test_user):
    """Test GET /analysis/{uuid} with processing analysis"""
    from app.api.analysis import get_analysis
    
    # Create processing analysis
    async with AsyncSessionLocal() as db:
        analysis = VideoAnalysis(
            user_id=test_user,
            status=AnalysisStatus.PROCESSING,
            uuid=uuid.uuid4()
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        # Get analysis
        result = await get_analysis(str(analysis.uuid), db=db)
        
        assert result["uuid"] == str(analysis.uuid)
        assert result["status"] == "PROCESSING"
        assert result["message"] == "Analysis in progress"
        
        # Cleanup
        await db.delete(analysis)
        await db.commit()