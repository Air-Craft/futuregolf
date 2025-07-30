"""
Test script for recording endpoints
Tests voice begin signal and swing detection APIs
"""

import requests
import json
import base64
import asyncio
import websockets
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_voice_begin_endpoint():
    """Test the voice begin signal detection endpoint"""
    print("\n=== Testing Voice Begin Signal Endpoint ===")
    
    url = f"{BASE_URL}/api/v1/recording/voice/begin"
    
    test_cases = [
        {
            "transcript": "I'm ready to begin recording",
            "confidence": 0.9,
            "session_id": "test-session-1",
            "expected_ready": True
        },
        {
            "transcript": "let's start recording now",
            "confidence": 0.8,
            "session_id": "test-session-2", 
            "expected_ready": True
        },
        {
            "transcript": "maybe later",
            "confidence": 0.7,
            "session_id": "test-session-3",
            "expected_ready": False
        },
        {
            "transcript": "hello there",
            "confidence": 0.6,
            "session_id": "test-session-4",
            "expected_ready": False
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}: '{test_case['transcript']}'")
        
        payload = {
            "transcript": test_case["transcript"],
            "confidence": test_case["confidence"],
            "session_id": test_case["session_id"]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  Ready to begin: {result['ready_to_begin']}")
                print(f"  Confidence: {result['confidence']:.2f}")
                print(f"  Reason: {result['reason']}")
                
                # Check if result matches expectation
                if result['ready_to_begin'] == test_case['expected_ready']:
                    print("  ✅ Result matches expectation")
                else:
                    print("  ❌ Result doesn't match expectation")
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")

def create_test_image_base64():
    """Create a simple test image as base64"""
    from PIL import Image, ImageDraw
    import io
    
    # Create a simple test image representing a golf swing position
    img = Image.new('RGB', (640, 480), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple stick figure in golf swing position
    # Head
    draw.ellipse([300, 50, 340, 90], fill='black')
    
    # Body
    draw.line([320, 90, 320, 250], fill='black', width=5)
    
    # Arms (swing position)
    draw.line([320, 120, 280, 100], fill='black', width=3)  # Left arm
    draw.line([320, 120, 360, 160], fill='black', width=3)  # Right arm
    
    # Club
    draw.line([280, 100, 250, 80], fill='brown', width=4)
    
    # Legs
    draw.line([320, 250, 300, 350], fill='black', width=4)
    draw.line([320, 250, 340, 350], fill='black', width=4)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=80)
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

def test_swing_detection_endpoint():
    """Test the swing detection endpoint"""
    print("\n=== Testing Swing Detection Endpoint ===")
    
    url = f"{BASE_URL}/api/v1/recording/swing/detect"
    
    # Create test image
    test_image_b64 = create_test_image_base64()
    
    test_cases = [
        {
            "session_id": "swing-test-1",
            "sequence_number": 1,
            "description": "First frame - setup position"
        },
        {
            "session_id": "swing-test-1", 
            "sequence_number": 2,
            "description": "Second frame - backswing"
        },
        {
            "session_id": "swing-test-1",
            "sequence_number": 3, 
            "description": "Third frame - potential complete swing"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}: {test_case['description']}")
        
        payload = {
            "session_id": test_case["session_id"],
            "image_data": test_image_b64,
            "sequence_number": test_case["sequence_number"]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  Swing detected: {result['swing_detected']}")
                print(f"  Confidence: {result['confidence']:.2f}")
                print(f"  Swing phase: {result.get('swing_phase', 'N/A')}")
                print(f"  Reason: {result['reason']}")
                print("  ✅ Analysis completed")
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")

def test_session_status():
    """Test session status endpoint"""
    print("\n=== Testing Session Status Endpoint ===")
    
    session_id = "test-status-session"
    url = f"{BASE_URL}/api/v1/recording/swing/sessions/{session_id}/status"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Session ID: {result['session_id']}")
            print(f"  Swings detected: {result['swings_detected']}")
            print(f"  Images in context: {result['images_in_context']}")
            print(f"  Created at: {result.get('created_at', 'N/A')}")
            print("  ✅ Status retrieved successfully")
        elif response.status_code == 404:
            print("  ℹ️  Session not found (expected for new session)")
        else:
            print(f"  ❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")

def test_health_endpoints():
    """Test health check endpoints"""
    print("\n=== Testing Health Endpoints ===")
    
    endpoints = [
        "/api/v1/recording/voice/health",
        "/api/v1/recording/swing/health"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}")
        url = f"{BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  Status: {result['status']}")
                print(f"  Service: {result['service']}")
                print("  ✅ Service healthy")
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")

async def test_websocket_voice_stream():
    """Test WebSocket voice streaming endpoint"""
    print("\n=== Testing WebSocket Voice Streaming ===")
    
    session_id = "ws-test-session"
    ws_url = f"ws://localhost:8000/api/v1/recording/voice/stream/{session_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("  ✅ WebSocket connected")
            
            # Send test voice data
            test_messages = [
                {
                    "transcript": "hello",
                    "confidence": 0.7,
                    "is_final": False
                },
                {
                    "transcript": "hello I'm ready",
                    "confidence": 0.8,
                    "is_final": False
                },
                {
                    "transcript": "hello I'm ready to begin recording",
                    "confidence": 0.9,
                    "is_final": True
                }
            ]
            
            for i, message in enumerate(test_messages):
                print(f"\n  Sending message {i+1}: '{message['transcript']}'")
                await websocket.send(json.dumps(message))
                
                # Wait for response
                response = await websocket.recv()
                result = json.loads(response)
                
                print(f"    Ready to begin: {result.get('ready_to_begin', False)}")
                print(f"    Confidence: {result.get('confidence', 0):.2f}")
                print(f"    Reason: {result.get('reason', 'N/A')}")
                
                if result.get('ready_to_begin') and result.get('confidence', 0) > 0.7:
                    print("    🎯 High confidence ready signal detected!")
            
            print("  ✅ WebSocket test completed")
            
    except Exception as e:
        print(f"  ❌ WebSocket Exception: {e}")

def main():
    """Run all tests"""
    print("🧪 Starting Recording API Tests")
    print("=" * 50)
    
    # Test health endpoints first
    test_health_endpoints()
    
    # Test voice begin signal
    test_voice_begin_endpoint()
    
    # Test swing detection
    test_swing_detection_endpoint()
    
    # Test session status
    test_session_status()
    
    # Test WebSocket (if available)
    print("\n=== Testing WebSocket (requires asyncio) ===")
    try:
        asyncio.run(test_websocket_voice_stream())
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Recording API Tests Completed")

if __name__ == "__main__":
    main()