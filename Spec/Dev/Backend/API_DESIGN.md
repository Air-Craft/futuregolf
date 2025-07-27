# Backend API Design

## Core Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration with OAuth support
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/oauth` - OAuth integration (Google, LinkedIn, Microsoft)
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user profile

### Video Management
- `POST /api/v1/videos/upload` - Upload video for analysis
- `GET /api/v1/videos/{id}` - Get video metadata
- `DELETE /api/v1/videos/{id}` - Delete video

### Video Analysis
- `POST /api/v1/video-analysis/{video_id}` - Start analysis process
- `GET /api/v1/video-analysis/{analysis_id}/status` - Poll analysis progress
- `GET /api/v1/video-analysis/{analysis_id}` - Get completed analysis results
- `GET /api/v1/video-analysis/user/analyses` - Get user's analysis history

### Text-to-Speech
- `POST /api/v1/tts/generate` - Generate TTS audio from text
- `POST /api/v1/tts/stream` - Stream TTS audio with real-time generation
- `GET /api/v1/tts/health` - TTS service health check

### Health & Status
- `GET /health` - General health check
- `GET /api/v1/status` - API status and version

## Request/Response Formats

### Video Upload
```json
{
  "video_file": "binary_data",
  "metadata": {
    "duration": 30.5,
    "resolution": "1920x1080",
    "fps": 60
  }
}
```

### Analysis Response
```json
{
  "analysis_id": "uuid",
  "video_id": "uuid",
  "status": "completed",
  "swing_analysis": {
    "swing_phases": [
      {
        "phase": "setup",
        "start_frame": 0,
        "end_frame": 45,
        "quality_score": 0.85
      }
    ],
    "pose_data": { ... },
    "alignment_feedback": [ ... ]
  },
  "coaching_script": [
    {
      "timestamp": 2.5,
      "text": "Great setup position..."
    }
  ],
  "composited_video_url": "https://storage.googleapis.com/..."
}
```

## Polling System
- Frontend polls `/status` endpoint every 2 seconds during analysis
- Analysis states: `queued`, `processing`, `completed`, `failed`
- Progress indicators for video upload, pose detection, AI analysis, video composition

## Error Handling
- Standard HTTP status codes
- Structured error responses with error codes and messages
- Rate limiting for analysis endpoints (free vs pro users)
- Graceful degradation for AI service failures