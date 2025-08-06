"""
Unit tests for analysis API endpoints.
Uses mocked database and external services.
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.main import app
from app.models.video_analysis import AnalysisStatus


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_storage():
    """Mock storage service for unit tests"""
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
    """Mock orchestrator for unit tests"""
    with patch('app.api.analysis.AnalysisOrchestrator') as MockOrch:
        orchestrator = Mock()
        orchestrator.analyze_video_background = AsyncMock()
        orchestrator.create_analysis_entry = AsyncMock(return_value=str(uuid.uuid4()))
        MockOrch.return_value = orchestrator
        yield orchestrator


@pytest.mark.unit
def test_create_analysis_endpoint(client):
    """Test POST /analysis/create endpoint"""
    response = client.post(
        "/api/v1/analysis/create",
        json={"user_id": 1}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "uuid" in data
    assert uuid.UUID(data["uuid"])  # Verify valid UUID


@pytest.mark.unit
def test_upload_video_to_analysis_invalid_uuid(client):
    """Test PUT /analysis/{uuid}/video with invalid UUID"""
    response = client.put(
        "/api/v1/analysis/invalid-uuid/video",
        files={"file": ("test.mp4", b"fake video content", "video/mp4")}
    )
    
    assert response.status_code == 400
    assert "Invalid UUID format" in response.json()["detail"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_video_to_analysis_not_found():
    """Test upload_video_to_analysis when analysis doesn't exist"""
    from app.api.analysis import upload_video_to_analysis
    from fastapi import UploadFile, BackgroundTasks, HTTPException
    import io
    
    fake_uuid = str(uuid.uuid4())
    
    # Mock database session
    mock_db = AsyncMock()
    mock_execute_result = AsyncMock()
    mock_execute_result.scalar_one_or_none = Mock(return_value=None)  # No analysis found
    mock_db.execute = AsyncMock(return_value=mock_execute_result)
    
    # Create mock file
    file = UploadFile(
        filename="test.mp4",
        file=io.BytesIO(b"fake video content")
    )
    
    # Create background tasks
    background_tasks = BackgroundTasks()
    
    # Test that it raises 404
    with pytest.raises(HTTPException) as exc_info:
        await upload_video_to_analysis(
            uuid=fake_uuid,
            background_tasks=background_tasks,
            file=file,
            db=mock_db
        )
    
    assert exc_info.value.status_code == 404
    assert "Analysis not found" in exc_info.value.detail


@pytest.mark.unit
def test_get_analysis_invalid_uuid(client):
    """Test GET /analysis/{uuid} with invalid UUID"""
    response = client.get("/api/v1/analysis/invalid-uuid")
    
    assert response.status_code == 400
    assert "Invalid UUID format" in response.json()["detail"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_analysis_not_found():
    """Test get_analysis when analysis doesn't exist"""
    from app.api.analysis import get_analysis
    from fastapi import HTTPException
    
    fake_uuid = str(uuid.uuid4())
    
    # Mock database session
    mock_db = AsyncMock()
    mock_execute_result = AsyncMock()
    mock_execute_result.scalar_one_or_none = Mock(return_value=None)  # No analysis found
    mock_db.execute = AsyncMock(return_value=mock_execute_result)
    
    # Test that it raises 404
    with pytest.raises(HTTPException) as exc_info:
        await get_analysis(fake_uuid, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Analysis not found" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_analysis_with_mocked_db():
    """Test create_analysis function with mocked database"""
    from app.api.analysis import create_analysis
    
    mock_db = AsyncMock()
    mock_db.add = Mock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.rollback = AsyncMock()
    
    result = await create_analysis(user_id=1, db=mock_db)
    
    assert "uuid" in result
    assert isinstance(result["uuid"], str)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_analysis_with_mocked_db():
    """Test get_analysis function with mocked database"""
    from app.api.analysis import get_analysis
    
    test_uuid = str(uuid.uuid4())
    
    # Mock database session
    mock_db = AsyncMock()
    
    # Mock analysis object
    mock_analysis = Mock()
    mock_analysis.uuid = uuid.UUID(test_uuid)
    mock_analysis.status = AnalysisStatus.COMPLETED
    mock_analysis.analysisJSON = {"test": "result"}
    mock_analysis.video_duration = 10.5
    mock_analysis.errorDescription = None
    
    # Mock execute result
    mock_execute_result = AsyncMock()
    mock_execute_result.scalar_one_or_none = Mock(return_value=mock_analysis)
    mock_db.execute = AsyncMock(return_value=mock_execute_result)
    
    result = await get_analysis(test_uuid, db=mock_db)
    
    assert result["uuid"] == test_uuid
    assert result["status"] == "COMPLETED"
    assert result["analysisJSON"] == {"test": "result"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_video_with_mocked_components(mock_storage):
    """Test upload_video_to_analysis function with all mocked components"""
    from app.api.analysis import upload_video_to_analysis
    from fastapi import UploadFile, BackgroundTasks
    import io
    
    test_uuid = str(uuid.uuid4())
    
    # Mock database session
    mock_db = AsyncMock()
    
    # Mock analysis object
    mock_analysis = Mock()
    mock_analysis.uuid = uuid.UUID(test_uuid)
    mock_analysis.status = AnalysisStatus.PENDING
    mock_analysis.user_id = 1
    
    # Mock execute result
    mock_execute_result = AsyncMock()
    mock_execute_result.scalar_one_or_none = Mock(return_value=mock_analysis)
    mock_db.execute = AsyncMock(return_value=mock_execute_result)
    mock_db.commit = AsyncMock()
    
    # Create mock file
    file_content = b"fake video content"
    file = UploadFile(
        filename="test.mp4",
        file=io.BytesIO(file_content)
    )
    
    # Create background tasks
    background_tasks = BackgroundTasks()
    
    # Mock orchestrator
    with patch('app.api.analysis.orchestrator') as mock_orch:
        mock_orch.analyze_video_background = AsyncMock()
        
        # Upload video
        result = await upload_video_to_analysis(
            uuid=test_uuid,
            background_tasks=background_tasks,
            file=file,
            db=mock_db
        )
        
        assert result["success"] is True
        assert result["uuid"] == test_uuid
        assert result["status"] == AnalysisStatus.PROCESSING.value
        
        # Verify mocks were called
        mock_storage.upload_video.assert_called_once()
        mock_db.commit.assert_called_once()