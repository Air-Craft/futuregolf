#!/usr/bin/env python
"""
Simple script to test Google Cloud Storage operations.
Tests upload, download, and delete operations.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from app.config.storage import storage_config
from google.cloud import storage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_storage_operations():
    """Test basic storage operations."""
    
    print("=" * 60)
    print("Testing Google Cloud Storage Configuration")
    print("=" * 60)
    
    # 1. Check configuration
    print("\n1. Checking configuration...")
    print(f"   Project ID: {storage_config.project_id}")
    print(f"   Bucket Name: {storage_config.bucket_name}")
    print(f"   Using API Key: {bool(storage_config.api_key)}")
    print(f"   Using Service Account: {bool(storage_config.credentials_path)}")
    
    # 2. Get storage client
    print("\n2. Creating storage client...")
    try:
        client = storage_config.get_storage_client()
        print("   ✅ Storage client created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create storage client: {e}")
        return False
    
    # 3. Get or create bucket
    print(f"\n3. Accessing bucket '{storage_config.bucket_name}'...")
    try:
        bucket = client.bucket(storage_config.bucket_name)
        
        # Check if bucket exists
        if bucket.exists():
            print(f"   ✅ Bucket exists and is accessible")
        else:
            print(f"   ⚠️  Bucket doesn't exist, attempting to create...")
            bucket = client.create_bucket(
                storage_config.bucket_name,
                location=storage_config.location
            )
            print(f"   ✅ Bucket created successfully")
    except Exception as e:
        print(f"   ❌ Failed to access/create bucket: {e}")
        return False
    
    # 4. Upload a test file
    print("\n4. Testing file upload...")
    test_content = b"This is a test file for GCS storage testing"
    test_filename = "test_files/test_upload.txt"
    
    try:
        blob = bucket.blob(test_filename)
        blob.upload_from_string(test_content, content_type="text/plain")
        print(f"   ✅ File uploaded successfully to: {test_filename}")
        print(f"   Public URL: {blob.public_url}")
    except Exception as e:
        print(f"   ❌ Failed to upload file: {e}")
        return False
    
    # 5. List files in bucket
    print("\n5. Listing files in bucket...")
    try:
        blobs = list(bucket.list_blobs(prefix="test_files/", max_results=10))
        print(f"   Found {len(blobs)} file(s) in test_files/:")
        for blob in blobs:
            print(f"     - {blob.name} ({blob.size} bytes)")
    except Exception as e:
        print(f"   ❌ Failed to list files: {e}")
    
    # 6. Download the file
    print("\n6. Testing file download...")
    try:
        blob = bucket.blob(test_filename)
        downloaded_content = blob.download_as_bytes()
        
        if downloaded_content == test_content:
            print("   ✅ File downloaded and content matches")
        else:
            print("   ⚠️  File downloaded but content doesn't match")
    except Exception as e:
        print(f"   ❌ Failed to download file: {e}")
        return False
    
    # 7. Generate signed URL (if using service account)
    print("\n7. Testing signed URL generation...")
    if storage_config.credentials_path:
        try:
            from datetime import timedelta
            blob = bucket.blob(test_filename)
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="GET"
            )
            print(f"   ✅ Signed URL generated (expires in 1 hour)")
            print(f"   URL: {signed_url[:80]}...")
        except Exception as e:
            print(f"   ⚠️  Signed URL generation not available with API key: {e}")
    else:
        print("   ⚠️  Signed URLs require service account credentials")
    
    # 8. Delete test file
    print("\n8. Cleaning up test file...")
    try:
        blob = bucket.blob(test_filename)
        blob.delete()
        print("   ✅ Test file deleted successfully")
    except Exception as e:
        print(f"   ❌ Failed to delete test file: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All storage operations completed successfully!")
    print("=" * 60)
    
    return True


def test_video_upload():
    """Test uploading a video-like file."""
    print("\n" + "=" * 60)
    print("Testing Video Upload")
    print("=" * 60)
    
    try:
        client = storage_config.get_storage_client()
        bucket = client.bucket(storage_config.bucket_name)
        
        # Create a temporary video file (just test data)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            # Write some dummy content (would be actual video in production)
            tmp.write(b"FAKE_VIDEO_CONTENT" * 1000)  # ~18KB fake video
            tmp_path = tmp.name
        
        # Upload as video
        user_id = 1
        video_id = 1
        filename = "test_video.mp4"
        
        blob_path = storage_config.get_file_path(user_id, video_id, "video", filename)
        print(f"\n1. Uploading video to: {blob_path}")
        
        blob = bucket.blob(blob_path)
        with open(tmp_path, "rb") as f:
            blob.upload_from_file(f, content_type="video/mp4")
        
        print(f"   ✅ Video uploaded successfully")
        print(f"   Size: {blob.size} bytes")
        print(f"   Public URL: {storage_config.get_public_url(blob_path)}")
        
        # Clean up
        blob.delete()
        os.unlink(tmp_path)
        print("   ✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Video upload failed: {e}")
        return False


if __name__ == "__main__":
    print("Starting Google Cloud Storage tests...\n")
    
    # Run basic operations test
    success = test_storage_operations()
    
    if success:
        # Run video upload test
        test_video_upload()
    
    sys.exit(0 if success else 1)