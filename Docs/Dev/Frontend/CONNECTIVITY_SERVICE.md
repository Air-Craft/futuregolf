# Connectivity Service Documentation

## Overview

The FutureGolf app implements a robust connectivity monitoring system that provides unified network and server health checking. This service ensures the app gracefully handles offline scenarios and automatically resumes operations when connectivity is restored.

## Architecture

### ConnectivityService

The `ConnectivityService` is a singleton that monitors both network connectivity and server reachability:

- **Network Monitoring**: Uses Apple's `NWPathMonitor` to detect network availability
- **Server Health Polling**: Polls the server health endpoint every 1 second when the app is active
- **Unified Status**: Provides a single `isConnected` property that combines both network and server status

### Key Features

1. **1-Second Server Polling**: Server health is checked every second while the app is active
2. **App Lifecycle Management**: Polling is suspended when app goes to background, resumed on foreground
3. **Pub-Sub Pattern**: Services can subscribe to connectivity changes via Combine publishers
4. **Synchronous Access**: `isLikelyConnected` property provides best-guess based on last check
5. **Toast Notifications**: Automatic user notifications when connectivity status changes
6. **Unified Messaging**: No distinction to user between "no internet" and "server down"

## Implementation Details

### Service Structure

```swift
@MainActor
class ConnectivityService: ObservableObject {
    static let shared = ConnectivityService()
    
    // Published properties for UI binding
    @Published var isConnected: Bool = false // Combined network + server connectivity
    @Published var connectionType: NWInterface.InterfaceType?
    
    // Server connectivity tracking
    private(set) var lastConnectivityCheck: Date = .distantPast
    private var isNetworkAvailable: Bool = false
    private var isServerReachable: Bool = false
}
```

### Server Health Check

The service polls the server health endpoint with a 2-second timeout:

```swift
private let serverHealthEndpoint = "\(Config.serverBaseURL)/api/v1/health"

private func checkServerHealth() async {
    guard isNetworkAvailable else {
        updateConnectivityStatus(serverReachable: false)
        return
    }
    
    lastConnectivityCheck = Date()
    
    // Poll with 2-second timeout
    var request = URLRequest(url: url)
    request.httpMethod = "GET"
    request.timeoutInterval = 2.0
}
```

### Connectivity States

- **Connected**: Both network is available AND server is reachable
- **Disconnected**: Either no network OR server is unreachable

Note: The app makes no distinction to the user between "no internet" and "server down" - both show as "Waiting for connectivity..."

### Lifecycle Management

```swift
// App becomes active
func applicationDidBecomeActive() {
    isAppActive = true
    // Check immediately
    Task { await checkServerHealth() }
    // Resume 1-second polling
    startServerHealthPolling()
}

// App resigns active
func applicationWillResignActive() {
    isAppActive = false
    // Suspend polling to save battery
    serverCheckTimer?.invalidate()
}
```

## Integration Points

### 1. App Launch

On app launch, connectivity status is checked and shown if offline:

```swift
// In FutureGolfApp.warmTTSCache()
if !ConnectivityService.shared.isConnected {
    ToastManager.shared.show("Waiting for connectivity...", 
                           type: .warning, 
                           duration: .infinity, 
                           id: "connectivity")
}
```

### 2. TTS Cache Warming

When connectivity is restored, the TTS cache automatically warms:

```swift
private func onConnectivityRestored() {
    // 1. Warm TTS cache
    TTSService.shared.cacheManager.warmCache()
    
    // 2. Resume any pending swing analyses
    // This will be handled by SwingAnalysisViewModel subscribers
}
```

### 3. Swing Analysis Processing

Pending swing analyses automatically resume when connectivity returns:

```swift
// VideoProcessingService monitors connectivity
connectivityService.$isConnected
    .sink { isConnected in
        if isConnected {
            self?.processPendingAnalyses()
        } else {
            self?.cancelAllActiveTasks()
        }
    }
```

### 4. SwingAnalysisViewModel

The view model subscribes to connectivity changes and queues analyses when offline:

```swift
private func setupConnectivityMonitoring() {
    connectivityCancellable = connectivityService.$isConnected
        .sink { [weak self] isConnected in
            if isConnected && self?.isOffline == true {
                // Resume processing
                self?.retryProcessing()
            }
        }
}
```

## User Experience

### Toast Notifications

- **Launch**: If offline on launch, shows persistent "Waiting for connectivity..." toast
- **Lost Connection**: Shows persistent warning toast
- **Restored Connection**: Shows brief success toast "Connected"

### Offline Behavior

When offline, the app:
1. Queues swing analyses for later processing
2. Shows video thumbnails but delays analysis
3. Prevents TTS cache warming
4. Displays "Waiting for connectivity..." in processing views

## Usage Examples

### Subscribing to Connectivity Changes

```swift
class MyViewModel: ObservableObject {
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        ConnectivityService.shared.$isConnected
            .sink { isConnected in
                if isConnected {
                    // Handle connection restored
                } else {
                    // Handle connection lost
                }
            }
            .store(in: &cancellables)
    }
}
```

### Using Best-Guess Connectivity

```swift
// For immediate checks without waiting for next poll
if ConnectivityService.shared.isLikelyConnected {
    // Proceed with operation
}
```

### Registering for Restoration Callbacks

```swift
let callbackId = ConnectivityService.shared.onConnectivityRestored {
    // Resume operations
}

// Clean up when done
ConnectivityService.shared.removeCallback(callbackId)
```

## Configuration

The connectivity service uses the following configuration values:

- **Server Base URL**: `Config.serverBaseURL`
- **Health Check Endpoint**: `/api/v1/health`
- **Health Check Timeout**: 2 seconds
- **Polling Interval**: 1 second (when app is active)
- **Cache Validity**: 5 seconds for `isLikelyConnected`

## Debugging

Enable debug mode to see detailed connectivity logs:

```
🌐 App became active, resuming connectivity monitoring
🌐 Network available via WiFi
🌐 Server reachable: true
🌐 Connectivity restored
🌐 Connectivity lost
🌐 App resigning active, suspending connectivity monitoring
```

## Best Practices

1. **Always check connectivity before network operations**
   ```swift
   guard ConnectivityService.shared.isConnected else {
       // Queue for later or show offline UI
       return
   }
   ```

2. **Use the unified `isConnected` property**
   - Don't check network and server separately
   - The service handles the combination logic

3. **Subscribe to changes rather than polling**
   ```swift
   ConnectivityService.shared.$isConnected
       .sink { /* handle changes */ }
   ```

4. **Handle both connectivity loss and restoration**
   - Queue operations when offline
   - Automatically retry when restored

5. **Clean up callbacks in deinit**
   ```swift
   deinit {
       if let id = connectivityCallbackId {
           ConnectivityService.shared.removeCallback(id)
       }
   }
   ```

## Performance Considerations

- **Battery Efficiency**: Polling is suspended when app is in background
- **Network Efficiency**: Uses lightweight health check endpoint
- **Debouncing**: Route changes are debounced to prevent rapid reconfigurations
- **Main Thread**: All UI updates happen on main thread automatically

## Testing

### Manual Testing

1. **Network Toggle**: Turn airplane mode on/off
2. **Server Down**: Stop backend server while app is running
3. **Background/Foreground**: Test polling suspension/resumption
4. **Network Types**: Switch between WiFi, cellular, and ethernet

### Debug Features

- Toast notifications show connectivity changes
- Console logs track polling and state changes
- `isLikelyConnected` for synchronous testing

## Technical Notes

- The service runs on the `@MainActor` for UI safety
- Network monitoring uses a dedicated dispatch queue
- Server polling uses `Timer` on the main run loop
- All published properties trigger UI updates automatically
- Callbacks are stored with UUID identifiers for safe removal