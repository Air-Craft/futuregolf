#!/usr/bin/env python3
"""
Setup script for Google Cloud Storage integration.
Run this script to initialize the storage bucket and configure lifecycle policies.
"""

import os
import sys
import logging
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from config.storage import storage_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_bucket_if_not_exists():
    """Create the storage bucket if it doesn't exist."""
    try:
        client = storage_config.get_storage_client()
        bucket_name = storage_config.bucket_name
        
        # Check if bucket exists
        try:
            bucket = client.bucket(bucket_name)
            bucket.reload()
            logger.info(f"Bucket '{bucket_name}' already exists")
            return bucket
        except GoogleCloudError:
            logger.info(f"Creating new bucket: {bucket_name}")
            
            # Create bucket
            bucket = client.create_bucket(
                bucket_name,
                location=storage_config.location,
                storage_class=storage_config.default_storage_class
            )
            
            logger.info(f"Bucket '{bucket_name}' created successfully")
            return bucket
            
    except Exception as e:
        logger.error(f"Failed to create bucket: {e}")
        raise


def configure_bucket_cors(bucket):
    """Configure CORS for the bucket to allow web uploads."""
    cors_configuration = [
        {
            "origin": ["http://localhost:3000", "https://futuregolf.app"],
            "method": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "responseHeader": [
                "Content-Type",
                "x-goog-resumable",
                "x-goog-meta-*"
            ],
            "maxAgeSeconds": 3600
        }
    ]
    
    bucket.cors = cors_configuration
    bucket.patch()
    logger.info("CORS configuration applied to bucket")


def configure_bucket_lifecycle(bucket):
    """Configure lifecycle rules for the bucket."""
    lifecycle_rules = [
        {
            "action": {"type": "Delete"},
            "condition": {
                "age": storage_config.auto_delete_temp_days,
                "matchesPrefix": [f"{storage_config.temp_folder}/"]
            }
        },
        {
            "action": {
                "type": "SetStorageClass", 
                "storageClass": storage_config.archive_storage_class
            },
            "condition": {
                "age": storage_config.auto_archive_days,
                "matchesPrefix": [f"{storage_config.video_folder}/"]
            }
        }
    ]
    
    bucket.lifecycle_rules = lifecycle_rules
    bucket.patch()
    logger.info("Lifecycle rules configured for bucket")


def create_folder_structure(bucket):
    """Create folder structure by uploading placeholder files."""
    folders = [
        storage_config.video_folder,
        storage_config.thumbnail_folder,
        storage_config.processed_folder,
        storage_config.temp_folder
    ]
    
    for folder in folders:
        placeholder_name = f"{folder}/.placeholder"
        blob = bucket.blob(placeholder_name)
        
        # Only create if it doesn't exist
        try:
            blob.reload()
            logger.info(f"Folder {folder} already exists")
        except GoogleCloudError:
            blob.upload_from_string(
                "",
                content_type="text/plain"
            )
            logger.info(f"Created folder: {folder}")


def test_bucket_operations(bucket):
    """Test basic bucket operations."""
    try:
        # Test upload
        test_blob_name = f"{storage_config.temp_folder}/test-file.txt"
        test_blob = bucket.blob(test_blob_name)
        test_blob.upload_from_string("Test content", content_type="text/plain")
        logger.info("Test upload successful")
        
        # Test download
        content = test_blob.download_as_text()
        assert content == "Test content"
        logger.info("Test download successful")
        
        # Test delete
        test_blob.delete()
        logger.info("Test delete successful")
        
        logger.info("All bucket operations tested successfully")
        
    except Exception as e:
        logger.error(f"Bucket operations test failed: {e}")
        raise


def main():
    """Main setup function."""
    try:
        logger.info("Starting Google Cloud Storage setup...")
        
        # Validate environment
        if not storage_config.project_id:
            logger.error("GOOGLE_CLOUD_PROJECT_ID not set")
            sys.exit(1)
        
        # Create bucket
        bucket = create_bucket_if_not_exists()
        
        # Configure bucket
        configure_bucket_cors(bucket)
        configure_bucket_lifecycle(bucket)
        
        # Create folder structure
        create_folder_structure(bucket)
        
        # Test operations
        test_bucket_operations(bucket)
        
        logger.info("Google Cloud Storage setup completed successfully!")
        logger.info(f"Bucket name: {storage_config.bucket_name}")
        logger.info(f"Bucket location: {storage_config.location}")
        logger.info(f"Default storage class: {storage_config.default_storage_class}")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()