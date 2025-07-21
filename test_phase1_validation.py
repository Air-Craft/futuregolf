#!/usr/bin/env python3
"""
Phase 1 Validation Tests for FutureGolf
Tests all Phase 1 requirements as specified in Spec/Dev/Phase1.md
"""

import os
import json
import subprocess
import sys
import requests
import time
from pathlib import Path

class Phase1Validator:
    def __init__(self):
        self.project_root = Path("/Users/brian/Tech/Code/futuregolf")
        self.results = []
        
    def test_project_structure(self):
        """Test that project structure is properly set up"""
        print("🔍 Testing project structure...")
        
        required_dirs = [
            "frontend",
            "backend", 
            "backend/models",
            "backend/api",
            "backend/prompts",
            "backend/database",
            "backend/services"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                self.results.append(f"✅ {dir_path} exists")
            else:
                self.results.append(f"❌ {dir_path} missing")
        
        # Check key files
        key_files = [
            "frontend/package.json",
            "frontend/App.js",
            "backend/main.py",
            "backend/requirements.txt",
            "CLAUDE.md",
            ".mcp.json"
        ]
        
        for file_path in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.results.append(f"✅ {file_path} exists")
            else:
                self.results.append(f"❌ {file_path} missing")
    
    def test_mcp_configuration(self):
        """Test MCP server configuration"""
        print("🔍 Testing MCP configuration...")
        
        # Test global MCP config
        global_config = Path("/Users/brian/Library/Application Support/Claude/claude_desktop_config.json")
        if global_config.exists():
            try:
                with open(global_config) as f:
                    config = json.load(f)
                    if "ios-simulator-screenshot" in config.get("mcpServers", {}):
                        self.results.append("✅ iOS simulator screenshot MCP configured globally")
                    else:
                        self.results.append("❌ iOS simulator screenshot MCP not configured")
            except Exception as e:
                self.results.append(f"❌ Error reading global MCP config: {e}")
        else:
            self.results.append("❌ Global MCP config file not found")
        
        # Test project MCP config
        project_config = self.project_root / ".mcp.json"
        if project_config.exists():
            try:
                with open(project_config) as f:
                    config = json.load(f)
                    if "Neon" in config.get("mcpServers", {}):
                        self.results.append("✅ Neon database MCP configured at project level")
                    else:
                        self.results.append("❌ Neon database MCP not configured")
            except Exception as e:
                self.results.append(f"❌ Error reading project MCP config: {e}")
        else:
            self.results.append("❌ Project MCP config file not found")
    
    def test_database_models(self):
        """Test database models are created"""
        print("🔍 Testing database models...")
        
        model_files = [
            "backend/models/user.py",
            "backend/models/video.py", 
            "backend/models/video_analysis.py",
            "backend/models/subscription.py"
        ]
        
        for model_file in model_files:
            full_path = self.project_root / model_file
            if full_path.exists():
                self.results.append(f"✅ {model_file} exists")
                # Check for key model elements
                try:
                    with open(full_path) as f:
                        content = f.read()
                        if "class" in content and "Base" in content:
                            self.results.append(f"✅ {model_file} contains SQLAlchemy model")
                        else:
                            self.results.append(f"⚠️ {model_file} may not be properly structured")
                except Exception as e:
                    self.results.append(f"❌ Error reading {model_file}: {e}")
            else:
                self.results.append(f"❌ {model_file} missing")
    
    def test_authentication_endpoints(self):
        """Test authentication endpoints are created"""
        print("🔍 Testing authentication endpoints...")
        
        auth_files = [
            "backend/api/auth_login.py",
            "backend/api/auth_register.py",
            "backend/api/auth_oauth.py",
            "backend/api/user_profile.py"
        ]
        
        for auth_file in auth_files:
            full_path = self.project_root / auth_file
            if full_path.exists():
                self.results.append(f"✅ {auth_file} exists")
            else:
                self.results.append(f"❌ {auth_file} missing")
        
        # Test if FastAPI main.py includes authentication routes
        main_py = self.project_root / "backend/main.py"
        if main_py.exists():
            try:
                with open(main_py) as f:
                    content = f.read()
                    if "FastAPI" in content:
                        self.results.append("✅ FastAPI app configured")
                    if "auth" in content.lower():
                        self.results.append("✅ Authentication routes referenced in main.py")
            except Exception as e:
                self.results.append(f"❌ Error reading main.py: {e}")
    
    def test_prompt_templates(self):
        """Test LLM prompt templates are created"""
        print("🔍 Testing prompt templates...")
        
        prompt_files = [
            "backend/prompts/video_analysis_swing_coaching.txt",
            "backend/prompts/user_positioning_feedback.txt",
            "backend/prompts/coaching_script_generation.txt",
            "backend/prompts/body_angle_pose_analysis.txt"
        ]
        
        for prompt_file in prompt_files:
            full_path = self.project_root / prompt_file
            if full_path.exists():
                self.results.append(f"✅ {prompt_file} exists")
                # Check if file has content
                try:
                    with open(full_path) as f:
                        content = f.read().strip()
                        if len(content) > 100:  # Arbitrary minimum length
                            self.results.append(f"✅ {prompt_file} has substantial content")
                        else:
                            self.results.append(f"⚠️ {prompt_file} may be empty or too short")
                except Exception as e:
                    self.results.append(f"❌ Error reading {prompt_file}: {e}")
            else:
                self.results.append(f"❌ {prompt_file} missing")
    
    def test_file_storage_configuration(self):
        """Test file storage service configuration"""
        print("🔍 Testing file storage configuration...")
        
        storage_files = [
            "backend/services/storage_service.py",
            "backend/config/storage.py"
        ]
        
        for storage_file in storage_files:
            full_path = self.project_root / storage_file
            if full_path.exists():
                self.results.append(f"✅ {storage_file} exists")
            else:
                self.results.append(f"❌ {storage_file} missing")
    
    def test_frontend_setup(self):
        """Test frontend React Native/Expo setup"""
        print("🔍 Testing frontend setup...")
        
        # Check package.json for Expo
        package_json = self.project_root / "frontend/package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                    if "expo" in package_data.get("dependencies", {}):
                        self.results.append("✅ Expo dependency found in package.json")
                    if "react-native" in package_data.get("dependencies", {}):
                        self.results.append("✅ React Native dependency found in package.json")
                    if "scripts" in package_data and "ios" in package_data["scripts"]:
                        self.results.append("✅ iOS script configured in package.json")
            except Exception as e:
                self.results.append(f"❌ Error reading package.json: {e}")
        else:
            self.results.append("❌ Frontend package.json not found")
        
        # Check if node_modules exists (dependencies installed)
        node_modules = self.project_root / "frontend/node_modules"
        if node_modules.exists():
            self.results.append("✅ Frontend dependencies installed (node_modules exists)")
        else:
            self.results.append("❌ Frontend dependencies not installed")
    
    def test_backend_setup(self):
        """Test backend Python/FastAPI setup"""
        print("🔍 Testing backend setup...")
        
        # Check requirements.txt
        requirements = self.project_root / "backend/requirements.txt"
        if requirements.exists():
            try:
                with open(requirements) as f:
                    content = f.read()
                    if "fastapi" in content.lower():
                        self.results.append("✅ FastAPI found in requirements.txt")
                    if "sqlalchemy" in content.lower():
                        self.results.append("✅ SQLAlchemy found in requirements.txt")
                    if "uvicorn" in content.lower():
                        self.results.append("✅ Uvicorn found in requirements.txt")
            except Exception as e:
                self.results.append(f"❌ Error reading requirements.txt: {e}")
        else:
            self.results.append("❌ Backend requirements.txt not found")
        
        # Check if virtual environment exists
        venv = self.project_root / "backend/venv"
        if venv.exists():
            self.results.append("✅ Backend virtual environment exists")
        else:
            self.results.append("❌ Backend virtual environment not found")
    
    def test_ios_simulator_capability(self):
        """Test iOS simulator screenshot capability"""
        print("🔍 Testing iOS simulator capability...")
        
        try:
            # Check if simulators are available
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "available"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "iPhone" in result.stdout:
                self.results.append("✅ iOS simulators available")
                
                # Try to take a screenshot
                screenshot_result = subprocess.run(
                    ["xcrun", "simctl", "io", "booted", "screenshot", "/tmp/phase1_test.png"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if screenshot_result.returncode == 0:
                    self.results.append("✅ iOS simulator screenshot capability working")
                else:
                    self.results.append("⚠️ iOS simulator screenshot test failed (may need booted simulator)")
            else:
                self.results.append("❌ iOS simulators not available")
                
        except subprocess.TimeoutExpired:
            self.results.append("❌ iOS simulator test timed out")
        except Exception as e:
            self.results.append(f"❌ iOS simulator test error: {e}")
    
    def run_all_tests(self):
        """Run all Phase 1 validation tests"""
        print("🚀 Running Phase 1 Validation Tests for FutureGolf")
        print("=" * 50)
        
        self.test_project_structure()
        self.test_mcp_configuration()
        self.test_database_models()
        self.test_authentication_endpoints()
        self.test_prompt_templates()
        self.test_file_storage_configuration()
        self.test_frontend_setup()
        self.test_backend_setup()
        self.test_ios_simulator_capability()
        
        print("\n📊 Test Results:")
        print("=" * 50)
        
        passed = 0
        failed = 0
        warnings = 0
        
        for result in self.results:
            print(result)
            if result.startswith("✅"):
                passed += 1
            elif result.startswith("❌"):
                failed += 1
            elif result.startswith("⚠️"):
                warnings += 1
        
        print(f"\n📈 Summary: {passed} passed, {failed} failed, {warnings} warnings")
        
        if failed == 0:
            print("🎉 Phase 1 validation completed successfully!")
            return True
        else:
            print("❌ Phase 1 validation has failures that need to be addressed")
            return False

def main():
    validator = Phase1Validator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()