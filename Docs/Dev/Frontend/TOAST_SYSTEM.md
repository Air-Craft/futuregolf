# Toast Notification System Documentation

## Overview

The Toast System provides a global, non-blocking way to display brief messages and progress indicators to users. It now supports multiple simultaneous toasts, custom IDs for targeted dismissal, and persistent toasts.

## Architecture

### Core Components

1. **ToastManager** - Singleton managing active toasts and queue
2. **Toast Model** - Data structure for toast content and styling
3. **ToastView** - SwiftUI view for rendering individual toasts
4. **ToastOverlay** - ViewModifier for app-wide integration

### Features

- **Multiple Simultaneous Toasts** - Display up to 3 toasts at once
- **Custom Toast IDs** - Dismiss specific toasts by ID
- **Persistent Toasts** - Toasts that don't auto-dismiss
- **Multiple toast types** (info, success, warning, error)
- **Progress toast with real-time updates**
- **Swipe to dismiss** - Swipe down gesture support
- **Automatic queuing** - Additional toasts queue when limit reached
- **Beautiful animations and styling**

## Implementation Details

### Toast Types

```swift
enum ToastType {
    case info     // Blue - General information
    case success  // Green - Successful operations
    case warning  // Orange - Warnings or cautions
    case error    // Red - Errors or failures
}
```

### Basic Usage

#### Simple Messages
```swift
// Show a success message
ToastManager.shared.show("Operation completed!", type: .success)

// Show an error with custom duration
ToastManager.shared.show("Network error", type: .error, duration: 5.0)

// Info toast (default type)
ToastManager.shared.show("Processing your request...")
```

#### Persistent Toasts with Custom IDs
```swift
// Show persistent toast with custom ID
ToastManager.shared.show(
    "Waiting for connectivity...", 
    type: .warning, 
    duration: .infinity,  // Never auto-dismiss
    id: "connectivity"
)

// Later, dismiss by ID
ToastManager.shared.dismiss(id: "connectivity")

// Show completion
ToastManager.shared.show("Connection restored", type: .success)
```

#### Progress Toasts
```swift
// Create a progress toast
let progressId = ToastManager.shared.showProgress("Uploading...", progress: 0.0)

// Update progress
ToastManager.shared.updateProgress(id: progressId, progress: 0.5)
ToastManager.shared.updateProgress(id: progressId, progress: 0.75, label: "Almost done...")

// Dismiss when complete
ToastManager.shared.dismissProgress(id: progressId)
ToastManager.shared.show("Upload complete!", type: .success)
```

### App Integration

Add toast overlay to your app's root view:

```swift
@main
struct FutureGolfApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .withToastOverlay() // Add this modifier
        }
    }
}
```

## Toast Queue Management

The system now supports multiple active toasts:

1. **Active Toasts**: Up to 3 toasts displayed simultaneously
2. **Queued Toasts**: Additional toasts wait in queue
3. **Stacking**: Toasts stack vertically with 8pt spacing
4. **Persistent Toasts**: Don't count against auto-dismiss timers

Example flow:
```swift
// These will all show simultaneously (up to 3)
ToastManager.shared.show("First message")      
ToastManager.shared.show("Second message")     
ToastManager.shared.show("Third message")      

// Fourth will queue until a slot opens
ToastManager.shared.show("Fourth message")     

// Persistent toast takes a slot but won't auto-dismiss
ToastManager.shared.show("Persistent", duration: .infinity, id: "persist")
```

## Visual Design

### Toast Appearance
- Rounded corners with shadow
- Icon based on toast type
- White text on colored background
- Positioned above tab bar (50pt from bottom)

### Progress Toast
- Includes linear progress bar
- Shows percentage text
- Updates label dynamically
- No auto-dismiss (must be dismissed programmatically)

### Animations
- Slide up from bottom on show
- Fade out and slide down on dismiss
- Spring animation for smooth appearance
- Tap animation feedback

## Integration Examples

### TTS Cache Progress
```swift
#if DEBUG
progressToastId = ToastManager.shared.showProgress("Caching TTS...", progress: 0.0)

// Update during caching
ToastManager.shared.updateProgress(
    id: toastId, 
    progress: progress,
    label: "Caching TTS... (\(currentSuccess)/\(totalCount))"
)

// Complete
ToastManager.shared.dismissProgress(id: toastId)
ToastManager.shared.show("TTS cache ready!", type: .success)
#endif
```

### Connectivity Status
```swift
#if DEBUG
$isConnected
    .removeDuplicates()
    .dropFirst()
    .sink { isConnected in
        if isConnected {
            ToastManager.shared.show("Connected via \(typeString)", type: .success)
        } else {
            ToastManager.shared.show("No network connection", type: .error)
        }
    }
#endif
```

### API Operations
```swift
Task {
    ToastManager.shared.show("Uploading video...")
    
    do {
        try await uploadVideo()
        ToastManager.shared.show("Upload successful!", type: .success)
    } catch {
        ToastManager.shared.show("Upload failed: \(error)", type: .error)
    }
}
```

## Configuration

### Toast Duration
- Default: 3.0 seconds
- Progress toasts: No auto-dismiss (`.infinity`)
- Customizable per toast

### Toast Styling
Modify `Toast.ToastType` for custom colors:
```swift
var backgroundColor: Color {
    switch self {
    case .info: return Color.blue.opacity(0.9)
    case .success: return Color.green.opacity(0.9)
    case .warning: return Color.orange.opacity(0.9)
    case .error: return Color.red.opacity(0.9)
    }
}
```

### Position and Layout
Adjust in `ToastOverlay`:
```swift
.padding(.bottom, 50) // Above tab bar
.padding(.horizontal, 16) // Side margins
```

## Best Practices

1. **Keep Messages Brief**
   ```swift
   // Good
   ToastManager.shared.show("Saved!", type: .success)
   
   // Avoid
   ToastManager.shared.show("Your changes have been successfully saved to the server", type: .success)
   ```

2. **Use Appropriate Types**
   - `.success` - Completed actions
   - `.error` - Failed operations
   - `.warning` - Important notices
   - `.info` - General feedback

3. **Progress Toast Management**
   ```swift
   // Always store the ID
   let progressId = ToastManager.shared.showProgress("Loading...")
   
   // Always dismiss when done
   defer { ToastManager.shared.dismissProgress(id: progressId) }
   ```

4. **Avoid Toast Spam**
   - Don't show multiple similar toasts
   - Use progress toasts for long operations
   - Consider grouping related messages

## Performance Considerations

- Singleton pattern ensures single instance
- Efficient queue management
- Minimal memory footprint
- SwiftUI animations optimized by system

## Testing

### Manual Testing
```swift
// Test all toast types
ToastManager.shared.show("Info toast", type: .info)
ToastManager.shared.show("Success toast", type: .success)
ToastManager.shared.show("Warning toast", type: .warning)
ToastManager.shared.show("Error toast", type: .error)

// Test progress
let id = ToastManager.shared.showProgress("Testing progress...")
for i in 0...10 {
    ToastManager.shared.updateProgress(id: id, progress: Double(i) / 10.0)
    try await Task.sleep(nanoseconds: 500_000_000)
}
ToastManager.shared.dismissProgress(id: id)

// Test queue
for i in 1...5 {
    ToastManager.shared.show("Message \(i)")
}
```

### UI Testing
```swift
// Check toast appears
app.staticTexts["Upload complete!"].waitForExistence(timeout: 5)

// Verify toast dismisses
XCTAssertFalse(app.staticTexts["Upload complete!"].exists)
```

## Troubleshooting

### Toast Not Appearing
1. Ensure `.withToastOverlay()` is added to root view
2. Check if ToastManager is on MainActor
3. Verify no view is covering the toast area

### Progress Not Updating
1. Store the progress ID correctly
2. Use same ID for all updates
3. Ensure updates are on MainActor

### Queue Issues
1. Toasts show in FIFO order
2. Progress toasts can interrupt queue
3. Dismissed toasts trigger next in queue