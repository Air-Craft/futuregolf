# Troubleshooting Guide

## Network Connectivity Issues

### TTS Timeout Problems

**Symptoms:**
- TTS requests timeout after working previously
- Console shows "TTS Error" messages

**Diagnostic Steps:**
1. Check server connectivity at app launch (look for 🚀 prefixed logs)
2. Verify IP address in `Config.swift` matches server
3. Test with curl from Mac: 
   ```bash
   curl -X POST http://192.168.40.75:8000/api/v1/tts/coaching \
     -H "Content-Type: application/json" \
     -d '{"text":"Test","voice":"onyx","model":"tts-1-hd","speed":0.9}'
   ```
4. Check if phone and Mac are on same network

**Common Causes:**
- Phone switched to cellular data
- Mac IP address changed
- Server not running
- Firewall blocking connection

### API Connection Test

The app now tests server connectivity at launch. Check console for:
```
🚀 APP LAUNCH: Testing server connectivity...
🚀 Server URL: http://192.168.40.75:8000
🚀 Server health check - Status: 200
🚀 TTS test - Status: 200, Time: X.XXs
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

### Console Log Prefixes
- 🚀 : App launch diagnostics
- 🎵 : TTS service logs
- 🎤 : Voice command logs
- 🐛 : General debug logs
- 📸 : Camera-related logs

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