# Offline Support Implementation

This document describes the offline support architecture implemented in the FutureGolf iOS app.

## Overview

The app provides comprehensive offline support to ensure a smooth user experience even without network connectivity. Videos are queued for upload when offline and automatically processed when connectivity is restored.

## Architecture Components

### 1. AnalysisStorageManager

**Location**: `ios/FutureGolf/FutureGolf/AnalysisStorageManager.swift`

Manages local persistence of analysis records with the following features:

- **Status Tracking**: Tracks analysis status (pending, uploading, analyzing, completed, failed)
- **Local Storage**: Persists analysis data as JSON in the documents directory
- **Thumbnail Storage**: Stores video thumbnails as JPEG data within the analysis record
- **Progress Tracking**: Monitors upload progress for each analysis

#### Key Methods:
- `saveAnalysis()` - Creates new analysis record
- `updateStatus()` - Updates analysis status
- `updateThumbnail()` - Stores video thumbnail
- `getPendingAnalyses()` - Retrieves analyses waiting for upload
- `updateAnalysisResult()` - Stores completed analysis results

### 2. VideoProcessingService

**Location**: `ios/FutureGolf/FutureGolf/VideoProcessingService.swift`

Handles background processing and retry logic:

- **Queue Management**: Processes pending uploads in order
- **Connectivity Monitoring**: Listens for network changes
- **Automatic Retry**: Retries failed uploads when connection restored
- **Task Cancellation**: Cancels active uploads when going offline

#### Key Features:
- Singleton pattern for app-wide queue management
- Processes oldest videos first
- Handles concurrent upload limit
- Cancels tasks gracefully when offline

### 3. ConnectivityService

**Location**: `ios/FutureGolf/FutureGolf/ConnectivityService.swift`

Monitors network connectivity using Apple's Network framework:

- **Real-time Monitoring**: Uses NWPathMonitor for instant updates
- **Connection Type**: Tracks WiFi, Cellular, or other connection types
- **Callback System**: Notifies subscribers when connectivity changes
- **Host Reachability**: Can check if specific servers are reachable

## UI/UX Flow

### Recording Flow

1. User records video normally
2. On completion, video is saved locally with status "pending"
3. If online: Upload starts immediately
4. If offline: Video queued, user sees "Waiting for connectivity..."

### Analysis Screen States

#### Online State
- Shows processing progress
- Displays analysis results when complete
- Normal flow with progress indicators

#### Offline State
- Shows video thumbnail with offline overlay
- Displays "Waiting for connectivity..." message
- Progress bar at 0%
- Toast notification for connectivity status

### Previous Analyses View

Shows all analyses with status indicators:
- **Pending**: WiFi slash icon overlay, "Waiting for connection"
- **Uploading**: Progress percentage shown
- **Analyzing**: "Analyzing..." status
- **Completed**: Green checkmark, full results available
- **Failed**: Red indicator, will retry automatically

## Implementation Details

### Navigation Flow

```
Home → Record → Analysis → (Back) → Previous Analyses
```

The Back button in SwingAnalysisView navigates to Previous Analyses, not Home.

### Graceful Degradation

- **No Error Popups**: All errors handled gracefully with appropriate UI states
- **Always Navigate**: Navigation to analysis screen always succeeds
- **Status Messages**: Clear, user-friendly messages for each state
- **Automatic Recovery**: No user action needed when connection restored

### Data Persistence

Analysis records stored as JSON with structure:
```swift
struct StoredAnalysis {
    let id: String
    let videoURL: URL
    let recordedAt: Date
    var status: AnalysisStatus
    var analysisResult: AnalysisResult?
    var uploadProgress: Double
    var thumbnailData: Data?
}
```

## Toast Notifications

The app shows toast notifications for connectivity changes:
- **"Waiting for connectivity..."** - Persistent toast when offline
- **"Connection restored"** - Brief success toast when online
- **Multiple toast support** - Can show multiple toasts simultaneously

## Best Practices

1. **Always Queue**: Never block user flow due to connectivity
2. **Clear Messaging**: Use specific messages like "Waiting for connectivity..." not generic "Preparing..."
3. **Visual Feedback**: Show appropriate icons and progress indicators
4. **Automatic Handling**: Don't require user intervention for retries
5. **Preserve Data**: Never lose user recordings due to connectivity issues

## Testing Offline Mode

1. Enable Airplane Mode before recording
2. Record a swing
3. Verify "Waiting for connectivity..." appears
4. Disable Airplane Mode
5. Verify automatic upload and processing begins
6. Check Previous Analyses view shows correct status throughout

## Future Enhancements

- Background upload support using BackgroundTasks framework
- Bandwidth detection for optimal video quality
- Selective sync options for cellular vs WiFi
- Export options for offline viewing