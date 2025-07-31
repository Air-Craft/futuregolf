# TTS Caching System Documentation

## Overview

The TTS Caching System pre-generates and stores Text-to-Speech audio files for the recording journey, eliminating synthesis delays during critical user interactions. This ensures immediate audio playback when users navigate through the swing recording process.

## Architecture

### Core Components

1. **TTSPhrases** - Enum defining all cacheable phrases
2. **TTSCacheManager** - Manages cache storage, warming, and retrieval
3. **TTSCacheMetadata** - Tracks cache state and refresh timing
4. **Integration with TTSService** - Seamless cache usage during playback

### Storage Structure

```
Documents/
└── TTSCache/
    ├── metadata.json        # Cache metadata and manifest
    ├── audio/              # Cached audio files
    │   ├── [hash].mp3      # SHA256-based filenames
    │   └── ...
    └── temp/               # Temporary files during refresh
```

## Implementation Details

### TTSPhrases Enum

Defines all cacheable phrases with SHA256-based filenames:

```swift
enum TTSPhrases: String, CaseIterable {
    case setupPositioning = "Alright. Get yourself into a position..."
    case recordingStarted = "Great. I'm now recording..."
    case firstSwingDone = "Great. Take another when you're ready."
    case secondSwingDone = "Ok one more to go."
    case recordingComplete = "That's great. I'll get to work analyzing..."
    case recordingTimeout = "That's taken longer than I had planned..."
    
    var filename: String {
        "\(hash).mp3"
    }
    
    var hash: String {
        // SHA256 hash of the text for consistent filenames
    }
}
```

### Cache Manager Features

#### Cache Warming
Initiated on app launch to pre-generate all audio:

```swift
func warmCache() {
    // Check if force refresh is enabled
    if Config.ttsForceCacheRefreshOnLaunch {
        clearCache()
    }
    
    // Check cache age
    if !shouldRefreshCache() {
        return // Cache is fresh
    }
    
    // Start background refresh
    refreshCacheInBackground()
}
```

#### Atomic Cache Replacement
Ensures cache validity during updates:

1. Download new audio to temp directory
2. Verify all files downloaded successfully
3. Atomically move files to final location
4. Update metadata only after successful replacement

#### Progress Tracking
In DEBUG mode, shows progress toast:
- Current phrase being cached
- Overall progress percentage
- Success/failure status

### Integration with TTSService

The TTSService automatically uses cached audio when available:

```swift
public func speak(_ text: String) async {
    // Check cache first
    if let cachedData = await cacheManager.getCachedAudio(for: text) {
        audioData = cachedData
    } else {
        // Fall back to synthesis
        audioData = try await synthesizeSpeech(text: text)
    }
    
    // Play audio...
}
```

## Configuration

### Config.swift Settings

```swift
// Cache refresh interval (24 hours default)
static let ttsCacheRefreshInterval: TimeInterval = 86400.0

// Force cache refresh on launch (debug)
static let ttsForceCacheRefreshOnLaunch: Bool = {
    return ProcessInfo.processInfo.environment["TTS_FORCE_REFRESH"] == "1"
}()

// Cache directory name
static let ttsCacheDirectory = "TTSCache"

// TTS synthesis timeout
static let ttsSynthesisTimeout: TimeInterval = 20.0
```

### Environment Variables

- `TTS_FORCE_REFRESH=1` - Force cache refresh on launch
- `DEBUG_MODE=1` - Enable progress toasts and detailed logging

## Cache Lifecycle

### 1. App Launch
- Cache manager checks connectivity first
- If offline, registers for connectivity restoration
- Validates cache age against refresh interval
- Initiates warming only when connected

### 2. Background Warming
- Downloads all phrases concurrently
- Shows progress in DEBUG mode
- Handles network failures gracefully
- Will not start if no network connection

### 3. Runtime Usage
- TTSService checks cache before synthesis
- Falls back to real-time synthesis if not cached
- Saves synthesized audio to cache if cacheable

### 4. Cache Refresh
- Automatic daily refresh (configurable)
- Force refresh via environment variable
- Atomic replacement ensures no downtime

## Connectivity Integration

The cache manager integrates with ConnectivityService:

### Connectivity Check on Warm Cache
```swift
func warmCache() {
    // Check connectivity first
    guard ConnectivityService.shared.isConnected else {
        print("No network connection, postponing cache warm-up")
        
        // Register for connectivity restoration
        if shouldRefreshCache() {
            registerForConnectivityRestoration()
        }
        return
    }
    
    // Proceed with cache warming...
}
```

### Automatic Retry on Connection
```swift
// One-time callback when connectivity restored
connectivityCallbackId = ConnectivityService.shared.onConnectivityRestored {
    if !self.isCacheWarming && self.shouldRefreshCache() {
        self.warmCache()
    }
}
```

Benefits:
- Prevents cache attempts when offline
- Automatically resumes when connected
- No wasted network requests
- Seamless user experience

## Debug Features

### Progress Toast
Shows real-time caching progress:
```
Caching TTS... (3/6)
[████████░░░░░░░] 50%
```

### Debug Logging
Detailed logs with 🗣️💾 prefix:
```
🗣️💾 TTS Cache: Starting cache warm-up process...
🗣️💾 TTS Cache: Total phrases to cache: 6
🗣️💾 TTS Cache: ✅ Successfully cached phrase setupPositioning (45632 bytes)
```

### Debug Commands
```swift
// List all cached files
TTSService.shared.cacheManager.debugListCachedFiles()

// Clear cache
TTSService.shared.cacheManager.clearCache()

// Check cache status
let status = TTSService.shared.cacheManager.getCacheStatus()
```

## Error Handling

### Network Errors
- Gracefully handles timeouts and connection failures
- Keeps existing cache on partial failure
- Retries on connectivity restoration

### Storage Errors
- Logs but doesn't crash on file system errors
- Falls back to real-time synthesis
- Cleans up temp files on failure

## Best Practices

1. **Always Cache Recording Journey Phrases**
   - These are time-sensitive and benefit most from caching
   - Defined in TTSPhrases enum for consistency

2. **Monitor Cache Health**
   ```swift
   let status = cacheManager.getCacheStatus()
   if !status.exists || status.phraseCount < TTSPhrases.allCases.count {
       // Cache incomplete, may need refresh
   }
   ```

3. **Handle Edge Cases**
   - User reaches recording screen before cache ready
   - Network unavailable during refresh
   - Storage space limitations

## Performance Metrics

- **Cache Hit Rate**: Should be 100% for defined phrases
- **Warming Time**: ~2-5 seconds for all phrases (network dependent)
- **Storage Size**: ~300KB for 6 phrases (50KB average per phrase)
- **Playback Latency**: <50ms from cache vs 1-3s for synthesis

## Testing

### Manual Testing
1. Force refresh: `TTS_FORCE_REFRESH=1`
2. Monitor progress toasts in DEBUG mode
3. Test offline behavior with airplane mode
4. Verify atomic replacement by interrupting refresh

### Automated Testing
```swift
// Test cache warming
let cacheManager = TTSCacheManager()
cacheManager.warmCache()

// Verify cache contents
let status = cacheManager.getCacheStatus()
XCTAssertEqual(status.phraseCount, TTSPhrases.allCases.count)

// Test cache retrieval
let audio = await cacheManager.getCachedAudio(for: TTSPhrases.setupPositioning.rawValue)
XCTAssertNotNil(audio)
```