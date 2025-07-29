# AI Swing Analysis

## Google Gemini Integration

### Video Analysis Process
1. **Video Upload**: Accept high-frame rate video (60fps recommended)
2. **Frame Extraction**: Process key frames for analysis (every 30 frames / 0.1s)
3. **Gemini Submission**: Submit video or frame sequence to Google Gemini 2.5
4. **Analysis Output**: Structured JSON with swing phases, timing, and feedback

### Gemini v2 API Configuration
- **Client**: `google-genai` library with centralized client architecture
- **Model**: `gemini-2.5-flash` for standard analysis, `gemini-2.5-pro` for detailed analysis
- **File Upload**: `client.aio.files.upload()` for video submission
- **Content Generation**: `client.aio.models.generate_content()` with structured prompts

### Analysis Prompts
Located in `backend/prompts/`:
- `gemini_video_analysis.txt` - Main swing analysis prompt
- `coaching_script_commentary.txt` - Coaching feedback generation
- `video_analysis_swing_coaching.txt` - Combined analysis and coaching

## MediaPipe Pose Detection

### Body Angle Analysis
- **Shoulder alignment**: Detect shoulder plane relative to target line
- **Head position**: Track head movement throughout swing
- **Hip rotation**: Measure hip turn in backswing and downswing
- **Spine angle**: Monitor posture changes during swing

### Key Pose Landmarks
- Shoulders (left/right)
- Hips (left/right) 
- Head/nose
- Hands/wrists
- Knees (left/right)

### Frame-by-Frame Processing
- Extract pose data every 2-3 frames
- Calculate angles and relative positions
- Generate alignment scores (0-1 scale)
- Detect swing phases based on pose changes

## Analysis Output Structure

### Swing Phases
```json
{
  "swing_phases": [
    {
      "phase": "setup",
      "start_frame": 0,
      "end_frame": 45,
      "duration_seconds": 1.5,
      "quality_score": 0.85,
      "feedback": "Good setup position with proper alignment"
    },
    {
      "phase": "backswing", 
      "start_frame": 46,
      "end_frame": 120,
      "duration_seconds": 2.5,
      "quality_score": 0.72,
      "feedback": "Slight over-rotation in shoulders"
    }
  ]
}
```

### Alignment Data
```json
{
  "alignment_data": [
    {
      "frame": 60,
      "timestamp": 2.0,
      "alignments": {
        "shoulders": 1,
        "head": 1, 
        "hips": 0,
        "spine": 1
      },
      "feedback": "Keep hips more square to target"
    }
  ]
}
```

### Coaching Script
```json
{
  "coaching_script": [
    {
      "timestamp": 2.5,
      "text": "Notice how your shoulders are properly aligned here",
      "emphasis": "positive"
    },
    {
      "timestamp": 4.2,
      "text": "Try to keep your head steady during the backswing",
      "emphasis": "improvement"
    }
  ]
}
```

## Quality Assurance

### Single Swing Detection
- Enhanced prompts to prevent multi-swing hallucination
- Frame validation to ensure realistic timing
- Quality scoring to identify best swing in sequence

### Error Handling
- Graceful fallback for pose detection failures
- Alternative analysis methods when MediaPipe data incomplete
- Retry logic for transient AI service errors

### Performance Optimization
- Frame sampling to reduce token costs
- Video resolution optimization for analysis speed
- Parallel processing of pose detection and AI analysis