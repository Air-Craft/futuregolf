"""
Unit tests for StorageService move_file method.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.services.storage_service import StorageService


@pytest.fixture
def mock_bucket():
    """Mock GCS bucket"""
    bucket = Mock()
    return bucket


@pytest.fixture
def storage_service(mock_bucket):
    """Create storage service with mocked bucket"""
    with patch('app.services.storage_service.storage_config') as mock_config:
        mock_config.get_storage_client.return_value = Mock()
        mock_config.get_bucket.return_value = mock_bucket
        service = StorageService()
        service.bucket = mock_bucket
        return service


@pytest.mark.unit
@pytest.mark.asyncio
async def test_move_file_success(storage_service, mock_bucket):
    """Test successful file move"""
    source_blob_name = "processing/test_video.mp4"
    dest_blob_name = "processed/test_video.mp4"
    
    # Mock source blob
    source_blob = Mock()
    source_blob.exists.return_value = True
    source_blob.content_type = "video/mp4"
    source_blob.download_as_bytes.return_value = b"video content"
    source_blob.metadata = {"user_id": "1", "video_id": "123"}
    
    # Mock dest blob
    dest_blob = Mock()
    
    # Setup bucket mocks
    def blob_side_effect(name):
        if name == source_blob_name:
            return source_blob
        elif name == dest_blob_name:
            return dest_blob
        return Mock()
    
    mock_bucket.blob.side_effect = blob_side_effect
    
    # Call method
    result = await storage_service.move_file(source_blob_name, dest_blob_name)
    
    # Verify success
    assert result is True
    
    # Verify operations
    source_blob.exists.assert_called_once()
    source_blob.download_as_bytes.assert_called_once()
    dest_blob.upload_from_string.assert_called_once_with(
        b"video content",
        content_type="video/mp4"
    )
    dest_blob.patch.assert_called_once()
    source_blob.delete.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_move_file_source_not_found(storage_service, mock_bucket):
    """Test move file when source doesn't exist"""
    source_blob_name = "processing/missing_video.mp4"
    dest_blob_name = "processed/test_video.mp4"
    
    # Mock source blob that doesn't exist
    source_blob = Mock()
    source_blob.exists.return_value = False
    
    mock_bucket.blob.return_value = source_blob
    
    # Call method
    result = await storage_service.move_file(source_blob_name, dest_blob_name)
    
    # Verify failure
    assert result is False
    
    # Verify no operations after exists check
    source_blob.download_as_bytes.assert_not_called()
    source_blob.delete.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_move_file_with_exception(storage_service, mock_bucket):
    """Test move file handles exceptions gracefully"""
    source_blob_name = "processing/test_video.mp4"
    dest_blob_name = "processed/test_video.mp4"
    
    # Mock source blob that throws exception
    source_blob = Mock()
    source_blob.exists.return_value = True
    source_blob.download_as_bytes.side_effect = Exception("Download failed")
    
    mock_bucket.blob.return_value = source_blob
    
    # Call method
    result = await storage_service.move_file(source_blob_name, dest_blob_name)
    
    # Verify failure
    assert result is False
    
    # Verify delete not called on error
    source_blob.delete.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_move_file_without_metadata(storage_service, mock_bucket):
    """Test move file when source has no metadata"""
    source_blob_name = "processing/test_video.mp4"
    dest_blob_name = "processed/test_video.mp4"
    
    # Mock source blob without metadata
    source_blob = Mock()
    source_blob.exists.return_value = True
    source_blob.content_type = "video/mp4"
    source_blob.download_as_bytes.return_value = b"video content"
    source_blob.metadata = None
    
    # Mock dest blob
    dest_blob = Mock()
    
    # Setup bucket mocks
    def blob_side_effect(name):
        if name == source_blob_name:
            return source_blob
        elif name == dest_blob_name:
            return dest_blob
        return Mock()
    
    mock_bucket.blob.side_effect = blob_side_effect
    
    # Call method
    result = await storage_service.move_file(source_blob_name, dest_blob_name)
    
    # Verify success
    assert result is True
    
    # Verify metadata patch not called
    dest_blob.patch.assert_not_called()
    
    # Verify other operations
    source_blob.delete.assert_called_once()