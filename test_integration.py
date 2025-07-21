#!/usr/bin/env python3
"""
Simple integration test for FutureGolf project
Tests both backend API endpoints and basic functionality
"""

import requests
import json
import time
import subprocess
import sys
import os

def test_backend_health():
    """Test backend health endpoint"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Backend health check passed")
            print(f"  Status: {data.get('status')}")
            print(f"  Service: {data.get('service')}")
            return True
        else:
            print(f"✗ Backend health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Backend health check failed: {e}")
        return False

def test_backend_root():
    """Test backend root endpoint"""
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Backend root endpoint passed")
            print(f"  Message: {data.get('message')}")
            return True
        else:
            print(f"✗ Backend root endpoint failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Backend root endpoint failed: {e}")
        return False

def test_cors_headers():
    """Test CORS headers are present"""
    try:
        # Test CORS with OPTIONS request and Origin header
        headers = {
            'Origin': 'http://localhost:8081',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'X-Requested-With'
        }
        response = requests.options('http://localhost:8000/', headers=headers, timeout=5)
        
        if response.status_code == 200:
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            if cors_origin and cors_methods:
                print("✓ CORS headers present")
                print(f"  Access-Control-Allow-Origin: {cors_origin}")
                print(f"  Access-Control-Allow-Methods: {cors_methods}")
                return True
            else:
                print("✗ CORS headers missing in response")
                return False
        else:
            print(f"✗ CORS preflight failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ CORS test failed: {e}")
        return False

def check_backend_process():
    """Check if backend process is running"""
    try:
        # Check if uvicorn process is running
        result = subprocess.run(['pgrep', '-f', 'uvicorn'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Backend process is running")
            return True
        else:
            print("✗ Backend process not found")
            return False
    except Exception as e:
        print(f"✗ Backend process check failed: {e}")
        return False

def test_frontend_files():
    """Test frontend files exist and are properly configured"""
    frontend_path = "/Users/brian/Tech/Code/futuregolf/frontend"
    
    # Check if package.json exists
    package_json_path = os.path.join(frontend_path, "package.json")
    if os.path.exists(package_json_path):
        print("✓ Frontend package.json exists")
        
        # Check if dependencies are installed
        node_modules_path = os.path.join(frontend_path, "node_modules")
        if os.path.exists(node_modules_path):
            print("✓ Frontend node_modules exists")
            return True
        else:
            print("✗ Frontend node_modules missing")
            return False
    else:
        print("✗ Frontend package.json missing")
        return False

def main():
    """Run all integration tests"""
    print("=" * 50)
    print("FutureGolf Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Backend Process Check", check_backend_process),
        ("Backend Health Endpoint", test_backend_health),
        ("Backend Root Endpoint", test_backend_root),
        ("CORS Headers", test_cors_headers),
        ("Frontend Files", test_frontend_files),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())