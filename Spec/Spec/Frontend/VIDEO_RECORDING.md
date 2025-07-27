# Video Recording Specification

## Camera Setup and Configuration

### Recording Parameters
- **Frame Rate**: 60fps minimum for smooth swing analysis
- **Resolution**: 1080p default, 4K optional for pro users
- **Orientation**: Portrait mode with automatic rotation lock
- **Duration**: 30 seconds default (configurable via constants file)
- **Format**: MP4 with H.264 encoding for compatibility

### Camera Positioning
- **Default Camera**: Rear camera for better quality
- **Positioning Guide**: On-screen overlay showing ideal user placement
- **Distance Indicator**: Visual guide for optimal recording distance
- **Framing Assistant**: Real-time feedback on user positioning

## Positioning Assistance System

### AI-Powered Setup Guidance

#### Snapshot Analysis
```javascript
// Take positioning snapshots every 2 seconds
const POSITIONING_INTERVAL = 2000; // 2 seconds
const positioningAnalysis = {
  captureInterval: POSITIONING_INTERVAL,
  analysisEndpoint: '/api/v1/positioning/analyze',
  maxAttempts: 10 // 20 seconds total
};
```

#### Analysis Criteria
- **User in Frame**: Detect if person is visible and properly framed
- **Full Body Visible**: Ensure complete swing motion will be captured
- **Adequate Space**: Verify sufficient room for full swing
- **Lighting Quality**: Check for adequate lighting conditions
- **Background Clarity**: Ensure clean background for pose detection

#### Positioning Instructions
- **Distance Guidance**: 
  - "Move closer to the camera"
  - "Step back a bit"
  - "Perfect distance!"
- **Horizontal Positioning**:
  - "Move a little to the left"
  - "Shift right slightly"
  - "Great positioning!"
- **Angle Adjustments**:
  - "Turn slightly toward the camera"
  - "Face more directly forward"
  - "Excellent angle!"

### TTS Integration for Setup

#### Instruction Sequence
1. **Initial Greeting**: "Let's analyze your swing. I'll help you get positioned perfectly"
2. **Positioning Phase**: Real-time spoken guidance based on AI analysis
3. **Setup Confirmation**: "That's perfect! Get ready with your club"
4. **Recording Start**: "Recording begins in 3... 2... 1... Take your swing!"

#### Voice Settings
- **Voice Selection**: Friendly, clear female voice for instructions
- **Speed**: Slightly slower than normal speaking pace
- **Volume**: Automatically adjusts based on device volume settings

## Recording Interface

### Visual Elements

#### Camera View
- **Live Preview**: Full-screen camera feed with overlay elements
- **Positioning Overlay**: Semi-transparent guide showing ideal user placement
- **Grid Lines**: Optional rule-of-thirds grid for composition
- **Focus Indicator**: Tap-to-focus with visual confirmation

#### Recording Controls
```javascript
const recordingControls = {
  recordButton: {
    style: 'large circular red button',
    states: ['ready', 'recording', 'processing'],
    animations: ['pulse on ready', 'solid red when recording']
  },
  stopButton: {
    visible: 'only during recording',
    position: 'bottom right',
    confirmation: 'double-tap to stop early'
  },
  cancelButton: {
    position: 'top left',
    confirmation: 'confirm before canceling'
  }
};
```

#### Progress Indicators
- **Time Display**: Large, easily readable countdown timer
- **Progress Bar**: Visual representation of recording progress
- **Phase Indicators**: Show current recording phase (setup/recording/processing)

### Audio Feedback

#### Recording Cues
- **Start Confirmation**: Clear audio signal when recording begins
- **Time Markers**: Soft beeps at 10s and 20s intervals
- **Countdown Warning**: Audible countdown from 5 seconds remaining
- **Completion Signal**: Distinct sound when recording ends

#### Background Audio Handling
- **Music Pause**: Automatically pause other audio during recording
- **Microphone Muting**: Disable audio recording to focus on visual analysis
- **Notification Silence**: Suppress system notifications during recording

## Recording States and Transitions

### State Management
```javascript
const recordingStates = {
  SETUP: 'positioning_assistance',
  READY: 'ready_to_record', 
  RECORDING: 'actively_recording',
  PROCESSING: 'upload_and_analysis',
  COMPLETED: 'ready_for_review'
};
```

### State Transitions
1. **Setup → Ready**: AI confirms proper positioning
2. **Ready → Recording**: User taps record or auto-start after countdown
3. **Recording → Processing**: Recording duration complete or manual stop
4. **Processing → Completed**: Video uploaded and analysis initiated

### Error States
- **Camera Permission Denied**: Show settings redirect with instructions
- **Insufficient Storage**: Warning with cleanup suggestions
- **Camera Hardware Error**: Fallback options or restart recommendation

## Video Quality Optimization

### Automatic Settings
- **Exposure Adjustment**: Auto-exposure with bias toward user area
- **Focus Management**: Continuous autofocus on user during recording
- **Stabilization**: Electronic image stabilization if available
- **Quality Adaptation**: Adjust settings based on device capabilities

### Manual Controls (Advanced)
- **Exposure Lock**: Tap and hold to lock exposure
- **Manual Focus**: Slide control for manual focus adjustment
- **Recording Quality**: Toggle between quality and file size optimization

## Performance Considerations

### Memory Management
- **Buffer Optimization**: Efficient video buffer management
- **Background Processing**: Minimize CPU usage during recording
- **Thermal Management**: Monitor device temperature and adjust if needed

### Battery Optimization
- **Power Efficiency**: Optimize camera settings for battery life
- **Background App Limits**: Pause non-essential background processes
- **Low Power Mode**: Graceful degradation when battery is low

### Device Compatibility
- **Older Devices**: Fallback to 30fps if 60fps unavailable
- **Storage Limits**: Compress video if storage space is limited
- **Camera Capabilities**: Adapt to available camera features per device