# Recent Updates Summary

This document summarizes the recent updates made to the FutureGolf application.

## Date: 2025-08-01 - MAJOR ARCHITECTURE REFACTOR ✨

### Video Analysis Pipeline - Complete Rewrite

**🚨 BREAKING CHANGE:** Complete architectural refactor of the video analysis system for simplicity and reliability.

**Problem:** The original system was overly complex, different from the working CLI tool (`analyze_video.py`), and causing upload stalling issues.

**Solution:** Clean architecture that works exactly like the proven `analyze_video.py` CLI tool.

#### Key Changes:
- ✅ **New Clean Service**: `video_analysis_service.py` mirrors CLI logic exactly
- ✅ **Auto-Background Processing**: Upload triggers analysis automatically via `BackgroundTasks`
- ✅ **Simplified API**: Single polling endpoint, same JSON format as CLI
- ✅ **Removed Complexity**: Deleted pose analysis, separate coaching generation
- ✅ **Enhanced Upload**: Auto-triggers analysis, no manual triggering needed

#### New Workflow:
```
Upload → Auto-Analysis → Poll Results (same JSON as CLI)
```

#### Files Modified:
- ✅ `backend/services/video_analysis_service.py` - New clean implementation
- ✅ `backend/api/video_analysis.py` - Simplified polling API  
- ✅ `backend/api/video_upload.py` - Auto-trigger integration

#### Files Removed:
- ❌ `pose_analysis_service.py`, `test_pose_analysis.py` (unused complexity)
- 📦 Legacy files backed up with `.bak` extension

**Impact:** Upload stalling resolved, consistent CLI behavior, simplified maintenance.

See: `Docs/Dev/Backend/VIDEO_ANALYSIS_CLEAN_ARCHITECTURE.md` for complete details.

---

## Previous Updates - 2025-08-01

### iOS App Updates

#### 1. Fixed TTS Speech Truncation
- **Issue**: TTS was being cut off when recording ended via voice command
- **Solution**: Removed duplicate `stopSpeaking()` calls that were interrupting the completion message
- **Files Modified**: `RecordingViewModel.swift`

#### 2. Comprehensive Offline Support
- **New Components**:
  - `AnalysisStorageManager.swift` - Local persistence of analysis records
  - `VideoProcessingService.swift` - Queue management and retry logic
- **Features**:
  - Videos queue for upload when offline
  - Automatic retry when connection restored
  - Graceful UI states (no error popups)
  - "Waiting for connectivity..." messages
- **Files Modified**: Multiple files including `SwingAnalysisView.swift`, `SwingAnalysisViewModel.swift`

#### 3. Enhanced Video Thumbnails
- **Change**: Thumbnails now generated from midway point of video instead of first frame
- **Benefit**: More representative preview of the swing
- **Files Modified**: `SwingAnalysisViewModel.swift`

#### 4. Improved Navigation
- **Change**: Back button in SwingAnalysisView navigates to PreviousAnalyses instead of Home
- **Navigation Flow**: Home → Record → Analysis → (Back) → Previous Analyses
- **Files Modified**: `SwingAnalysisView.swift`

#### 5. Enhanced Toast System
- **New Features**:
  - Multiple simultaneous toasts (up to 3)
  - Custom IDs for targeted dismissal
  - Persistent toasts with `duration: .infinity`
  - Swipe-to-dismiss gesture
- **Usage Example**:
  ```swift
  // Show persistent toast
  ToastManager.shared.show("Waiting...", duration: .infinity, id: "wait")
  // Dismiss by ID
  ToastManager.shared.dismiss(id: "wait")
  ```
- **Files Modified**: `ToastManager.swift`

#### 6. Audio Route Management
- **New Component**: `AudioRouteManager.swift`
- **Issue Fixed**: TTS was forcing phone speaker instead of using active audio device
- **Features**:
  - Respects user's audio device choice (headphones, Bluetooth, etc.)
  - Monitors audio route changes
  - Shows debug toasts for route changes
- **Configuration Changes**:
  - Removed `.defaultToSpeaker` option
  - Added `.allowBluetooth`, `.allowBluetoothA2DP`, `.allowAirPlay`
- **Files Modified**: `TTSService.swift`, `OnDeviceSTTService.swift`

### Backend Updates

#### 1. Added Missing Dependency
- **Issue**: `ModuleNotFoundError: No module named 'google.generativeai'`
- **Solution**: Added `google-generativeai>=0.3.0` to `pyproject.toml`
- **Impact**: Backend can now start successfully with Gemini AI integration

### Documentation Updates

Created/Updated the following documentation:
1. `Docs/Dev/Frontend/OFFLINE_SUPPORT.md` - Comprehensive offline architecture guide
2. `Docs/Dev/Frontend/AUDIO_ROUTING.md` - Audio route management documentation
3. `Docs/Dev/Frontend/TOAST_SYSTEM.md` - Updated with multi-toast support
4. `Docs/Dev/RECENT_UPDATES.md` - This summary document

## Testing Recommendations

1. **Offline Mode**: Test recording with airplane mode, verify queuing and auto-retry
2. **Audio Routing**: Test with headphones/Bluetooth connected
3. **Toast System**: Trigger multiple toasts to verify stacking
4. **Navigation**: Verify Back button behavior in analysis screen
5. **Thumbnails**: Check that video thumbnails show mid-swing frame

## Known Issues

None reported at this time.

## Next Steps

1. Monitor for any edge cases in offline handling
2. Consider adding background upload support
3. Potential enhancement: Multiple audio device selection UI