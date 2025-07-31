# On-Device Speech-to-Text (STT) Implementation

## Overview
The FutureGolf iOS app uses on-device speech recognition for voice commands using iOS's native Speech framework. This provides low-latency, privacy-preserving voice control without requiring network requests.

## Architecture

### OnDeviceSTTService.swift
- Singleton service managing speech recognition
- Uses `SFSpeechRecognizer` with on-device processing
- Publishes voice commands via Combine framework

### Key Features
- **On-device processing**: `requiresOnDeviceRecognition = true`
- **Real-time recognition**: Partial results enabled for responsive feedback
- **Command patterns**: Flexible phrase matching for start/stop commands

## Voice Commands

### Start Recording Commands
- "begin"
- "start"
- "i'm ready"
- "let's go"
- "do it"
- "record"
- "recording"

### Stop Recording Commands
- "stop"
- "finish"
- "done"
- "cancel"
- "abort"
- "that's enough"
- "end recording"
- "stop recording"

## Audio Session Management

The STT service uses `.playAndRecord` category with these options:
- `.duckOthers`: Reduces volume of other audio
- `.allowBluetooth`: Enables Bluetooth headset support

This configuration is compatible with TTS playback without session conflicts.

## Integration with RecordingViewModel

```swift
// Listen for voice commands
voiceCommandCancellable = onDeviceSTT.$lastCommand
    .compactMap { $0 }
    .sink { [weak self] command in
        self?.handleVoiceCommand(command)
    }
```

## Permissions Required

### Info.plist Entries
- `NSSpeechRecognitionUsageDescription`: "We use speech recognition to allow voice commands for hands-free recording control."
- `NSMicrophoneUsageDescription`: "We need microphone access to record your voice commands and golf swing videos."

## Error Handling

The service handles:
- Permission denied states
- Device availability checks
- Recognition task failures with automatic restart

## Debug Logging

When `Config.isDebugEnabled` is true, the service logs:
- Command detection details
- Recognition status changes
- Permission states