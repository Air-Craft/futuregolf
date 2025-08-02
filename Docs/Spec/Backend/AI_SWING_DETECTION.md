# AI Swing Detection

## ✅ Objective

Build a **FastAPI WebSocket server** that:
- Accepts a **video frame stream** (screenshots) from a client along with **video-relative timestamps**
- Maintains image sequence per connection/session in **LangChain memory**
- Determines if a **complete golf swing** has occurred via LLM analysis
- Responds with detection results
- Clears or trims memory based on global thresholds

---

## 📊 Tech Stack

- **FastAPI** + `WebSocket` support
- **LangChain** for LLM interaction
- **Google Gemini Flash 3.5** (or default low-power model specified in config)
- `ConversationBufferMemory` or custom memory class
- Async + non-blocking architecture

---

## 📡 WebSocket API

**Endpoint**: `/ws/detect-golf-swing`

### Incoming client messages:

```json
{
  "timestamp": 1.12,                // Float, video-relative seconds
  "image_base64": "<...>"          // Base64-encoded JPEG or PNG
}
```

### Outgoing server messages:

```json
{
  "status": "evaluated",
  "swing_detected": true,
  "timestamp": 2.45,
  "context_window": [time since first image to latest image]
  "context_size": [size in kb or tokens of conversation memory buffer]
}
```

Or:

```json
{
  "status": "awaiting_more_data"
  "context_window": [time since first image to latest image]
  "context_size": [size in kb or tokens of conversation memory buffer]
}
```

---

## ⟳ Backend Flow

### 1. Session Setup
- On WebSocket connect:
  - Accept connection
  - Initialize `ConversationChain` with `ConversationBufferMemory`
  - Start an empty image buffer `List[Dict[timestamp: float, image: bytes]]`

### 2. Receive Image Frames
- On each message:
  - Parse JSON payload
  - Decode base64 image
  - Append to `image_buffer`
  - Maintain sort order by timestamp

### 3. Check Submission Threshold
- Track:
  - `image_buffer`
  - `first_timestamp = image_buffer[0]['timestamp']`
  - `last_timestamp = current_image_timestamp`

If `last_timestamp - first_timestamp >= LLM_SUBMISSION_THRESHOLD` (default: **1.25s**, set in config):

- Format image buffer into prompt-friendly form
- Prompt LLM:
  > “The following image sequence shows a golfer. Does it represent a full golf swing from address to follow-through?”

- If **yes**:
  - Send `{"swing_detected": true}`
  - Clear memory and image buffer
- If **no**:
  - Retain context
  - Continue image collection

### 4. Apply Rolling Window
- Discard any image where:
  `current_timestamp - image['timestamp'] > CONTEXT_EXPIRY_SECONDS`
- Default: **5.0s** (set in config)

### 5. On Disconnect
- Cleanup:
  - WebSocket
  - LangChain instance
  - Image buffer

---

## ⚙️ Configurable Settings

From global config:

```python
LLM_SUBMISSION_THRESHOLD = 1.25   # seconds
CONTEXT_EXPIRY_SECONDS = 5.0      # seconds
MAX_IMAGE_BUFFER = 100            # optional safeguard
```

---

## 🧠 LangChain Integration

Use a `ConversationChain`:

```python
ConversationChain(
  llm=...,  # Gemini Flash 3.5
  memory=ConversationBufferMemory(return_messages=True)
)
```

---

## 🧰 Testing

Test client:
- Use fixtures/video/test_video.[mov|mp4]
- Cleanup any previous test runs
- Use a library to grab screenshots of the test video every 0.35s (or whatever iOS is using) and resize, recompress them similar to iOS (maybe we should have a test_config.yaml in the backend/tests folder)
- Stream those screenshots to the endpoint. It should detect 3 swings 
- Simulates time gaps to test memory trimming
- Remove screenshots used for testing
---

## Documentation

- Document the development and tests in the respective files in `Docs/Dev` looking for existing relevant files first and creating any needed.

---

## 🔄 Summary

Fast, non-blocking WebSocket-based image stream processing with LangChain-backed LLM inference, tailored for golf swing detection. State is retained only in RAM per connection. Older frames trimmed after 5 seconds. A new inference happens every 1.25s of received video time.
