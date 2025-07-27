# Video Playback Specification

## Custom Video Player

### Playback Features

- **Play/Pause toggle**: Play/pause video
- **Skip Back/Forward**: Fast-forward and rewind 5 seconds
- **Coach audio mute toggle button**: Mute/unmute audio 
- **Text Tips Show/Hide**: Show/hide text tips on video
- **Precision Scrubbing**: Frame-by-frame navigation during seek
- **Thumbnail Previews**: Show video thumbnails while scrubbing
- **Timestamp Display**: Frame-accurate time display (MM:SS.FF format)
- **Playback Speed toggle**: 0.5x, 0.25x, 1.0x. 0.5x default playback


### Text Overlays
- **Swing**: [Swing Count]. Starts at 0. Increases by 1 at each downswing.
- **Score**: [0.0-10.0]. Resets to ... prior to next swing.
- **Clubhead speed**: [100mph]
- **Text Tips**: Showing text for critiques of the swing (bottom left aligned and shifting up when others are added)
    - Text shows from start time until end of that swing


### TTS Coaching Integration
- Coaching statements triggered at indicated time stamps and rendered into voice with preferred TTS provider (see OVERVIEW.md)
- **TTS on/off toggle**: Turn on/off TTS

#### Smart Resume Logic
- **Seek Behavior**: When user seeks, find next TTS entry after new position
- **Speed Independence**: TTS plays at normal speed regardless of video speed
- **Interruption Handling**: Gracefully handle user interactions during TTS
- **Visual Sync**: None for now


### Responsive Design
- **Portrait/Landscape Mode**: Force orientation for which the video was recorded (could be either). Align all video controls accordingly.

