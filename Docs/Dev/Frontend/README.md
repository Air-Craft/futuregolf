# Frontend Development Documentation

## Overview

This directory contains documentation for the FutureGolf iOS frontend development, including implementation guides, configuration details, and troubleshooting information.

## Core Services

### Audio & Speech
- [**TTS Service**](./TTS_SERVICE.md) - Text-to-Speech implementation with OpenAI backend
- [**TTS Caching**](./TTS_CACHING.md) - Pre-generation and caching system for instant audio playback
- [**On-Device STT**](./ON_DEVICE_STT.md) - Speech-to-Text using iOS Speech Recognition

### Camera & Recording
- [**Camera Configuration**](./CAMERA_CONFIGURATION.md) - Frame rate optimization and capture setup

### Network & UI
- [**Connectivity Service**](./CONNECTIVITY_SERVICE.md) - Network monitoring and recovery
- [**Toast System**](./TOAST_SYSTEM.md) - Global notification and progress UI

## Architecture Highlights

### TTS Audio Pipeline
1. **Cache Check** → Check pre-generated audio cache
2. **Instant Playback** → Use cached audio if available
3. **Fallback Synthesis** → Generate if not cached
4. **Background Warming** → Pre-generate all journey phrases

### Network Resilience
- Real-time connectivity monitoring
- Automatic retry on connection restoration
- Visual feedback in DEBUG mode
- Host-specific reachability checking

### User Feedback
- Non-blocking toast notifications
- Progress tracking for long operations
- Type-based styling (info, success, warning, error)
- Queue management for multiple messages

## Configuration

Key settings in `Config.swift`:
```swift
// TTS Configuration
static let ttsCacheRefreshInterval: TimeInterval = 86400.0
static let ttsSynthesisTimeout: TimeInterval = 20.0

// Network Timeouts
static let healthCheckTimeout: TimeInterval = 5.0
static let apiRequestTimeout: TimeInterval = 30.0
static let videoUploadTimeout: TimeInterval = 120.0
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `DEBUG_MODE` | Enable debug toasts and logging | false |
| `TTS_FORCE_REFRESH` | Force TTS cache refresh on launch | false |
| `DEBUG_LAUNCH_RECORDING` | Skip to recording screen | false |

## Quick Reference

### Check TTS Cache Status
```swift
TTSService.shared.cacheManager.debugListCachedFiles()
```

### Monitor Network Status
```swift
print("Connected: \(ConnectivityService.shared.isConnected)")
print("Type: \(ConnectivityService.shared.connectionType)")
```

### Show Toast Notification
```swift
ToastManager.shared.show("Success!", type: .success)
```

### Track Progress
```swift
let id = ToastManager.shared.showProgress("Uploading...")
ToastManager.shared.updateProgress(id: id, progress: 0.5)
ToastManager.shared.dismissProgress(id: id)
```

## Related Documentation

- [Troubleshooting Guide](../TROUBLESHOOTING.md) - Common issues and solutions
- [Debug Features](../DEBUG_FEATURES.md) - Development tools and logging