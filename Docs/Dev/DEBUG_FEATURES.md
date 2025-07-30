# DEBUG FEATURES

This document describes the debugging tools and features available for FutureGolf development, particularly for the Recording Screen functionality.

## Table of Contents
- [Recording Screen Debug Solution](#recording-screen-debug-solution)
- [Debug Launch Mode](#debug-launch-mode)
- [UITests](#uitests)
- [Enhanced Error Logging](#enhanced-error-logging)
- [Deployment Tools](#deployment-tools)
- [Troubleshooting Guide](#troubleshooting-guide)

## Recording Screen Debug Solution

The Recording Screen debug solution provides comprehensive testing and debugging capabilities for the video recording functionality, including camera setup, voice recognition, API integration, and error handling.

### Overview

The debug solution consists of four main components:

1. **Debug Launch Mode** - Direct access to recording screen testing interface
2. **Enhanced UITests** - Comprehensive automated testing suite
3. **Enhanced Error Logging** - Detailed debug logging throughout the recording process
4. **Deployment Tools** - Automated scripts for building and installing debug versions

## Debug Launch Mode

### Activation

The debug launch mode is activated by setting the `DEBUG_LAUNCH_RECORDING` environment variable to `1`.

#### Method 1: Via Xcode Scheme
1. Open the FutureGolf project in Xcode
2. Go to **Product** → **Scheme** → **Edit Scheme**
3. Select **Run** in the left sidebar
4. Go to **Arguments** tab → **Environment Variables**
5. Add: `DEBUG_LAUNCH_RECORDING = 1`
6. Run the app with QiPhone selected as target

#### Method 2: Via Launch Arguments
```bash
# When running from command line
xcodebuild -scheme FutureGolf -destination 'platform=iOS,name=QiPhone' \
  -configuration Debug run \
  -launchArguments DEBUG_LAUNCH_RECORDING=1
```

### Debug Interface Features

When debug mode is enabled, the app launches into a **Debug Recording Launcher** interface with the following features:

#### Test Recording Screen Setup
- **Camera Permission Testing** - Checks and requests camera access
- **Microphone Permission Testing** - Validates audio recording permissions
- **API Connectivity Testing** - Verifies backend endpoint availability
- **Real-time Logging** - Shows detailed setup logs with timestamps

#### Launch Recording Screen
- **Direct Access** - Bypasses normal app navigation to go straight to recording screen
- **Error Monitoring** - Tracks all setup errors and displays them in the UI
- **Permission Handling** - Provides clear feedback on permission states

#### Debug Logging Display
- **Timestamped Logs** - All setup activities with precise timestamps
- **Scrollable Log View** - Review up to 20 recent log entries
- **Error Highlighting** - Failed operations clearly marked in red

### Code Implementation

The debug launch mode is implemented in `FutureGolfApp.swift`:

```swift
// Debug flag for direct recording screen launch
private let debugLaunchRecording = ProcessInfo.processInfo.environment["DEBUG_LAUNCH_RECORDING"] == "1"

var body: some Scene {
    WindowGroup {
        if debugLaunchRecording {
            // Launch directly into recording screen for testing
            NavigationView {
                DebugRecordingLauncher()
            }
        } else {
            // Normal app flow
            HomeView()
        }
    }
}
```

## UITests

### RecordingScreenUITests.swift

Comprehensive UI test suite located at:
```
ios/FutureGolf/FutureGolfUITests/RecordingScreenUITests.swift
```

#### Test Categories

1. **Navigation and Setup Tests**
   - `testNavigateToRecordingScreen()` - Validates navigation to recording screen
   - `testRecordingScreenUIElements()` - Verifies all UI elements are present
   - `testAccessibilityElements()` - Validates accessibility identifiers and labels

2. **Permission Tests**
   - `testCameraPermissionFlow()` - Tests camera permission granting
   - `testCameraPermissionDenied()` - Tests permission denial handling
   - `testMicrophonePermissionFlow()` - Tests microphone permission granting

3. **Recording Phase Tests**
   - `testRecordingPhaseUI()` - Validates recording phase UI elements
   - `testCancelRecordingFlow()` - Tests cancel functionality
   - `testAppBackgroundingDuringRecording()` - Tests app lifecycle handling

4. **Integration Tests**
   - `testEndToEndRecordingFlow()` - Complete recording workflow test
   - `testAPIConnectivity()` - Backend API integration testing
   - `testNetworkConnectivity()` - Network error handling

5. **Performance Tests**
   - `testCameraSetupPerformance()` - Measures camera initialization time
   - `testMemoryUsageDuringRecording()` - Monitors memory usage

#### Running UITests

```bash
# Run all recording screen UI tests
cd ios/FutureGolf
xcodebuild -scheme FutureGolf -destination 'platform=iOS,name=QiPhone' test -only-testing:FutureGolfUITests/RecordingScreenUITests

# Run specific test
xcodebuild -scheme FutureGolf -destination 'platform=iOS,name=QiPhone' test -only-testing:FutureGolfUITests/RecordingScreenUITests/testEndToEndRecordingFlow
```

#### Test Configuration

UITests are configured with:
- Environment variable: `UI_TESTING = 1`
- API base URL: `API_BASE_URL = http://192.168.1.228:8000`
- Automatic permission resets for clean test runs

## Enhanced Error Logging

### RecordingViewModel Debug Logging

The `RecordingViewModel` includes comprehensive debug logging prefixed with 🐛 for easy identification:

#### Initialization Logging
```swift
override init() {
    super.init()
    
    // Enhanced error logging for debugging
    print("🐛 RecordingViewModel: Initializing...")
    
    do {
        setupProgressCircles()
        print("🐛 RecordingViewModel: Progress circles setup completed")
        
        setupSpeechRecognizer()
        print("🐛 RecordingViewModel: Speech recognizer setup completed")
        
        // Start API session
        let sessionId = recordingAPIService.startSession()
        print("🐛 RecordingViewModel: API session started with ID: \(sessionId)")
        
    } catch {
        print("🐛 RecordingViewModel: Initialization error: \(error)")
    }
}
```

#### Camera Setup Logging
```swift
func setupCamera() async throws {
    print("🐛 RecordingViewModel: Starting camera setup...")
    
    // Detailed logging for each setup step:
    // - Capture session creation
    // - Permission checking and requesting
    // - Session configuration
    // - Camera input setup
    // - Video/photo output setup
    
    print("🐛 RecordingViewModel: Camera setup completed successfully")
}
```

#### Voice Recognition Logging
```swift
func startVoiceRecognition() async throws {
    print("🐛 RecordingViewModel: Starting voice recognition setup...")
    
    // Logs include:
    // - iOS version-specific permission handling
    // - Audio session configuration
    // - Speech recognizer setup
    // - Audio engine initialization
}
```

### Viewing Debug Logs

#### In Xcode Console
1. Run the app from Xcode with QiPhone selected
2. Open **Console** (View → Debug Area → Console)
3. Filter by 🐛 to see only debug messages
4. Debug messages include timestamps and detailed operation info

#### Device Console
```bash
# View device logs in terminal
xcrun devicectl device log stream --device QiPhone | grep "🐛"

# Or using Console.app
# Open Console.app → Select QiPhone → Filter by "🐛"
```

## Deployment Tools

### Automated Deployment Script

**Location:** `/Users/brian/Tech/Code/futuregolf/launch_debug_recording.py`

```bash
# Run automated deployment
cd /Users/brian/Tech/Code/futuregolf
python3 launch_debug_recording.py
```

**Features:**
- Builds app for QiPhone automatically
- Attempts installation via multiple methods
- Provides step-by-step instructions for manual setup
- Includes comprehensive troubleshooting guidance

### Manual Installation Script

**Location:** `/Users/brian/Tech/Code/futuregolf/install_debug_app.sh`

```bash
# Run manual installation
cd /Users/brian/Tech/Code/futuregolf
chmod +x install_debug_app.sh
./install_debug_app.sh
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. App Crashes on Launch
**Symptoms:** App immediately crashes when opening recording screen

**Debug Steps:**
1. Enable debug mode: `DEBUG_LAUNCH_RECORDING=1`
2. Check Xcode console for 🐛 debug messages
3. Look for initialization errors in RecordingViewModel
4. Verify camera/microphone permissions

**Common Causes:**
- Missing camera permissions
- Invalid camera configuration for device
- Network connectivity issues preventing API calls

#### 2. Camera Setup Failures
**Symptoms:** Black screen or camera not initializing

**Debug Steps:**
1. Check debug logs for camera permission status
2. Verify camera hardware availability
3. Test camera switching functionality
4. Check for iOS version compatibility issues

**Common Causes:**
- Camera permission denied
- Hardware camera not available (simulator)
- Conflicting camera sessions from other apps

#### 3. Voice Recognition Not Working
**Symptoms:** Voice commands not triggering recording

**Debug Steps:**
1. Check microphone permission logs
2. Verify speech recognizer initialization
3. Test with clear, direct voice commands
4. Check network connectivity for speech processing

**Common Causes:**
- Microphone permission denied
- Poor network connectivity affecting speech recognition
- Background noise interference
- iOS speech recognition service unavailable

#### 4. API Connectivity Issues
**Symptoms:** Network errors, failed API calls

**Debug Steps:**
1. Verify backend server is running: `http://192.168.1.228:8000`
2. Test API endpoints manually
3. Check device network connectivity
4. Verify API service configuration

**Common Causes:**
- Backend server not running
- Network connectivity issues
- Incorrect API base URL configuration
- Firewall blocking requests

#### 5. Frame Rate Configuration Crash
**Symptoms:** App crashes with `NSInvalidArgumentException` related to `setActiveVideoMinFrameDuration`

**Error Example:**
```
*** Terminating app due to uncaught exception 'NSInvalidArgumentException', 
reason: '*** -[AVCaptureDevice setActiveVideoMinFrameDuration:] Unsupported frame duration 
- Supported ranges: ( "<AVFrameRateRange: 0x1157e49b0 1 - 30>" ), 
tried to set maxFrameRate to 60.000000'
```

**Debug Steps:**
1. Check device-specific frame rate capabilities in debug logs
2. Look for "Available frame rate ranges" log message
3. Verify target frame rate is within supported range
4. Check if device supports high frame rates

**Solution:**
The issue was fixed by:
- Reducing target frame rate from 120fps to 30fps
- Adding device capability detection before setting frame rates
- Implementing fallback to device defaults when unsupported rates are requested
- Adding comprehensive validation of frame duration values

**Common Causes:**
- Older devices with limited camera capabilities
- Attempting to set frame rates beyond device hardware limits
- Missing validation of camera capabilities before configuration

### Debug Log Analysis

#### Successful Initialization Sequence
```
🐛 RecordingViewModel: Initializing...
🐛 RecordingViewModel: Progress circles setup completed
🐛 RecordingViewModel: Speech recognizer setup completed
🐛 RecordingViewModel: API session started with ID: [UUID]
🐛 RecordingViewModel: Starting camera setup...
🐛 RecordingViewModel: Capture session created successfully
🐛 RecordingViewModel: Camera permission status: 3 (authorized)
🐛 RecordingViewModel: Starting session configuration...
🐛 RecordingViewModel: Session preset set to: hd1920x1080
🐛 RecordingViewModel: Setting up camera input...
🐛 RecordingViewModel: Camera input setup completed
🐛 RecordingViewModel: Setting up video output...
🐛 RecordingViewModel: Video output setup completed
🐛 RecordingViewModel: Setting up photo output...
🐛 RecordingViewModel: Photo output setup completed
🐛 RecordingViewModel: Camera setup completed successfully
```

#### Error Example - Permission Denied
```
🐛 RecordingViewModel: Starting camera setup...
🐛 RecordingViewModel: Capture session created successfully
🐛 RecordingViewModel: Camera permission status: 2 (denied)
🐛 RecordingViewModel: Camera permission denied or restricted
Error: Camera access is required to record your swing. Please enable camera permissions in Settings.
```

### Performance Monitoring

#### Memory Usage
Monitor memory usage during recording to identify leaks:
```swift
// UITests include memory monitoring
func testMemoryUsageDuringRecording() throws {
    measure(metrics: [XCTMemoryMetric()]) {
        // Simulate recording workflow
        // Memory usage should remain stable
    }
}
```

#### Camera Setup Performance
Track camera initialization time:
```swift
func testCameraSetupPerformance() throws {
    measure {
        // Measure camera setup time
        // Should complete within reasonable timeframe
    }
}
```

## Best Practices

### Development Workflow
1. **Always test with debug mode first** before testing normal app flow
2. **Check permissions** before testing recording functionality
3. **Verify backend connectivity** before testing API-dependent features
4. **Monitor debug logs** for early detection of issues
5. **Use UITests** for regression testing after changes

### Debug Mode Usage
1. **Enable debug mode** when developing recording features
2. **Test permission flows** regularly to ensure proper handling
3. **Validate API integration** with real backend endpoints
4. **Monitor performance** during extended recording sessions
5. **Document new issues** found during debugging

### Code Maintenance
1. **Keep debug logging** comprehensive but not overwhelming
2. **Update UITests** when adding new recording features
3. **Maintain deployment scripts** as project structure changes
4. **Document new debug features** in this file
5. **Regular cleanup** of debug logs to prevent log spam

---

## Contact and Support

For issues with the debug tools or additional debugging needs, refer to:
- **RecordingScreen implementation**: `ios/FutureGolf/FutureGolf/RecordingScreen.swift`
- **RecordingViewModel debug logs**: `ios/FutureGolf/FutureGolf/RecordingViewModel.swift`
- **UITests**: `ios/FutureGolf/FutureGolfUITests/RecordingScreenUITests.swift`
- **Debug launcher**: `ios/FutureGolf/FutureGolf/FutureGolfApp.swift`

The debug solution provides comprehensive coverage for identifying and resolving runtime issues with the recording screen functionality.