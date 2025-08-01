# Video Analysis - Clean Architecture (v2)

## Overview

The video analysis system has been completely refactored to use a clean, simple architecture based on the working `analyze_video.py` logic. This eliminates complexity and ensures consistent behavior between CLI and API usage.

## Architecture Principles

### 1. **Single Source of Truth**
- All video analysis uses the same core logic as `analyze_video.py`
- Same Gemini API integration, prompt handling, and response processing
- Consistent JSON output format across CLI and API

### 2. **Automatic Background Processing**
- Video upload automatically triggers analysis (no manual triggering)
- Uses FastAPI `BackgroundTasks` for async processing
- Clean separation between upload and analysis phases

### 3. **Simple Polling API**
- iOS polls single endpoint for results
- Clear status progression: `pending` → `processing` → `completed`/`failed`
- Complete analysis JSON returned when ready

## Core Components

### VideoAnalysisService (`services/video_analysis_service.py`)

Clean service that mirrors `analyze_video.py` functionality:

```python
class CleanVideoAnalysisService:
    async def analyze_video_file(self, video_path: str) -> Dict[str, Any]:
        # Exact same logic as analyze_video.py:
        # 1. Get video properties (duration, fps, frames)
        # 2. Load and format coaching prompt
        # 3. Upload to Gemini and wait for processing
        # 4. Generate analysis with safety settings
        # 5. Parse and validate JSON response
        # 6. Add metadata and return

    async def analyze_video_from_storage(self, video_id: int, user_id: int):
        # Complete workflow:
        # 1. Get video from database
        # 2. Download from storage to temp file
        # 3. Call analyze_video_file()
        # 4. Save results to database
        # 5. Clean up temp files
```

**Key Features:**
- Same Gemini client configuration as CLI
- Same safety settings and generation config
- Same prompt loading and formatting logic
- Same error handling and cleanup
- Returns identical JSON structure

### Video Upload API (`api/video_upload.py`)

Enhanced to auto-trigger analysis:

```python
@router.post("/upload")
async def upload_video(background_tasks: BackgroundTasks, ...):
    # 1. Validate and upload file to storage
    # 2. Create video record in database
    # 3. Auto-trigger background analysis:
    background_tasks.add_task(
        analysis_service.analyze_video_from_storage,
        video.id,
        user_id
    )
    # 4. Return upload confirmation with analysis_status: "queued"
```

### Video Analysis API (`api/video_analysis.py`)

Simplified polling-based API:

```python
# Main polling endpoint
GET /api/v1/video-analysis/video/{video_id}
# Returns:
# - If pending/processing: Status info
# - If completed: Full analysis JSON (same as analyze_video.py)
# - If failed: Error details

# Lightweight status check
GET /api/v1/video-analysis/status/{video_id}
# Returns just status without full JSON payload

# User's analysis history
GET /api/v1/video-analysis/user/analyses
```

## API Flow

### 1. Video Upload
```http
POST /api/v1/videos/upload
Content-Type: multipart/form-data

{
  "file": <video_file>,
  "user_id": 1,
  "title": "Golf Swing",
  "description": "Practice session"
}
```

**Response:**
```json
{
  "success": true,
  "video_id": 123,
  "status": "uploaded",
  "analysis_status": "queued"
}
```

### 2. Analysis Polling
```http
GET /api/v1/video-analysis/video/123
```

**While Processing:**
```json
{
  "success": true,
  "analysis": {
    "id": 456,
    "status": "processing",
    "message": "Analysis in progress",
    "created_at": "2025-01-01T12:00:00Z"
  }
}
```

**When Complete:**
```json
{
  "success": true,
  "analysis": {
    "id": 456,
    "status": "completed",
    "ai_analysis": {
      "swings": [...],
      "summary": {...},
      "coaching_script": {
        "lines": [
          {"text": "Great setup position...", "start_frame_number": 10},
          {"text": "Work on your backswing...", "start_frame_number": 45}
        ]
      },
      "_metadata": {
        "analysis_duration": 12.5,
        "video_duration": 8.2,
        "model_used": "gemini-2.5-flash"
      }
    }
  }
}
```

## JSON Response Format

The API returns the exact same JSON structure as `analyze_video.py`:

```json
{
  "swings": [
    {
      "score": 7,
      "phases": {
        "setup": {"start_frame": 5, "end_frame": 15},
        "backswing": {"start_frame": 15, "end_frame": 45},
        "downswing": {"start_frame": 45, "end_frame": 65},
        "follow_through": {"start_frame": 65, "end_frame": 85}
      },
      "comments": ["Good tempo", "Work on hip rotation"]
    }
  ],
  "summary": {
    "highlights": ["Consistent tempo", "Good balance"],
    "improvements": ["Hip rotation", "Follow through"]
  },
  "coaching_script": {
    "lines": [
      {
        "text": "Let's analyze your swing. Starting with your setup...",
        "start_frame_number": 5
      },
      {
        "text": "Notice how your backswing has good extension...",
        "start_frame_number": 25
      }
    ]
  },
  "_metadata": {
    "analysis_duration": 12.5,
    "video_duration": 8.2,
    "video_fps": 30.0,
    "frame_count": 246,
    "model_used": "gemini-2.5-flash",
    "analysis_timestamp": "2025-01-01T12:00:00Z"
  }
}
```

## Database Integration

### VideoAnalysis Model
```sql
CREATE TABLE video_analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    video_id INTEGER REFERENCES videos(id),
    status analysis_status_enum,
    ai_analysis JSONB,  -- Complete Gemini response
    video_duration FLOAT,
    analysis_confidence FLOAT,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    error_message TEXT
);
```

**Key Points:**
- `ai_analysis` contains the complete JSON from Gemini
- `coaching_script.lines[]` is included in the main analysis
- No separate storage for pose analysis (removed)
- Status transitions: `PENDING` → `PROCESSING` → `COMPLETED`/`FAILED`

## Removed Components

### Deprecated (Backed up with .bak extension)
- `services/pose_analysis_service.py` - MediaPipe integration
- `services/video_analysis_service_legacy.py` - Complex legacy service
- `api/video_analysis_legacy.py` - Complex legacy API
- All pose analysis endpoints and dependencies

### Why Removed
- Pose analysis was not used in production
- Added complexity without value
- Different from working `analyze_video.py` logic
- Caused processing delays and errors

## Testing

### CLI Validation
```bash
# Test the core analysis logic
cd backend
pdm run python analyze_video.py path/to/video.mp4

# Should produce same JSON as API will return
```

### API Testing
```bash
# 1. Upload video
curl -X POST http://localhost:8000/api/v1/videos/upload \
  -F "file=@test_video.mp4" \
  -F "user_id=1"

# 2. Poll for results
curl http://localhost:8000/api/v1/video-analysis/video/123

# 3. Verify JSON structure matches analyze_video.py output
```

## Configuration

### Required Environment Variables
```bash
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=postgresql://...
GOOGLE_CLOUD_STORAGE_BUCKET=your_bucket
```

### Dependencies
```bash
pdm install  # Installs all required packages including:
# - google-genai (Gemini AI)
# - opencv-python (cv2)
# - fastapi
# - sqlalchemy
```

## Monitoring

### Logging
- Analysis start/completion logged with video_id
- Gemini API call timing and response size
- Error details for failed analyses
- Temp file cleanup confirmation

### Key Metrics
- Analysis completion time
- Success/failure rates
- Video processing queue size
- Background task execution

## Troubleshooting

### Common Issues

**Analysis stuck in processing:**
- Check background task worker is running
- Verify Gemini API key is valid
- Check storage download permissions

**JSON parsing errors:**
- Gemini response format changed
- Safety settings blocking content
- Prompt formatting issues

**Import errors:**
- Missing cv2: `pip install opencv-python`
- Missing genai: `pip install google-genai`
- Database connection issues

### Debug Tools
```python
# Test service directly
from services.video_analysis_service import get_clean_video_analysis_service
service = get_clean_video_analysis_service()
result = await service.analyze_video_file("test.mp4")
```

## Migration Notes

### From Legacy System
1. Old pose analysis endpoints removed
2. Manual analysis triggering eliminated  
3. Complex status management simplified
4. Same JSON format maintained for iOS compatibility

### iOS Integration Changes
- No changes to upload endpoint
- Simplified polling (single endpoint)
- Same JSON response structure
- No manual analysis triggering needed