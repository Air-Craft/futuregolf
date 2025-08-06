# 🛠️ SPEC: Refactored Video Analysis Flow (UUID-Based, Two-Step Upload)

## Overview

This spec introduces a two-step video analysis flow for improved reliability and decoupling. Clients first create an analysis entry and then upload a video against that entry. This replaces the previous flow where video and analysis were submitted together.

---

## 1. Endpoint: `POST /api/v1/analysis/create`

**Purpose:**  
Create a new analysis entry and return a UUID.

**Implementation:**  
- Generate a new analysis record in the database.  
- Set `status = "AWAITING_VIDEO"`.  
- Return the uuid to the client.

**Returns:**  
```json
{ "uuid": "<uuid>" }
```

---

## 2. Endpoint: `PUT /api/v1/analysis/{uuid}/video`

**Purpose:**  
Attach a video file to a specific analysis entry.

**Implementation:**  
- Upload the file to GCS → `processing/` folder.  
- Update the analysis record:  
  - `originalVideoURL = gcs://.../processing/{uuid}_original`  
  - `status = "PENDING_ANALYSIS"`  
- Spawn a background task:  
  - Set `status = "ANALYZING"`  
  - Download video from GCS  
  - Submit video to LLM (e.g., Gemini)  
  - On success:  
    - Move video to `processed/` folder in GCS and rename as `{uuid}_original`  
    - Update:  
      - `originalVideoURL = gcs://.../processed/{uuid}_original`  
      - `processedVideoURL =` same for now  
      - `analysisJSON = <result from LLM>`  
      - `status = "COMPLETE"`

---

## 3. Endpoint: `GET /api/v1/analysis/{uuid}`

**Purpose:**  
Poll analysis status and retrieve results.

**Returns:**  
- All fields from the analysis table as JSON.  
- Clients will poll this endpoint to check for completion.

---

## 💾 Database Changes

Ensure the `video_analyses` table includes:  
- `uuid` (UUID, indexed, unique, non-nullable)  
- `status`: Enum or string field, values:  
  - `"AWAITING_VIDEO"`  
  - `"PENDING_ANALYSIS"`  
  - `"ANALYZING"`  
  - `"COMPLETE"`  
- `originalVideoURL`: String  
- `processedVideoURL`: String  
- `analysisJSON`: jsonb  
- `errorDescription`: String  

---

## 🧠 Background Task Logic

**Trigger:** After `PUT /analysis/{uuid}/video` completes

**Steps:**  
1. Set `status = "ANALYZING"`  
2. Download video from GCS  
3. Submit to LLM  
   - Handle upload retries (due to known BrokenPipe errors)  
   - Compress if needed before upload  
4. On success:  
   - Move video to `processed/` bucket + rename to `{uuid}_original`  
   - Update DB with:  
     - `originalVideoURL = <new path>`  
     - `processedVideoURL = <same>`  
     - `analysisJSON = <LLM result>`  
     - `status = "COMPLETE"`

---

## 📦 Code Placement

- **Endpoints:**  
  - `POST /analysis/create` → `api/analysis.py`  
  - `PUT /analysis/{uuid}/video` → `api/analysis.py`  
  - `GET /analysis/{uuid}` → `api/analysis.py`  

- **Service Layer:**  
  - Add `create_analysis_entry()` in `AnalysisOrchestrator`  
  - Refactor `submit_video_for_analysis()` to handle UUID and new flow  
  - Add `start_background_analysis(uuid)` to launch `analyze_video_background()`  

- **Storage Logic:**  
  - Use `VideoUploadService` → upload to `processing/`, then move to `processed/`  
  - Ensure `StorageService.move_file(...)` exists or is implemented

---

## 👩‍🏭 Key Implementation Details

- GCS supports connection polling. Ensure (if not already) that the client is reused during the life of the server.

---

## 🧪 Testing

### General
- Tests should...  
  - Start their own server on first available port (make this a util as it is already done in another test)  
  - Capture those servers logs in `backend/logs/test_server_logs.txt`  
  - Use the live database (Neon) for now. We will improve this later.  
  - Improve the DI of any app code in order to help with tests.
  - Create the minimum number of tests to ensure the features are working

### Unit
- Create analysis → assert DB entry  
- Upload video → mock cloud storage → assert DB status update  
- Background task → mock LLM → assert final DB state

### Integration
- Same as above but with live LLM and Cloud Storage

### E2E Testing
- Start test server  
- Call endpoints to create analysis, upload video, poll for result  
- Expect status updates over time from GET endpoint  
- Use live LLM, DB and Cloud Storage

### Edge Cases
- Video too large → set `status = "FAILED"`, set `errorDescription` in db  
- Invalid UUID  
- LLM or Cloud Storage failure → set `status = "FAILED"`, set `error_description` in db

---

## ✅ Acceptance Criteria

- `POST /analysis/create` returns a UUID  
- `PUT /analysis/{uuid}/video` uploads video and starts analysis  
- Background analysis populates `analysisJSON` and updates statuses  
- `GET /analysis/{uuid}` returns full analysis record  
- System is robust to large files and LLM upload failures (via retries/compression)
