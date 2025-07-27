# File Storage System

## Google Cloud Storage Configuration

### Bucket Setup
- **Bucket Name**: `fg-video`
- **Region**: Multi-regional for global access
- **Storage Class**: Standard for active video files, Nearline for archived content
- **Versioning**: Enabled for data protection
- **Lifecycle Rules**: Automatic transition to cheaper storage classes

### Authentication
- **Service Account**: `backend/gcs-credential.json` (protected in .gitignore)
- **Scope**: Storage read/write permissions
- **IAM Roles**: Storage Object Admin for the application service account

## File Organization Structure

### Directory Layout
```
fg-video/
├── videos/
│   ├── original/
│   │   └── {user_id}/
│   │       └── {video_id}.mp4
│   └── processed/
│       └── {user_id}/
│           └── {video_id}_composited.mp4
├── thumbnails/
│   └── {user_id}/
│       └── {video_id}_thumb.jpg
└── temp/
    └── {processing_id}/
        ├── frames/
        └── working_files/
```

### File Naming Convention
- **Original Videos**: `{video_id}.mp4`
- **Composited Videos**: `{video_id}_composited.mp4`
- **Thumbnails**: `{video_id}_thumb.jpg`
- **Temporary Files**: `{processing_id}_{timestamp}_{type}.ext`

## Upload Pipeline

### Video Upload Process
1. **Client Upload**: Direct upload to GCS via signed URLs
2. **Metadata Storage**: Store file info in PostgreSQL
3. **Validation**: Verify file integrity and format
4. **Processing Queue**: Add to analysis queue
5. **Cleanup**: Remove temporary files after processing

### Upload Validation
- **File Size**: Max 500MB per video
- **Duration**: Max 2 minutes for free tier, 5 minutes for pro
- **Format**: MP4, MOV, AVI supported
- **Resolution**: Min 720p, Max 4K
- **Frame Rate**: 30fps minimum, 120fps maximum

## Video Processing Pipeline

### Frame Extraction
```python
# Extract frames at key intervals
frames_path = f"temp/{processing_id}/frames/"
extract_frames(video_path, frames_path, interval=0.1)  # Every 0.1 seconds
```

### Pose Detection Processing
```python
# MediaPipe pose analysis on extracted frames
pose_data = []
for frame in extracted_frames:
    pose_results = mediapipe_pose.process(frame)
    pose_data.append(extract_landmarks(pose_results))
```

### Video Composition
```python
# Overlay analysis data on original video
composited_video = overlay_analysis_data(
    original_video=video_path,
    pose_data=pose_data,
    swing_phases=analysis_results['swing_phases'],
    alignment_scores=analysis_results['alignment_data']
)
```

## Storage Service Implementation

### Core Operations
Located in `backend/services/storage_service.py`:

```python
class StorageService:
    def upload_video(self, file_data, user_id, video_id)
    def download_video(self, blob_name)
    def delete_video(self, blob_name)
    def generate_signed_url(self, blob_name, expiration=3600)
    def upload_composited_video(self, file_path, user_id, video_id)
    def create_thumbnail(self, video_blob_name)
```

### URL Generation
- **Signed URLs**: For secure direct uploads from mobile clients
- **Public URLs**: For processed video playback (with appropriate permissions)
- **Expiration**: 1 hour for uploads, 24 hours for downloads

## File Lifecycle Management

### Retention Policies
- **Original Videos**: 
  - Free tier: 30 days
  - Pro tier: 1 year
- **Processed Videos**: Same as original
- **Temporary Files**: 24 hours (automatic cleanup)
- **Thumbnails**: Same as associated video

### Cleanup Automation
- **Scheduled Job**: Daily cleanup of expired files
- **Database Triggers**: Mark files for deletion when records are soft-deleted
- **Storage Lifecycle**: GCS lifecycle rules for automatic archival

### Data Recovery
- **Soft Delete**: 30-day grace period before permanent deletion
- **Version Control**: GCS versioning for accidental overwrites
- **Backup Strategy**: Cross-region replication for critical user data

## Performance Optimization

### CDN Integration
- **Global Distribution**: CloudFlare or GCS CDN for video delivery
- **Edge Caching**: Cache processed videos at edge locations
- **Bandwidth Optimization**: Adaptive bitrate streaming for mobile

### Compression Settings
- **Original Storage**: Minimal compression to preserve quality for analysis
- **Delivery Compression**: H.264 with optimized settings for mobile playback
- **Thumbnail Generation**: JPEG with 80% quality, 320x240 resolution

### Monitoring
- **Storage Usage**: Track per-user storage consumption
- **Transfer Costs**: Monitor bandwidth usage and optimize delivery
- **Error Tracking**: Log upload failures and retry mechanisms