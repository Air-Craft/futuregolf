#!/usr/bin/env python3
"""
Test script to verify Google Gemini API v2 migration.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_import():
    """Test if new library imports work."""
    try:
        from google import genai
        from google.genai.types import HarmCategory, HarmBlockThreshold
        print("✅ Successfully imported google.genai v2 library")
        return True
    except ImportError as e:
        print(f"❌ Failed to import google.genai v2: {e}")
        return False

def test_client_creation():
    """Test if client creation works."""
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return False
        
        client = genai.Client(api_key=api_key)
        print("✅ Successfully created Gemini client")
        return True
    except Exception as e:
        print(f"❌ Failed to create Gemini client: {e}")
        return False

def test_models_list():
    """Test if we can list available models."""
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return False
        
        client = genai.Client(api_key=api_key)
        # This is a basic test - we're not actually calling the API
        # Just checking if the client methods exist
        if hasattr(client, 'models'):
            print("✅ Client has models attribute")
            return True
        else:
            print("❌ Client missing models attribute")
            return False
    except Exception as e:
        print(f"❌ Failed to test models: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Google Gemini API v2 Migration")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_import),
        ("Client Creation Test", test_client_creation),
        ("Models Test", test_models_list),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Migration looks successful.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())