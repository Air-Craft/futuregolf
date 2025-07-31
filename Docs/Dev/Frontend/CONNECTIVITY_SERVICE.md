# Connectivity Service Documentation

## Overview

The ConnectivityService provides real-time network monitoring and connectivity state management for the FutureGolf application. It uses Apple's Network framework to detect network changes and provides a callback system for components to respond to connectivity restoration.

## Architecture

### Core Components

1. **ConnectivityService** - Main singleton service for network monitoring
2. **ConnectivityAware Protocol** - Protocol for components that need connectivity notifications
3. **Network Framework Integration** - Uses NWPathMonitor for real-time network state

### Features

- Real-time network connectivity monitoring
- Connection type detection (WiFi, Cellular, Ethernet)
- Callback system for connectivity restoration
- Host reachability testing
- Debug mode connectivity toasts
- MainActor-isolated for UI safety

## Implementation Details

### Service Initialization

```swift
@MainActor
class ConnectivityService: ObservableObject {
    static let shared = ConnectivityService()
    
    @Published var isConnected: Bool = true
    @Published var connectionType: NWInterface.InterfaceType?
    
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "com.futuregolf.connectivity")
}
```

### Key Methods

#### Monitor Connectivity State
```swift
// Check current connectivity
let isConnected = ConnectivityService.shared.isConnected

// Get connection type
let connectionType = ConnectivityService.shared.connectionType
```

#### Register for Connectivity Restoration
```swift
let callbackId = ConnectivityService.shared.onConnectivityRestored {
    // Perform actions when connectivity is restored
    print("Network connection restored!")
}

// Remove callback when no longer needed
ConnectivityService.shared.removeCallback(callbackId)
```

#### Check Host Reachability
```swift
let isReachable = await ConnectivityService.shared.isHostReachable("https://api.example.com")
```

### ConnectivityAware Protocol

Components can adopt the ConnectivityAware protocol for easier integration:

```swift
protocol ConnectivityAware {
    func onConnectivityRestored()
    func onConnectivityLost()
}

// Example usage
class MyService: ConnectivityAware {
    init() {
        setupConnectivityMonitoring()
    }
    
    func onConnectivityRestored() {
        // Resume network operations
    }
    
    func onConnectivityLost() {
        // Pause network operations
    }
}
```

## Integration with Other Services

### TTS Cache Manager Integration

The TTSCacheManager uses ConnectivityService to:
- Postpone cache warming when offline
- Resume cache operations when connectivity is restored
- Provide better error handling for network failures

```swift
private func setupConnectivityMonitoring() {
    connectivityCallbackId = ConnectivityService.shared.onConnectivityRestored { [weak self] in
        guard let self = self else { return }
        
        if !self.isCacheWarming && self.shouldRefreshCache() {
            print("🗣️💾 TTS Cache: Connectivity restored, starting cache warm-up")
            self.warmCache()
        }
    }
}
```

### Debug Mode Features

When `Config.isDebugEnabled` is true:
- Shows toast notifications for connectivity changes
- Displays connection type in toasts
- Provides visual feedback for network state

## Configuration

No specific configuration required. The service automatically:
- Starts monitoring on first access
- Uses system network state
- Integrates with ToastManager for debug notifications

## Best Practices

1. **Always Check Connectivity Before Network Operations**
   ```swift
   guard ConnectivityService.shared.isConnected else {
       // Handle offline state
       return
   }
   ```

2. **Register Callbacks for Critical Operations**
   ```swift
   private var connectivityCallbackId: UUID?
   
   init() {
       connectivityCallbackId = ConnectivityService.shared.onConnectivityRestored {
           self.retryFailedOperations()
       }
   }
   
   deinit {
       if let id = connectivityCallbackId {
           ConnectivityService.shared.removeCallback(id)
       }
   }
   ```

3. **Use Host Reachability for Specific Endpoints**
   ```swift
   let serverReachable = await ConnectivityService.shared.isHostReachable(Config.serverBaseURL)
   ```

## Error Handling

The service handles all internal errors gracefully:
- Network monitor failures are logged but don't crash
- Host reachability returns false on any error
- Callbacks are safely executed with weak self references

## Testing

### Manual Testing
1. Toggle airplane mode to test connectivity changes
2. Switch between WiFi and cellular
3. Use Network Link Conditioner for various network conditions

### Debug Mode Testing
Enable debug mode to see toast notifications:
```bash
DEBUG_MODE=1 # In launch environment
```

## Performance Considerations

- Singleton pattern ensures single monitor instance
- Callbacks use weak references to prevent retain cycles
- Network state changes are debounced internally by NWPathMonitor
- Host reachability checks use HEAD requests with 5-second timeout