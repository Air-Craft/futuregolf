#!/usr/bin/env python3
"""
Direct debug recording screen launcher for QiPhone
This script will install and launch the app in debug mode
"""

import subprocess
import sys
import time
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            return True
        else:
            print(f"❌ {description} failed:")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"💥 {description} error: {e}")
        return False

def main():
    print("🎯 FutureGolf Debug Recording Screen Launcher")
    print("=" * 50)
    
    # Change to iOS project directory
    ios_dir = "/Users/brian/Tech/Code/futuregolf/ios/FutureGolf"
    if not os.path.exists(ios_dir):
        print(f"❌ iOS project directory not found: {ios_dir}")
        sys.exit(1)
    
    os.chdir(ios_dir)
    print(f"📁 Working directory: {ios_dir}")
    
    # Step 1: Build the app
    build_cmd = 'xcodebuild -scheme FutureGolf -destination "platform=iOS,name=QiPhone" -configuration Debug build'
    if not run_command(build_cmd, "Building app for QiPhone"):
        print("\n💡 Build failed. Try opening the project in Xcode and:")
        print("   - Set development team for signing")
        print("   - Trust developer certificate on device")
        print("   - Ensure QiPhone is connected and trusted")
        sys.exit(1)
    
    # Step 2: Install the app
    install_cmd = 'xcrun devicectl device install app --device QiPhone /Users/brian/Library/Developer/Xcode/DerivedData/FutureGolf-*/Build/Products/Debug-iphoneos/FutureGolf.app'
    if not run_command(install_cmd, "Installing app on QiPhone"):
        # Fallback to legacy method
        legacy_install = 'ios-deploy --bundle /Users/brian/Library/Developer/Xcode/DerivedData/FutureGolf-*/Build/Products/Debug-iphoneos/FutureGolf.app --device QiPhone'
        if not run_command(legacy_install, "Installing app (legacy method)"):
            print("\n💡 Installation failed. Manual steps:")
            print("   1. Open Xcode")
            print("   2. Run the app directly from Xcode to QiPhone")
            print("   3. Once installed, follow debug instructions below")
    
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")
    print("\n📱 MANUAL STEPS TO ENABLE DEBUG MODE:")
    print("   1. Find FutureGolf app on QiPhone")
    print("   2. Force quit if running (swipe up, swipe away)")
    print("   3. Open Xcode")
    print("   4. Go to Product > Scheme > Edit Scheme")
    print("   5. In Run > Arguments > Environment Variables:")
    print("      Add: DEBUG_LAUNCH_RECORDING = 1")
    print("   6. Run from Xcode with QiPhone selected")
    
    print("\n🐛 DEBUG FEATURES AVAILABLE:")
    print("   ✓ Direct recording screen access")
    print("   ✓ Permission testing")
    print("   ✓ API connectivity testing")
    print("   ✓ Comprehensive error logging")
    print("   ✓ Real-time debug information")
    
    print("\n📋 TESTING WORKFLOW:")
    print("   1. App opens in Debug Recording Launcher")
    print("   2. Tap 'Test Recording Screen Setup'")
    print("   3. Review logs for any errors")
    print("   4. If tests pass, tap 'Launch Recording Screen'")
    print("   5. Monitor Xcode console for 🐛 debug messages")
    
    print("\n🔍 TROUBLESHOOTING:")
    print("   - Watch Xcode console for detailed error messages")
    print("   - Look for RecordingViewModel debug logs")
    print("   - Check camera/microphone permission prompts")
    print("   - Verify API connectivity to backend")
    
    print("\n🎬 Ready to debug the recording screen!")

if __name__ == "__main__":
    main()