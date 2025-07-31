# Troubleshooting Guide

## Network Connectivity Issues

### ConnectivityService Monitoring

The app now includes automatic network monitoring with visual feedback in DEBUG mode.

**Features:**
- Real-time connectivity detection
- Toast notifications for connection changes
- Automatic retry when connectivity restored
- Host reachability checking

**Debug Toast Messages:**
- "Connected via WiFi" - Network restored
- "No network connection" - Network lost
- "Connected via Cellular" - Using mobile data

### TTS Timeout Problems

**Symptoms:**
- TTS requests timeout after working previously
- Console shows "TTS Error" messages
- Toast shows "No network connection"

**Diagnostic Steps:**
1. Check ConnectivityService status:
   ```swift
   print("Connected: \(ConnectivityService.shared.isConnected)")
   print("Connection type: \(ConnectivityService.shared.connectionType)")
   ```

2. Verify server reachability:
   ```swift
   let reachable = await ConnectivityService.shared.isHostReachable(Config.serverBaseURL)
   ```

3. Check server connectivity at app launch (look for 🚀 prefixed logs)

4. Verify IP address in `Config.swift` matches server

5. Test with curl from Mac: 
   ```bash
   curl -X POST http://192.168.40.75:8000/api/v1/tts/coaching \
     -H "Content-Type: application/json" \
     -d '{"text":"Test","voice":"onyx","model":"tts-1-hd","speed":0.9}'
   ```

6. Check if phone and Mac are on same network

**Common Causes:**
- Phone switched to cellular data
- Mac IP address changed
- Server not running
- Firewall blocking connection

**Automatic Recovery:**
- TTS cache manager automatically retries when connectivity restored
- Services registered with ConnectivityService get callbacks
- No manual intervention needed in most cases

### API Connection Test

The app now tests server connectivity at launch. Check console for:
```
🚀 APP LAUNCH: Testing server connectivity...
🚀 Server URL: http://192.168.40.75:8000
🚀 Server health check - Status: 200
🚀 TTS test - Status: 200, Time: X.XXs
```

## TTS Caching Issues

### Cache Not Populating

**Symptoms:**
- Recording journey audio has delays
- Console shows cache miss messages
- Progress toast stuck at 0%

**Diagnostic Steps:**
1. Check cache status:
   ```swift
   TTSService.shared.cacheManager.debugListCachedFiles()
   ```

2. Verify network connectivity when app launches

3. Look for cache warming logs:
   ```
   🗣️💾 TTS Cache: Starting cache warm-up process...
   🗣️💾 TTS Cache: Total phrases to cache: 6
   ```

4. Force cache refresh:
   ```bash
   # Launch with force refresh
   TTS_FORCE_REFRESH=1
   ```

**Common Causes:**
- No network on first launch
- Server unreachable during cache warming
- File system permissions issues

### Cache Progress Toast Not Showing

**Requirements:**
- DEBUG_MODE=1 environment variable
- Toast overlay added to root view
- Cache warming in progress

**Verify:**
```swift
// Should see in FutureGolfApp
.withToastOverlay()
```

## Voice Command Issues

### STT Not Recognizing Commands

**Check:**
1. Microphone permissions granted
2. Device supports on-device recognition
3. Speaking clearly with supported phrases
4. Console shows "🎤 Voice command received"

**Supported Commands:**
- Start: "begin", "start", "i'm ready", "let's go"
- Stop: "stop", "finish", "done", "cancel"

## Camera Issues

### Low Frame Rate

**Check Console for:**
```
🐛 RecordingViewModel: Found compatible format - Format: 1920x1080, FPS: 30.0-30.0
🐛 RecordingViewModel: No format found for target rates, finding best available...
```

**Solutions:**
- Ensure good lighting (low light forces lower frame rates)
- Close other camera-using apps
- Restart device if camera seems stuck

### Black Preview Screen

**Diagnostic Steps:**
1. Check camera permissions in Settings
2. Look for "🐛 CameraPreviewCoordinator" logs
3. Verify capture session is starting
4. Check for red background (indicates preview layer issue)

## Audio Session Conflicts

### Symptoms:
- TTS cuts out when STT starts
- Microphone not working
- Audio routing issues

### Solution:
Both TTS and STT use `.playAndRecord` category with compatible options. If issues persist, check for other apps using audio.

## Debug Features

### Environment Variables
- `DEBUG_LAUNCH_RECORDING=1`: Launch directly to recording screen
- `API_BASE_URL`: Override default server URL
- `TTS_FORCE_REFRESH=1`: Force TTS cache refresh on launch
- `DEBUG_MODE=1`: Enable debug toasts and verbose logging

### Console Log Prefixes
- 🚀 : App launch diagnostics
- 🗣️ : TTS service logs (replaced 🎵)
- 🗣️💾 : TTS cache operations
- 🎤 : Voice command logs
- 🐛 : General debug logs
- 📸 : Camera-related logs
- 🌐 : Connectivity status logs

## Backend Server Issues

### Verify Server Running:
```bash
ps aux | grep -E "python.*8000|uvicorn" | grep -v grep
```

### Check Server Logs:
Look for FastAPI/Uvicorn output in terminal where server was started

### Test Endpoints Directly:
```bash
# Health check
curl http://192.168.40.75:8000/health

# TTS test
curl -X POST http://192.168.40.75:8000/api/v1/tts/coaching \
  -H "Content-Type: application/json" \
  -d '{"text":"Test","voice":"onyx","model":"tts-1-hd","speed":0.9}' \
  -o test.mp3
```