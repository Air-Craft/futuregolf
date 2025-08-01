# Audio Routing Configuration

This document describes the audio routing implementation that ensures TTS and microphone use the active audio device (headphones, Bluetooth, speaker) rather than forcing a specific output.

## Overview

The app now properly respects the user's audio device choice, playing TTS through headphones/Bluetooth when connected and using the appropriate microphone input.

## Architecture

### AudioRouteManager

**Location**: `ios/FutureGolf/FutureGolf/AudioRouteManager.swift`

A centralized manager for audio route configuration and monitoring:

#### Key Features:
- **Route Monitoring**: Listens for audio route changes via `AVAudioSession.routeChangeNotification`
- **Device Detection**: Identifies headphones, Bluetooth, AirPlay, CarPlay, speaker, etc.
- **Configuration Methods**: 
  - `configureForPlayback()` - Sets up audio for TTS playback
  - `configureForRecording()` - Sets up audio for voice recording
- **Debug Support**: Shows toast notifications when audio route changes (debug builds only)

#### Audio Session Options:

**Playback Configuration**:
```swift
.playAndRecord
mode: .default
options: [
    .duckOthers,           // Lower other audio
    .allowBluetooth,       // Allow Bluetooth devices
    .allowBluetoothA2DP,   // High-quality Bluetooth audio
    .allowAirPlay          // Allow AirPlay devices
]
```

**Recording Configuration**:
```swift
.playAndRecord
mode: .measurement        // Optimized for voice
options: [
    .duckOthers,
    .allowBluetooth
]
```

### Integration Points

#### TTSService
- Uses `AudioRouteManager.configureForPlayback()` before playing audio
- Removed `.defaultToSpeaker` option that was forcing speaker output
- Properly initialized in async context to avoid main actor issues

#### OnDeviceSTTService
- Uses `AudioRouteManager.configureForRecording()` before starting recognition
- Already had proper `.allowBluetooth` configuration
- Supports Bluetooth microphones

## Route Change Handling

The AudioRouteManager responds to these route change reasons:
- `.newDeviceAvailable` - Headphones/Bluetooth connected
- `.oldDeviceUnavailable` - Headphones/Bluetooth disconnected
- `.categoryChange` - Audio category changed
- `.override` - System override
- `.wakeFromSleep` - Device woke up
- `.routeConfigurationChange` - Route settings changed

## User Experience

### Visual Feedback
- Debug builds show toast: "Audio: Headphones" when route changes
- Current route stored in `AudioRouteManager.currentRoute`
- Boolean flag `isHeadphonesConnected` for UI decisions

### Behavior
1. **Headphones Connected**: TTS plays through headphones
2. **Bluetooth Connected**: TTS plays through Bluetooth device
3. **Nothing Connected**: TTS plays through speaker (not forced)
4. **AirPlay Active**: TTS plays through AirPlay device

## Implementation Notes

### Main Actor Isolation
Due to Swift concurrency, AudioRouteManager methods that modify state are marked `@MainActor`. Services initialize their reference in async context:

```swift
Task { @MainActor in
    self.audioRouteManager = AudioRouteManager.shared
}
```

### Initialization
AudioRouteManager is initialized early in app startup:
```swift
// In FutureGolfApp.init()
_ = AudioRouteManager.shared
```

## Testing Audio Routes

1. **Test Headphones**:
   - Connect wired headphones
   - Verify TTS plays through headphones
   - Disconnect and verify switch to speaker

2. **Test Bluetooth**:
   - Connect Bluetooth headphones/speaker
   - Verify TTS plays through Bluetooth
   - Test microphone input from Bluetooth device

3. **Test AirPlay**:
   - Connect to AirPlay device
   - Verify TTS routes correctly

4. **Test Route Changes**:
   - Start TTS playback
   - Connect/disconnect headphones mid-playback
   - Verify smooth transition

## Troubleshooting

### Common Issues

1. **Audio Not Routing**: Check AudioRouteManager is initialized
2. **Bluetooth Issues**: Ensure `.allowBluetooth` options are set
3. **No Audio**: Verify audio session is active
4. **Forced Speaker**: Remove any `.defaultToSpeaker` options

### Debug Information

Enable debug logging to see:
- Current audio route
- Route change events
- Audio session configuration
- Device connection status

## Best Practices

1. **Don't Force Routes**: Let iOS handle routing based on user preference
2. **Handle Interruptions**: Audio may be interrupted by calls/Siri
3. **Test All Devices**: Test with various audio devices
4. **Respect User Choice**: Never override user's audio device selection
5. **Provide Feedback**: Show current audio route in debug/settings