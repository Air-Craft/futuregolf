# Migration Guide - Video Analysis Architecture v2

## Overview

The video analysis system has been completely refactored from a complex multi-service architecture to a clean, simple system based on the working `analyze_video.py` CLI tool.

## What Changed

### Before (Legacy Architecture)
```
Upload → Manual Trigger → Complex Service → Pose Analysis → Coaching Generation → Multiple Endpoints
```

### After (Clean Architecture v2)  
```
Upload → Auto-Background Analysis → Simple Polling → Complete Results
```

## Breaking Changes

### API Endpoints

#### ❌ REMOVED Endpoints:
```http
POST /api/v1/video-analysis/analyze/{video_id}  # Manual trigger (no longer needed)
GET /api/v1/video-analysis/{analysis_id}        # Analysis ID based (changed to video ID)
GET /api/v1/video-analysis/pose-analysis/{id}   # Pose analysis (removed)
GET /api/v1/video-analysis/body-angles/{id}     # Body angles (removed)  
GET /api/v1/video-analysis/biomechanical-scores/{id}  # Biomech (removed)
```

#### ✅ NEW/UPDATED Endpoints:
```http
GET /api/v1/video-analysis/video/{video_id}     # Main polling endpoint (NEW)
GET /api/v1/video-analysis/status/{video_id}    # Status check (UPDATED to use video_id)
GET /api/v1/video-analysis/user/analyses        # User analyses (UNCHANGED)
DELETE /api/v1/video-analysis/analysis/{id}     # Delete analysis (UNCHANGED)
```

### Response Format Changes

#### Analysis Response Structure
**✅ UNCHANGED:** The core analysis JSON structure remains identical to maintain iOS compatibility.

```json
{
  "swings": [...],
  "summary": {...}, 
  "coaching_script": {
    "lines": [...]
  }
}
```

**✅ NEW:** Added `_metadata` section with analysis timing and video properties.

#### Status Response Structure
**Before:**
```json
{
  "analysis_id": 123,
  "status": "completed",
  "progress": 100
}
```

**After:**
```json
{
  "video_id": 456,
  "analysis_id": 123,
  "status": "completed", 
  "message": "Analysis completed successfully"
}
```

## Code Migration

### iOS Client Changes

#### Upload Flow (No Changes Required)
```swift
// Upload endpoint unchanged
let uploadURL = "\(baseURL)/videos/upload"
// Upload still returns video_id
```

#### Analysis Polling (URL Change Only)
```swift
// OLD - Analysis ID based
let analysisURL = "\(baseURL)/video-analysis/\(analysisId)"

// NEW - Video ID based (simpler)
let analysisURL = "\(baseURL)/video-analysis/video/\(videoId)"
```

#### No Manual Triggering Needed
```swift
// OLD - Manual trigger after upload
await apiClient.triggerAnalysis(videoId: videoId)

// NEW - Automatic (remove trigger call)
// Analysis starts automatically after upload completes
```

### Backend Service Integration

#### Service Import Changes
```python
# OLD
from services.video_analysis_service_legacy import get_video_analysis_service
from services.pose_analysis_service import get_pose_analysis_service

# NEW  
from services.video_analysis_service import get_clean_video_analysis_service
# No pose analysis service needed
```

#### Analysis Workflow
```python
# OLD - Complex multi-step process
service = get_video_analysis_service()
pose_result = await pose_service.analyze_video_pose(video_path)
analysis_result = await service.analyze_with_pose_data(video_path, pose_result)
coaching_script = await service.generate_coaching_script(analysis_result)

# NEW - Single step (matches CLI)
service = get_clean_video_analysis_service()
complete_result = await service.analyze_video_from_storage(video_id, user_id)
# Includes coaching script in main analysis
```

## Database Changes

### Schema Updates Required

#### VideoAnalysis Table
```sql
-- Remove pose analysis columns (if they exist)
ALTER TABLE video_analyses DROP COLUMN IF EXISTS pose_data;
ALTER TABLE video_analyses DROP COLUMN IF EXISTS body_position_data;
ALTER TABLE video_analyses DROP COLUMN IF EXISTS swing_metrics;

-- Keep essential columns
-- ai_analysis JSONB column now contains complete analysis including coaching_script
-- No schema changes required - existing columns are compatible
```

#### Data Migration
```sql
-- No data migration needed
-- Existing ai_analysis JSON structure is compatible
-- New analyses will include coaching_script in main JSON
```

## Configuration Changes

### Environment Variables
```bash
# UNCHANGED - Same variables needed
GEMINI_API_KEY=your_key
DATABASE_URL=postgresql://...
GOOGLE_CLOUD_STORAGE_BUCKET=your_bucket

# REMOVED - No longer needed
# MEDIAPIPE_MODEL_PATH=... (pose analysis removed)
```

### Dependencies
```bash
# Install missing dependencies if needed
pdm install opencv-python    # For video property extraction
pdm install google-genai     # For Gemini API (v2)

# Remove unnecessary dependencies
pdm remove mediapipe         # If pose analysis only
```

## Testing Migration

### 1. Verify New Architecture
```bash
# Test service imports
cd backend
python -c "from services.video_analysis_service import get_clean_video_analysis_service; print('✅ Service OK')"

# Test API imports  
python -c "from api.video_analysis import router; print('✅ API OK')"
```

### 2. Test Upload Flow
```bash
# Upload a test video
curl -X POST http://localhost:8000/api/v1/videos/upload \
  -F "file=@test_video.mp4" \
  -F "user_id=1"

# Should return: {"analysis_status": "queued", ...}
```

### 3. Test Polling Flow
```bash
# Poll for results (video_id from upload response)
curl http://localhost:8000/api/v1/video-analysis/video/123

# Should eventually return complete analysis JSON
```

### 4. Validate JSON Structure
```bash
# Compare with CLI output
cd backend
pdm run python analyze_video.py test_video.mp4

# API response should match CLI structure
```

## Performance Implications

### Improvements
- ✅ **Faster Processing**: Removed pose analysis overhead (~30-60s reduction)
- ✅ **Simpler Pipeline**: Fewer failure points, better reliability
- ✅ **Consistent Timing**: Same performance as proven CLI tool
- ✅ **Auto-Background**: No waiting for manual triggers

### Considerations
- 🔄 **Background Tasks**: Uses FastAPI background tasks (single-process)
- 🔄 **No Parallel Processing**: Sequential analysis (same as CLI)
- 🔄 **Memory Usage**: Temp video files during processing

## Rollback Plan

### If Issues Arise
1. **Restore Legacy Files**:
   ```bash
   mv video_analysis_service_legacy.py.bak video_analysis_service.py
   mv video_analysis_legacy.py.bak video_analysis.py
   ```

2. **Update main.py imports** back to legacy

3. **Test legacy endpoints** still work

### Quick Rollback Test
```bash
# Keep backup files until confident in new system
ls -la backend/services/*.bak
ls -la backend/api/*.bak
```

## Support

### Common Migration Issues

**Import Errors:**
```bash
# Missing dependencies
pip install opencv-python google-genai

# Path issues  
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

**Database Connection:**
```python
# Async session issues
from database.config import AsyncSessionLocal
async with AsyncSessionLocal() as session:
    # Use async operations
```

**JSON Format Differences:**
- New system returns identical JSON structure
- Added `_metadata` section (iOS can ignore)
- Coaching script included in main response

### Getting Help

1. Check `VIDEO_ANALYSIS_CLEAN_ARCHITECTURE.md` for complete architecture
2. Compare API responses with `analyze_video.py` CLI output
3. Test with minimal video file first
4. Check background task logs for processing status

## Verification Checklist

- [ ] New service imports without errors
- [ ] Upload endpoint accepts video and returns `analysis_status: "queued"`
- [ ] Polling endpoint returns processing status, then completed results
- [ ] Analysis JSON structure matches CLI output
- [ ] Coaching script included in response
- [ ] Background analysis completes successfully
- [ ] iOS client can parse new responses
- [ ] No manual analysis triggering needed