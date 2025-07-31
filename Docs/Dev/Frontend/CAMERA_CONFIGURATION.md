# Camera Configuration

## Overview
The recording screen supports high frame rate video capture with intelligent format selection and real-time frame rate display.

## Frame Rate Configuration

### Target Frame Rates
- **Preferred**: 60 fps (when device supports)
- **Fallback**: 30 fps
- **Minimum**: 24 fps

### Device-Specific Support
The app dynamically detects camera capabilities:
1. Searches for 60fps-capable formats at 1080p or higher
2. Falls back to 30fps if 60fps unavailable
3. Uses highest available frame rate as last resort

## Camera Selection

### Default Camera
- Front camera (`.front`) - for user self-recording
- Switchable to back camera via UI button

### Format Selection Algorithm
```swift
1. For each target frame rate (60fps, then 30fps):
   - Find formats supporting target rate
   - Prefer 1920x1080 or higher resolution
   - Select best quality format at target rate
2. If no target rate found:
   - Use highest available frame rate
   - Prioritize resolution over frame rate
```

## Real-Time Frame Rate Display

Shows actual achieved frame rate in top-right corner:
- Format: "XX FPS" 
- Updates when camera configuration changes
- Positioned below camera flip button to avoid overlap

## Session Configuration

### Preset
- `AVCaptureSession.Preset.hd1920x1080`

### Video Stabilization
- Mode: `.auto` (when supported)

### Orientation
- Fixed to portrait mode
- iOS 17+: Uses `videoRotationAngle = 90`
- iOS 16-: Uses `videoOrientation = .portrait`

## Still Image Capture

For swing detection, captures stills every 0.25 seconds:
- Resolution: 1920x1080 (when possible)
- Format: JPEG with 0.7 compression
- Resized to 300x400 for API transmission

## Debug Logging

Extensive camera setup logging with "🐛" prefix:
- Format enumeration details
- Selected format specifications
- Frame rate achievement status