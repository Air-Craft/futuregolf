"""
E2E tests for complete analysis flow.
Tests the full user journey: create -> upload -> poll -> complete.
Uses real server, database, and services.
"""

import pytest
import requests
import time
import uuid
import os
import sys

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)


def test_health_check(api_v1_url):
    """Test that server is running and healthy"""
    response = requests.get(f"{api_v1_url}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_create_analysis(api_v1_url):
    """Test creating a new analysis entry"""
    response = requests.post(
        f"{api_v1_url}/analysis/create",
        json={"user_id": 1}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "uuid" in data
    
    # Verify UUID is valid
    try:
        uuid.UUID(data["uuid"])
    except ValueError:
        pytest.fail("Invalid UUID returned")


def test_upload_video_to_analysis(api_v1_url):
    """Test uploading a video to an analysis"""
    # First create an analysis
    create_response = requests.post(
        f"{api_v1_url}/analysis/create",
        json={"user_id": 1}
    )
    assert create_response.status_code == 200
    analysis_uuid = create_response.json()["uuid"]
    
    # Create a test video file
    test_video_content = b"Test video content for E2E test"
    
    # Upload video to the analysis
    files = {
        "file": ("test_video.mp4", test_video_content, "video/mp4")
    }
    
    upload_response = requests.put(
        f"{api_v1_url}/analysis/{analysis_uuid}/video",
        files=files
    )
    
    # Note: This might fail if GCS is not configured, which is expected
    # We're testing the API contract, not the actual storage
    if upload_response.status_code == 500:
        # Check if it's a storage error (expected if GCS not configured)
        error_detail = upload_response.json().get("detail", "")
        if "storage" in error_detail.lower() or "upload" in error_detail.lower():
            pytest.skip("GCS not configured for E2E test")
    else:
        assert upload_response.status_code == 200
        data = upload_response.json()
        assert data["success"] is True
        assert data["uuid"] == analysis_uuid
        assert data["status"] in ["PENDING", "PROCESSING"]


def test_get_analysis_status(api_v1_url):
    """Test getting analysis status"""
    # Create an analysis
    create_response = requests.post(
        f"{api_v1_url}/analysis/create",
        json={"user_id": 1}
    )
    assert create_response.status_code == 200
    analysis_uuid = create_response.json()["uuid"]
    
    # Get analysis status
    get_response = requests.get(f"{api_v1_url}/analysis/{analysis_uuid}")
    
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["uuid"] == analysis_uuid
    assert data["status"] == "PENDING"
    assert "created_at" in data


def test_invalid_uuid_handling(api_v1_url):
    """Test that invalid UUIDs are handled properly"""
    # Test with invalid UUID format
    response = requests.get(f"{api_v1_url}/analysis/not-a-uuid")
    assert response.status_code == 400
    assert "Invalid UUID" in response.json()["detail"]
    
    # Test with non-existent UUID
    fake_uuid = str(uuid.uuid4())
    response = requests.get(f"{api_v1_url}/analysis/{fake_uuid}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_complete_flow_simulation(api_v1_url):
    """
    Test complete flow simulation (without actual video processing).
    This simulates what a client app would do:
    1. Create analysis
    2. Check status (should be awaiting_video)
    3. Upload video (if GCS available)
    4. Poll for status
    """
    # Step 1: Create analysis
    create_response = requests.post(
        f"{api_v1_url}/analysis/create",
        json={"user_id": 1}
    )
    assert create_response.status_code == 200
    analysis_uuid = create_response.json()["uuid"]
    print(f"Created analysis: {analysis_uuid}")
    
    # Step 2: Check initial status
    status_response = requests.get(f"{api_v1_url}/analysis/{analysis_uuid}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "PENDING"
    print(f"Initial status: {status_data['status']}")
    
    # Step 3: Try to upload video (might fail if GCS not configured)
    test_video_content = b"Test video content"
    files = {"file": ("test.mp4", test_video_content, "video/mp4")}
    
    upload_response = requests.put(
        f"{api_v1_url}/analysis/{analysis_uuid}/video",
        files=files
    )
    
    if upload_response.status_code == 500:
        print("Upload failed (expected if GCS not configured)")
        # Still check that status remains awaiting_video
        status_response = requests.get(f"{api_v1_url}/analysis/{analysis_uuid}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "PENDING"
    else:
        print("Upload succeeded")
        assert upload_response.status_code == 200
        
        # Step 4: Poll for status changes (simulate client polling)
        max_polls = 5
        poll_interval = 2  # seconds
        
        for i in range(max_polls):
            time.sleep(poll_interval)
            
            poll_response = requests.get(f"{api_v1_url}/analysis/{analysis_uuid}")
            assert poll_response.status_code == 200
            
            current_status = poll_response.json()["status"]
            print(f"Poll {i+1}: Status = {current_status}")
            
            # Status should progress from PENDING -> PROCESSING -> COMPLETED/FAILED
            if current_status in ["COMPLETED", "FAILED"]:
                print(f"Analysis finished with status: {current_status}")
                
                # If complete, should have analysis data
                if current_status == "COMPLETED":
                    assert "analysisJSON" in poll_response.json()
                # If failed, should have error description
                elif current_status == "FAILED":
                    assert "errorDescription" in poll_response.json()
                break
        
        # Final verification
        final_response = requests.get(f"{api_v1_url}/analysis/{analysis_uuid}")
        assert final_response.status_code == 200
        print(f"Final analysis state: {final_response.json()}")


def test_concurrent_analyses(api_v1_url):
    """Test that multiple analyses can be created and managed concurrently"""
    # Create multiple analyses
    analysis_uuids = []
    
    for i in range(3):
        response = requests.post(
            f"{api_v1_url}/analysis/create",
            json={"user_id": i + 1}
        )
        assert response.status_code == 200
        analysis_uuids.append(response.json()["uuid"])
    
    print(f"Created {len(analysis_uuids)} analyses")
    
    # Verify all can be retrieved
    for analysis_uuid in analysis_uuids:
        response = requests.get(f"{api_v1_url}/analysis/{analysis_uuid}")
        assert response.status_code == 200
        assert response.json()["uuid"] == analysis_uuid
        assert response.json()["status"] == "PENDING"
    
    print("All analyses successfully created and retrievable")