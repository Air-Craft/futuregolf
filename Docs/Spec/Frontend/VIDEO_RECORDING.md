# Video Recording Specification

## Camera Setup and Configuration

### Recording Parameters
- **Frame Rate**: 120fps optimal, 60fps minimum for smooth swing analysis
- **Resolution**: 1080p default
- **Orientation**: Portrait mode with automatic rotation lock
- **Duration**: We'll count the swings to determine completion
- **Format**: MP4 with H.264 encoding for compatibility

### Camera Positioning
- **Default Camera**: Rear camera for better quality. But user can switch to front camera via icon
- **Positioning Guide**: On-screen overlay showing ideal user placement
- **Distance Indicator**: Visual guide for optimal recording distance
- **Framing Assistant**: Real-time feedback on user positioning


## Swing Recording Interface

### Visual Elements

#### Camera View
- **Live Preview**: Full-screen camera feed with overlay elements
- **Auto Focus**: Auto focuses on main person in frame

#### Recording Controls
- ** Cancel Button**: In the upper left. Pauses TTS and prompts to cancel/erase recording.
- Do not include standard record/play/pause buttons

#### Video Camera UI Elements
- **Time Display**: Time display with millisecond resolution
- **Progress Indicator**: 3 circles, green/white checks after that swing has completed. Only show once recording has begun
- **Positioning Indicator**: Fade white line art indicating ideal user placement. Button switch to left-handed mode (mirrors the graphic). Fades once recording begins.



### Operation Phases

- **Setup Phase**: Video preview is visible along with Positioning Indicator. Listens to user for "begin" signal (see below)
- **Recording Phase**: Video recording begins, stills silently taken to feed to swing counter (see below)


#### State Transitions
1. **Setup → Recording**: Automatic with voice instruction (see above)
2. **Recording → Processing**: Automatic after user has taken 3 swings (actual number set in hard coded config for now). App segways to Swing Analsys screen


#### User "Begin" Signal (Setup → Recording)
- Stream opened to Langserve API endpoint
- On device SST translates words and streams to endpoint
- Endpoint queries LLM prompting for "Has the user indicated clearly they are ready to begin recording?". LLM should return true/false and confidence.
- If true with high confidence, begin Recording Phase


#### Automatic Swing Detection
- Stills silently taken every 0.25 seconds
- Stills resized, recompressed on device to achieve minimum size for fastest transfer and llm processing
- Still submitted to server endpoint (langserv?) for processing
- LLM indicates whether the sequence of images thus far constitutes a complete golf swing.
- If so, a sound and visual indicator are made in the app and the LLM/langchain context is reset 
- If exceed config set threshold (e.g. 3 min), automatically end with TTS feedback

### Audio Feedback

#### Recording Cues
- **Start Confirmation**: Clear audio signal when recording begins, TTS: "Great. I'm now recording. Begin swinging when you are ready."
- **Count Signal**: Audible beep after user takes a swing. TTS: "Great. Take another when you're ready.",  "Ok one more to go."
- **Completion Signal**: Distinct completion sound when recording ends. TTS: "That's great. I'll get to work analyzing your swings."
- **Overtime Signal**: TTS: "That's taken longer than I had planned. I'll analyze what we have."

#### Background Audio Handling
- **Music Pause**: Automatically pause other audio during recording
- **Microphone Muting**: Disable audio recording to focus on visual analysis
- **Notification Silence**: Suppress system notifications during recording


### Error States
- **Camera Permission Denied**: Show settings redirect with instructions
- **Insufficient Storage**: Warning with cleanup suggestions
- **Camera Hardware Error**: Fallback options or restart recommendation

## Video Quality Optimization

- **Exposure Adjustment**: Auto-exposure with bias toward user area
- **Focus Management**: Continuous autofocus on user during recording
- **Stabilization**: Electronic image stabilization if available
- **Quality Adaptation**: Adjust settings based on device capabilities


