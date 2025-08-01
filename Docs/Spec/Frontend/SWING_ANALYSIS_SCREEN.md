

# SWING ANALYSIS SCREEN

Users come to the screen immediately after submitting a video for processing and also in order to view a previously processed video. 
Suitable placeholder should be implemented while the video is currently processing.

## Layout

1. **Video thumbnail** with play button overlay:
   - Fixed height based on 16:9 aspect ratio
   - No rounded corners
   - Shows busy indicator while offline/loading/caching TTS
   - Play button appears only when TTS coaching audio is cached
   - Thumbnail extracted from middle of video
2. **Overview box** with some stats: Overall Score, Avg Head Speed, and one compliment and one critique. Icons indicating each.
3. **Analysis Section** -- A series of thumbnails at key moments with the analysis for those moments underneath
4. **Summary Box** -- An additional summary box with more analysis.

The whole page is scrollable.


### Video Processing Mode

While the video is being processed we should show a simplified version of this screen:

* Thumbnail with animated busy/processing indicator (no overlay text)
* Slim progress bar based on feedback from server/polling
* Small text indicating status:
  - "Waiting for connectivity..." when offline
  - "Uploading video" when uploading
  - "Processing swing data..." when analyzing
  - "Preparing coaching audio..." when caching TTS
* The analysis section below is always visible but collapsed
* Expandable section shows appropriate placeholder content based on state
* When processing and TTS caching completes, play button appears on thumbnail


## Post-Analysis

* Analysis returns JSON with swing phases, key points, and coaching script
* Stills are extracted from video at timestamps for each swing phase
* Key moment thumbnails and feedback form entries in Analysis section
* Summary text is supplied from the analysis JSON
* Completion sound plays when analysis is ready
* If user navigated away, progress toast appears at bottom
* All coaching script lines are parsed and cached as TTS audio
* Play button only appears after all TTS phrases are cached




## Journeys

* Click on video thumbnail play button (only when TTS ready) → Navigate to Video Playback Screen
* Scroll to see Analysis and Summary content
* Tap expandable section to see placeholder/preview content during processing
* Click back → Return to Home Screen
* If offline → See busy indicator and "Waiting for connectivity..."
* When connection restored → Processing resumes automatically



## Data Storage

### Folder-Based Storage Structure

Each analysis session is stored in a folder named with a timestamp-based ID for easy sorting:

```
Documents/
├── SwingAnalyses/
│   ├── 2024-08-01-143052/          # Analysis ID (timestamp-based)
│   │   ├── video.mp4               # Original video
│   │   ├── thumbnail.jpg           # Video thumbnail (midpoint)
│   │   ├── analysis.json           # Analysis results
│   │   ├── report.json             # Generated report with all data
│   │   ├── keyframes/              # Extracted still images
│   │   │   ├── setup_090.jpg       # Frame at setup phase
│   │   │   ├── backswing_150.jpg   # Frame at backswing
│   │   │   ├── downswing_180.jpg   # Frame at downswing
│   │   │   └── follow_through_210.jpg
│   │   └── tts_cache/              # Cached TTS audio files
│   │       ├── coaching_line_0.mp3 # "Alright, let's take a look..."
│   │       ├── coaching_line_1.mp3 # "Starting with your setup..."
│   │       └── ...                 # All coaching script lines
│   └── 2024-08-01-151230/          # Another analysis session
│       └── ...
```

### Analysis Report JSON Structure

The `report.json` file contains all analysis data with references to media files:

```json
{
  "id": "2024-08-01-143052",
  "created_at": "2024-08-01T14:30:52Z",
  "video_path": "video.mp4",
  "thumbnail_path": "thumbnail.jpg",
  "overall_score": 85,
  "avg_head_speed": "95 mph",
  "top_compliment": "Great tempo and balance",
  "top_critique": "Work on hip rotation",
  "summary": "Your swing shows good fundamentals...",
  "key_moments": [
    {
      "phase": "Setup",
      "timestamp": 1.5,
      "frame_path": "keyframes/setup_090.jpg",
      "feedback": "Good posture, maintain spine angle"
    },
    ...
  ],
  "coaching_script": [
    {
      "text": "Alright, let's take a look at your golf swing.",
      "start_frame": 0,
      "tts_path": "tts_cache/coaching_line_0.mp3"
    },
    ...
  ]
}
```

## Additional Notes

* Analysis ID uses timestamp format: YYYY-MM-DD-HHMMSS for natural sorting
* All media files are stored relative to the analysis folder
* TTS files are cached per-analysis to ensure availability
* Thumbnail is extracted from video midpoint for best representation
* Key frame extraction happens at exact timestamps from analysis 







