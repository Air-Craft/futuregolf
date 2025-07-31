# Text-to-Speech (TTS) Service

## Overview
The TTS service provides voice feedback using a backend OpenAI-based API with queuing and audio session management. The service includes an intelligent caching system that pre-generates common audio phrases for instant playback during the recording journey.

## Related Documentation
- [TTS Caching System](./TTS_CACHING.md) - Details on the audio caching implementation
- [Connectivity Service](./CONNECTIVITY_SERVICE.md) - Network monitoring for TTS operations

## Configuration

### Server Endpoint
- URL: `{Config.serverBaseURL}/api/v1/tts/coaching`
- Method: POST
- Content-Type: application/json

### Request Parameters
```json
{
  "text": "string",
  "voice": "onyx",
  "model": "tts-1-hd",
  "speed": 0.9
}
```

### Timeout Configuration
- Synthesis timeout: `Config.ttsSynthesisTimeout` (default: 20.0 seconds)
- Configurable via Config.swift for all network operations

## Audio Session Setup

The service uses `.playAndRecord` mode with:
- `.duckOthers`: Reduces other audio volume during speech
- `.defaultToSpeaker`: Routes audio to speaker by default

## Queue Management

- Speech requests are queued to prevent overlapping
- Sequential processing ensures one utterance at a time
- Queue can be cleared with `stopSpeaking()`

## Caching System

The TTS service includes automatic caching for frequently used phrases:

### Cache Features
- Pre-generates audio on app launch for instant playback
- Daily cache refresh (configurable)
- Atomic cache updates ensure continuous availability
- Network-aware: postpones operations when offline
- Progress tracking in DEBUG mode

### Cached Phrases
All recording journey instructions are cached:
- Setup positioning
- Recording started
- Swing feedback (1st, 2nd)
- Recording complete
- Timeout message

See [TTS Caching Documentation](./TTS_CACHING.md) for implementation details.

## Network Configuration

Uses `URLSession.shared` with default timeout settings for reliable connectivity.

## Error Handling

When TTS requests fail:
1. Error is logged with timing information
2. Queue processing continues with next item
3. Optional fallback to iOS system TTS (currently disabled)

## Usage Example

```swift
// From RecordingScreen
viewModel.ttsService.speakText("Alright. Get yourself into a position where we can see your whole swing, and let me know when you're ready.")
```

## Common TTS Messages

1. **Setup Phase**: "Alright. Get yourself into a position where we can see your whole swing, and let me know when you're ready."
2. **Recording Started**: "Great. I'm now recording. Begin swinging when you're ready."
3. **First Swing**: "Great. Take another when you're ready."
4. **Second Swing**: "Ok one more to go."
5. **Completion**: "That's great. I'll get to work analyzing your swings."
6. **Timeout**: "That's taken longer than I had planned. I'll analyze what we have."

## Debugging

### Log Prefixes
- `🗣️ TTS:` - General TTS operations
- `🗣️💾 TTS Cache:` - Cache-related operations

### Environment Variables
- `TTS_FORCE_REFRESH=1` - Force cache refresh on launch
- `DEBUG_MODE=1` - Enable progress toasts and verbose logging

### Debug Commands
```swift
// Check cache status
TTSService.shared.cacheManager.debugListCachedFiles()

// Force cache refresh
TTSService.shared.cacheManager.clearCache()
TTSService.shared.cacheManager.warmCache()
```