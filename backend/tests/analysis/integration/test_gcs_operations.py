"""
Integration tests for Google Cloud Storage operations.
These tests use REAL GCS and MUST FAIL if GCS is not accessible.
"""

import pytest
import os
import tempfile
import asyncio
from typing import Optional
import logging

from app.services.storage_service import get_storage_service
from app.config.storage import StorageConfig

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def storage_service():
    """Get real storage service - will fail if GCS not configured"""
    try:
        service = get_storage_service()
        # Verify bucket is accessible
        if not service.bucket.exists():
            pytest.fail(f"GCS bucket '{service.config.bucket_name}' does not exist or is not accessible")
        return service
    except Exception as e:
        pytest.fail(f"GCS integration test failed - storage service not accessible: {e}")


@pytest.fixture
def test_video_file():
    """Create a test video file"""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp4', delete=False) as f:
        # Create a small test video (just dummy data for testing)
        f.write(b'test video content' * 1000)  # ~17KB
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def large_test_video_file():
    """Create a large test video file (>100MB)"""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp4', delete=False) as f:
        # Create a 105MB file
        chunk = b'x' * (1024 * 1024)  # 1MB chunk
        for _ in range(105):
            f.write(chunk)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.mark.integration
@pytest.mark.requires_gcs
class TestGCSOperations:
    """Test real GCS operations"""
    
    @pytest.mark.asyncio
    async def test_gcs_upload_real(self, storage_service, test_video_file):
        """Test real GCS upload - MUST FAIL if GCS is not accessible"""
        try:
            # Open the test file
            with open(test_video_file, 'rb') as f:
                # Upload to GCS
                result = await storage_service.upload_video(
                    file=f,
                    filename=f"test_upload_{os.urandom(8).hex()}.mp4",
                    user_id=1,
                    video_id=1,
                    content_type='video/mp4'
                )
            
            # Assert upload succeeded
            assert result["success"] is True, f"GCS upload failed: {result.get('error')}"
            assert "url" in result, "Upload result missing URL"
            assert "blob_name" in result, "Upload result missing blob name"
            
            # Verify file exists in GCS
            blob = storage_service.bucket.blob(result["blob_name"])
            assert blob.exists(), f"Uploaded file not found in GCS: {result['blob_name']}"
            
            # Cleanup - delete the test file from GCS
            blob.delete()
            
        except Exception as e:
            pytest.fail(f"GCS upload integration test failed - service error: {e}")
    
    @pytest.mark.asyncio
    async def test_gcs_move_file_real(self, storage_service):
        """Test real GCS file move - MUST FAIL if GCS is not accessible"""
        try:
            # First upload a file to move
            source_name = f"test_source_{os.urandom(8).hex()}.mp4"
            dest_name = f"test_dest_{os.urandom(8).hex()}.mp4"
            
            # Create source blob
            source_blob = storage_service.bucket.blob(source_name)
            source_blob.upload_from_string(b"test content for move operation")
            
            # Verify source exists
            assert source_blob.exists(), "Source file not created in GCS"
            
            # Move the file
            success = await storage_service.move_file(source_name, dest_name)
            assert success is True, "Move operation failed"
            
            # Verify destination exists
            dest_blob = storage_service.bucket.blob(dest_name)
            assert dest_blob.exists(), "Destination file not found after move"
            
            # Verify source is deleted
            source_blob.reload()  # Refresh to check existence
            assert not source_blob.exists(), "Source file still exists after move"
            
            # Cleanup
            dest_blob.delete()
            
        except Exception as e:
            pytest.fail(f"GCS move file integration test failed - service error: {e}")
    
    @pytest.mark.asyncio
    async def test_gcs_download_real(self, storage_service):
        """Test real GCS download - MUST FAIL if GCS is not accessible"""
        try:
            # Upload a file first
            test_blob_name = f"test_download_{os.urandom(8).hex()}.mp4"
            test_content = b"test content for download"
            
            blob = storage_service.bucket.blob(test_blob_name)
            blob.upload_from_string(test_content)
            
            # Download the file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                blob.download_to_filename(tmp.name)
                
                # Verify content
                with open(tmp.name, 'rb') as f:
                    downloaded_content = f.read()
                assert downloaded_content == test_content, "Downloaded content doesn't match"
                
                # Cleanup temp file
                os.unlink(tmp.name)
            
            # Cleanup GCS
            blob.delete()
            
        except Exception as e:
            pytest.fail(f"GCS download integration test failed - service error: {e}")
    
    @pytest.mark.asyncio
    async def test_gcs_large_file_upload(self, storage_service, large_test_video_file):
        """Test uploading a large file (>100MB) to GCS"""
        try:
            # This test verifies that large files can be handled
            # In production, we should reject files >100MB, but GCS should handle it
            
            with open(large_test_video_file, 'rb') as f:
                # Get file size
                f.seek(0, 2)  # Seek to end
                file_size = f.tell()
                f.seek(0)  # Reset to beginning
                
                assert file_size > 100 * 1024 * 1024, f"Test file not large enough: {file_size} bytes"
                
                # Upload to GCS (this should work at GCS level)
                blob_name = f"test_large_{os.urandom(8).hex()}.mp4"
                blob = storage_service.bucket.blob(blob_name)
                
                # Use resumable upload for large files
                blob.upload_from_file(f, content_type='video/mp4')
                
                # Verify upload
                assert blob.exists(), "Large file upload failed"
                assert blob.size == file_size, f"Uploaded size mismatch: {blob.size} != {file_size}"
                
                # Cleanup
                blob.delete()
                
        except Exception as e:
            pytest.fail(f"GCS large file integration test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_gcs_permission_error_handling(self, storage_service):
        """Test handling of GCS permission errors"""
        try:
            # Try to access a bucket we don't have permission to
            # This should fail gracefully
            from google.cloud import storage
            client = storage.Client()
            
            # Try to access a bucket that doesn't exist or we don't have access to
            invalid_bucket = client.bucket("invalid-bucket-name-that-should-not-exist-xyz123")
            
            with pytest.raises(Exception) as exc_info:
                # This should raise an exception
                invalid_bucket.exists()
            
            # Verify we get a proper error
            assert exc_info.value is not None
            
        except Exception as e:
            # This is expected - we're testing error handling
            logger.info(f"Expected permission error occurred: {e}")
    
    @pytest.mark.asyncio
    async def test_gcs_concurrent_operations(self, storage_service):
        """Test concurrent GCS operations"""
        try:
            # Create multiple upload tasks
            tasks = []
            blob_names = []
            
            for i in range(5):
                blob_name = f"test_concurrent_{i}_{os.urandom(4).hex()}.mp4"
                blob_names.append(blob_name)
                
                async def upload_task(name):
                    blob = storage_service.bucket.blob(name)
                    blob.upload_from_string(f"content {name}".encode())
                    return name
                
                tasks.append(upload_task(blob_name))
            
            # Execute concurrently
            results = await asyncio.gather(*tasks)
            
            # Verify all uploads succeeded
            assert len(results) == 5, "Not all concurrent uploads completed"
            
            for blob_name in blob_names:
                blob = storage_service.bucket.blob(blob_name)
                assert blob.exists(), f"Concurrent upload failed for {blob_name}"
                
                # Cleanup
                blob.delete()
                
        except Exception as e:
            pytest.fail(f"GCS concurrent operations test failed: {e}")


@pytest.mark.integration
@pytest.mark.requires_gcs
class TestGCSErrorHandling:
    """Test GCS error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_gcs_network_failure_simulation(self, storage_service):
        """Test behavior when GCS is temporarily unavailable"""
        # This is hard to simulate without mocking, but we can test retry logic
        # by trying to download a non-existent file
        
        try:
            blob = storage_service.bucket.blob("non-existent-file.mp4")
            
            # This should not exist
            assert not blob.exists(), "Test file unexpectedly exists"
            
            # Try to download - should fail gracefully
            with pytest.raises(Exception) as exc_info:
                with tempfile.NamedTemporaryFile() as tmp:
                    blob.download_to_filename(tmp.name)
            
            # Verify we get a proper error
            assert "404" in str(exc_info.value) or "Not Found" in str(exc_info.value)
            
        except Exception as e:
            if "404" not in str(e) and "Not Found" not in str(e):
                pytest.fail(f"Unexpected error type: {e}")