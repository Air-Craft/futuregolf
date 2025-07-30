#!/bin/bash

# Install and run FutureGolf app in debug mode on QiPhone
# This will launch directly into the recording screen test interface

echo "🚀 Installing FutureGolf in debug mode on QiPhone..."

# Navigate to iOS project directory
cd "$(dirname "$0")/ios/FutureGolf"

# Install app on device with debug environment variable
xcodebuild \
  -scheme FutureGolf \
  -destination 'platform=iOS,name=QiPhone' \
  -configuration Debug \
  install

if [ $? -eq 0 ]; then
    echo "✅ App installed successfully!"
    echo ""
    echo "📱 To enable debug mode:"
    echo "   1. Open the app on QiPhone"
    echo "   2. Force quit the app (swipe up and close)"
    echo "   3. Set DEBUG_LAUNCH_RECORDING=1 environment variable"
    echo "   4. Relaunch the app"
    echo ""
    echo "🐛 Debug features:"
    echo "   - Direct access to recording screen testing"
    echo "   - Comprehensive error logging"
    echo "   - Permission testing"
    echo "   - API connectivity testing"
    echo "   - Real-time debugging information"
    echo ""
    echo "📋 Instructions:"
    echo "   1. Run 'Test Recording Screen Setup' first"
    echo "   2. Check the logs for any errors"
    echo "   3. If no errors, tap 'Launch Recording Screen'"
    echo "   4. Monitor console output for debugging info"
    echo ""
    echo "🔍 To view debug logs:"
    echo "   - Use Xcode Console or device logs"
    echo "   - Look for 🐛 prefixed debug messages"
    echo "   - Watch for RecordingViewModel setup messages"
else
    echo "❌ Installation failed. Check Xcode signing settings."
    echo "💡 You may need to:"
    echo "   - Open the project in Xcode"
    echo "   - Set the development team"
    echo "   - Trust the developer certificate on the device"
fi