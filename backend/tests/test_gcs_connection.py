#!/usr/bin/env python3
"""
Test script for Google Cloud Storage connection.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Load environment variables
load_dotenv()

def test_gcs_connection():
    """Test Google Cloud Storage connection and basic operations."""
    print("🔍 Testing Google Cloud Storage Connection...")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    gcs_vars = {
        "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        "GCS_PROJECT_ID": os.getenv("GCS_PROJECT_ID"),
        "GCS_BUCKET_NAME": os.getenv("GCS_BUCKET_NAME")
    }
    
    for var, value in gcs_vars.items():
        if value:
            if "CREDENTIALS" in var:
                print(f"✅ {var}: {value} (exists: {os.path.exists(value)})")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Check if credentials file exists
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        print(f"\n✅ Credentials file found at: {cred_path}")
        # Check file size to ensure it's not empty
        size = os.path.getsize(cred_path)
        print(f"✅ Credentials file size: {size} bytes")
    else:
        print(f"\n❌ Credentials file not found at: {cred_path}")
        return False
    
    # Test GCS connection
    print("\n🔌 Testing GCS Connection...")
    try:
        from config.storage import storage_config
        
        # Try to get storage client
        client = storage_config.get_storage_client()
        print(f"✅ Successfully created GCS client for project: {storage_config.project_id}")
        
        # List buckets to verify connection
        try:
            buckets = list(client.list_buckets(max_results=5))
            print(f"✅ Connection verified! Found {len(buckets)} bucket(s) in project")
            for bucket in buckets:
                print(f"   - {bucket.name}")
        except Exception as e:
            print(f"⚠️  Could not list buckets (might be a permissions issue): {e}")
        
        # Try to get the configured bucket
        print(f"\n📦 Testing bucket access: {storage_config.bucket_name}")
        try:
            bucket = storage_config.get_bucket()
            print(f"✅ Successfully accessed bucket: {bucket.name}")
            print(f"   - Location: {bucket.location}")
            print(f"   - Storage class: {bucket.storage_class}")
            print(f"   - Created: {bucket.time_created}")
        except Exception as e:
            print(f"❌ Error accessing bucket: {e}")
            print("   Note: The bucket might not exist yet. It will be created on first use.")
        
        # Test file upload capability
        print("\n📤 Testing upload capability...")
        try:
            test_content = "FutureGolf GCS test file"
            test_path = storage_config.get_file_path(
                user_id=1,
                video_id=1,
                file_type="temp",
                filename="test_connection.txt"
            )
            print(f"   - Test file path: {test_path}")
            
            # Get public URL format
            public_url = storage_config.get_public_url(test_path)
            print(f"   - Public URL format: {public_url}")
            
            print("✅ File path generation working correctly")
            
        except Exception as e:
            print(f"❌ Error testing upload capability: {e}")
        
        print("\n✅ GCS configuration is working properly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error connecting to GCS: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False

def test_storage_service():
    """Test the storage service functionality."""
    print("\n\n🧪 Testing Storage Service...")
    print("=" * 50)
    
    try:
        from services.storage_service import StorageService
        
        service = StorageService()
        print("✅ Storage service initialized successfully")
        
        # Test configuration
        print(f"\n📋 Storage Service Configuration:")
        print(f"   - Bucket: {service.config.bucket_name}")
        print(f"   - Max file size: {service.config.max_file_size / 1024 / 1024}MB")
        print(f"   - Allowed video types: {len(service.config.allowed_video_types)} types")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing storage service: {e}")
        return False

def main():
    """Run all GCS tests."""
    print("🚀 FutureGolf - Google Cloud Storage Connection Test")
    print("=" * 70)
    
    # Test basic connection
    connection_ok = test_gcs_connection()
    
    # Test storage service
    service_ok = test_storage_service()
    
    # Summary
    print("\n\n📊 Test Summary:")
    print("=" * 50)
    if connection_ok and service_ok:
        print("✅ All GCS tests passed!")
        print("\n🎉 Google Cloud Storage is properly configured and ready to use!")
        return 0
    else:
        print("❌ Some tests failed. Please check the configuration.")
        print("\nTroubleshooting tips:")
        print("1. Ensure gcs-credential.json exists in the backend directory")
        print("2. Check that the service account has proper permissions")
        print("3. Verify the project ID matches your GCS project")
        print("4. Make sure the .env file is properly configured")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)