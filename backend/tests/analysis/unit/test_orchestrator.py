"""
Unit tests for AnalysisOrchestrator service.
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import tempfile
import os

# Add backend to path
import sys
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.services.video_analysis_service import AnalysisOrchestrator
from app.models.video_analysis import VideoAnalysis, AnalysisStatus


@pytest.fixture
def mock_storage_service():
    """Mock storage service"""
    mock = Mock()
    mock.bucket = Mock()
    mock.config = Mock()
    mock.config.bucket_name = "test-bucket"
    mock.move_file = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_vision_service():
    """Mock vision service"""
    mock = Mock()
    mock.download_video_from_storage = AsyncMock(return_value="/tmp/test_video.mp4")
    mock.analyze_video_file = AsyncMock(return_value={
        "swing_analysis": {
            "overall_assessment": "Good swing",
            "score": 85
        },
        "_metadata": {
            "video_duration": 10.5,
            "analysis_duration": 2.3
        }
    })
    return mock


@pytest.fixture
def orchestrator(mock_storage_service, mock_vision_service):
    """Create orchestrator with mocked dependencies"""
    with patch('app.services.video_analysis_service.get_storage_service', return_value=mock_storage_service):
        with patch('app.services.video_analysis_service.CleanVideoAnalysisService') as MockVision:
            MockVision.return_value = mock_vision_service
            orch = AnalysisOrchestrator()
            orch.storage_service = mock_storage_service
            orch.vision_service = mock_vision_service
            return orch


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_analysis_entry(orchestrator):
    """Test creating a new analysis entry"""
    with patch('app.services.video_analysis_service.AsyncSessionLocal') as mock_session_class:
        # Setup mock session
        mock_db = AsyncMock()
        mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_class.return_value.__aexit__ = AsyncMock()
        
        # Call method
        result = await orchestrator.create_analysis_entry(user_id=1)
        
        # Verify UUID returned
        assert result is not None
        assert isinstance(result, str)
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_attach_video_to_analysis(orchestrator):
    """Test attaching video to existing analysis"""
    test_uuid = str(uuid.uuid4())
    
    with patch('app.services.video_analysis_service.AsyncSessionLocal') as mock_session_class:
        # Setup mock session
        mock_db = AsyncMock()
        mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_class.return_value.__aexit__ = AsyncMock()
        
        # Mock analysis object
        mock_analysis = Mock()
        mock_analysis.uuid = uuid.UUID(test_uuid)
        
        # Create async mock for the chain execute().scalar_one_or_none()
        mock_execute_result = AsyncMock()
        mock_execute_result.scalar_one_or_none = Mock(return_value=mock_analysis)
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # Call method
        result = await orchestrator.attach_video_to_analysis(
            test_uuid, 
            "processing/test_video.mp4"
        )
        
        # Verify success
        assert result is True
        assert mock_analysis.originalVideoURL == "processing/test_video.mp4"
        assert mock_analysis.status == AnalysisStatus.PROCESSING
        mock_db.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_attach_video_to_analysis_not_found(orchestrator):
    """Test attaching video when analysis not found"""
    test_uuid = str(uuid.uuid4())
    
    with patch('app.services.video_analysis_service.AsyncSessionLocal') as mock_session_class:
        # Setup mock session
        mock_db = AsyncMock()
        mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_class.return_value.__aexit__ = AsyncMock()
        
        # Mock no analysis found
        mock_execute_result = AsyncMock()
        mock_execute_result.scalar_one_or_none = Mock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_execute_result)
        
        # Call method
        result = await orchestrator.attach_video_to_analysis(
            test_uuid, 
            "processing/test_video.mp4"
        )
        
        # Verify failure
        assert result is False
        mock_db.commit.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_video_background_success(orchestrator):
    """Test successful background video analysis"""
    test_uuid = str(uuid.uuid4())
    
    with patch('app.services.video_analysis_service.AsyncSessionLocal') as mock_session_class:
        # We need multiple session instances for the multiple async with blocks
        
        # First session - get analysis and update status
        mock_db1 = AsyncMock()
        mock_analysis1 = Mock()
        mock_analysis1.uuid = uuid.UUID(test_uuid)
        mock_analysis1.originalVideoURL = "gcs://test-bucket/processing/test_video.mp4"
        mock_analysis1.user_id = 1
        mock_analysis1.id = 123
        
        mock_execute_result1 = AsyncMock()
        mock_execute_result1.scalar_one_or_none = Mock(return_value=mock_analysis1)
        mock_db1.execute = AsyncMock(return_value=mock_execute_result1)
        
        # Second session - update with results
        mock_db2 = AsyncMock()
        mock_analysis2 = Mock()
        mock_analysis2.uuid = uuid.UUID(test_uuid)
        mock_db2.get = AsyncMock(return_value=mock_analysis2)
        
        # Create separate mock session instances
        mock_session1 = AsyncMock()
        mock_session1.__aenter__ = AsyncMock(return_value=mock_db1)
        mock_session1.__aexit__ = AsyncMock()
        
        mock_session2 = AsyncMock()
        mock_session2.__aenter__ = AsyncMock(return_value=mock_db2)
        mock_session2.__aexit__ = AsyncMock()
        
        # Use side_effect to return different sessions on each call
        mock_session_class.side_effect = [mock_session1, mock_session2]
        
        # Call method
        await orchestrator.analyze_video_background(test_uuid)
        
        # Verify status updates
        assert mock_analysis1.status == AnalysisStatus.PROCESSING
        assert mock_analysis2.status == AnalysisStatus.COMPLETED
        assert mock_analysis2.analysisJSON is not None
        assert mock_analysis2.video_duration == 10.5
        
        # Verify storage operations
        orchestrator.vision_service.download_video_from_storage.assert_called_once()
        orchestrator.vision_service.analyze_video_file.assert_called_once()
        orchestrator.storage_service.move_file.assert_called_once_with(
            "processing/test_video.mp4",
            f"processed/{test_uuid}_original"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_video_background_analysis_failure(orchestrator):
    """Test background analysis when video analysis fails"""
    test_uuid = str(uuid.uuid4())
    
    # Make analysis fail
    orchestrator.vision_service.analyze_video_file = AsyncMock(
        side_effect=Exception("Analysis failed")
    )
    
    with patch('app.services.video_analysis_service.AsyncSessionLocal') as mock_session_class:
        # First session - get analysis and update status
        mock_db1 = AsyncMock()
        mock_analysis1 = Mock()
        mock_analysis1.uuid = uuid.UUID(test_uuid)
        mock_analysis1.originalVideoURL = "gcs://test-bucket/processing/test_video.mp4"
        mock_analysis1.user_id = 1
        mock_analysis1.id = 123
        
        mock_execute_result1 = AsyncMock()
        mock_execute_result1.scalar_one_or_none = Mock(return_value=mock_analysis1)
        mock_db1.execute = AsyncMock(return_value=mock_execute_result1)
        
        # Second session - update with error (for error path)
        mock_db2 = AsyncMock()
        mock_execute_result2 = AsyncMock()
        mock_analysis2 = Mock()
        mock_execute_result2.scalar_one_or_none = Mock(return_value=mock_analysis2)
        mock_db2.execute = AsyncMock(return_value=mock_execute_result2)
        
        # Create separate mock session instances
        mock_session1 = AsyncMock()
        mock_session1.__aenter__ = AsyncMock(return_value=mock_db1)
        mock_session1.__aexit__ = AsyncMock()
        
        mock_session2 = AsyncMock()
        mock_session2.__aenter__ = AsyncMock(return_value=mock_db2)
        mock_session2.__aexit__ = AsyncMock()
        
        # Use side_effect to return different sessions on each call
        mock_session_class.side_effect = [mock_session1, mock_session2]
        
        # Call method
        await orchestrator.analyze_video_background(test_uuid)
        
        # Verify error handling
        assert mock_analysis2.status == AnalysisStatus.FAILED
        assert "Analysis failed" in mock_analysis2.errorDescription
        assert mock_analysis2.processing_completed_at is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_video_background_temp_file_cleanup(orchestrator):
    """Test that temporary files are cleaned up after analysis"""
    test_uuid = str(uuid.uuid4())
    temp_path = "/tmp/test_video_temp.mp4"
    
    # Create a real temp file to test cleanup
    with open(temp_path, 'w') as f:
        f.write("test")
    
    orchestrator.vision_service.download_video_from_storage = AsyncMock(return_value=temp_path)
    
    with patch('app.services.video_analysis_service.AsyncSessionLocal') as mock_session_class:
        # First session - get analysis and update status
        mock_db1 = AsyncMock()
        mock_analysis1 = Mock()
        mock_analysis1.uuid = uuid.UUID(test_uuid)
        mock_analysis1.originalVideoURL = "gcs://test-bucket/processing/test_video.mp4"
        mock_analysis1.user_id = 1
        mock_analysis1.id = 123
        
        mock_execute_result1 = AsyncMock()
        mock_execute_result1.scalar_one_or_none = Mock(return_value=mock_analysis1)
        mock_db1.execute = AsyncMock(return_value=mock_execute_result1)
        
        # Second session - update with results
        mock_db2 = AsyncMock()
        mock_analysis2 = Mock()
        mock_db2.get = AsyncMock(return_value=mock_analysis2)
        
        # Create separate mock session instances
        mock_session1 = AsyncMock()
        mock_session1.__aenter__ = AsyncMock(return_value=mock_db1)
        mock_session1.__aexit__ = AsyncMock()
        
        mock_session2 = AsyncMock()
        mock_session2.__aenter__ = AsyncMock(return_value=mock_db2)
        mock_session2.__aexit__ = AsyncMock()
        
        # Use side_effect to return different sessions on each call
        mock_session_class.side_effect = [mock_session1, mock_session2]
        
        # Call method
        await orchestrator.analyze_video_background(test_uuid)
        
        # Verify temp file was cleaned up
        assert not os.path.exists(temp_path)