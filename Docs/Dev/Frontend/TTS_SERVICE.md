# Text-to-Speech (TTS) Service

## Overview
The TTS service provides voice feedback using a backend OpenAI-based API with queuing and audio session management.

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

## Audio Session Setup

The service uses `.playAndRecord` mode with:
- `.duckOthers`: Reduces other audio volume during speech
- `.defaultToSpeaker`: Routes audio to speaker by default

## Queue Management

- Speech requests are queued to prevent overlapping
- Sequential processing ensures one utterance at a time
- Queue can be cleared with `stopSpeaking()`

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

Enable verbose logging by checking console output for lines prefixed with "🎵 TTS:"