# Backend Testing Documentation

## Overview

This document covers the testing strategy and implementation for the FutureGolf backend services, with a focus on the AI Swing Detection WebSocket API.

## AI Swing Detection Testing

### Overview

The AI Swing Detection service uses WebSocket communication to process a stream of video frames and detect complete golf swings in real-time. The testing framework simulates the iOS app's behavior by streaming frames extracted from test videos.

### Test Setup

#### 1. Frame Extraction

Frame extraction is now handled automatically by the test framework using the `VideoFrameExtractor` utility class located in `tests/utils/video_frame_extractor.py`. This utility:
- Extracts frames from test videos at configurable intervals (default: 0.35 seconds matching iOS frame rate)
- Resizes and compresses frames to match iOS app behavior (configurable via `tests/config/test_frame_extraction.yaml`)
- Saves frames to the configured output directory
- Creates metadata files with timestamp information

The frame extraction happens automatically when running tests, but can also be done manually if needed using the VideoFrameExtractor class directly.

#### 2. Environment Setup

Create a `.env` file in the backend directory with:

```bash
# Google Gemini API key for LLM
GOOGLE_API_KEY=your_gemini_api_key

# Optional: Override default settings
LLM_SUBMISSION_THRESHOLD=1.25  # Seconds before submitting to LLM
CONTEXT_EXPIRY_SECONDS=5.0     # Rolling window for frame retention
MAX_IMAGE_BUFFER=100           # Maximum frames in buffer
IOS_FRAME_INTERVAL=0.35        # Frame extraction interval
```

#### 3. Install Dependencies

```bash
cd backend
pdm install
```

This installs all required dependencies including:
- LangChain for conversation memory management
- Google Gemini integration for LLM analysis
- WebSocket libraries for real-time communication

### Running Tests

#### Quick Command Reference

```bash
# Basic test run (auto cleanup)
cd backend
pdm run pytest tests/test_swing_detection_ws.py::test_swing_detection_three_swings -xvs

# Preserve extracted frames (no cleanup)
pdm run pytest tests/test_swing_detection_ws.py::test_swing_detection_three_swings -xvs --no-cleanup

# Test against live server
pdm run pytest tests/test_swing_detection_ws.py::test_swing_detection_three_swings -xvs --base-url http://localhost:8001

# Combined: live server + preserve frames
pdm run pytest tests/test_swing_detection_ws.py::test_swing_detection_three_swings -xvs \
  --base-url http://localhost:8001 \
  --no-cleanup

# Manual testing with verbose output
pdm run python test_swing_detection_live.py --base http://localhost:8001 --verbose
```

#### Test Execution Modes

The swing detection tests support two execution modes:

1. **Fixture Mode (Default)**: Automatically starts a test server
2. **Live Server Mode**: Connects to an already-running server

#### Fixture Mode (Self-Contained Testing)

```bash
cd backend
pdm run pytest tests/test_swing_detection_ws.py::test_swing_detection_three_swings -xvs
```

This mode:
- Automatically starts a test server on a free port
- Runs tests against the fixture server
- Shows server logs in the test output
- Cleans up the server after tests complete

#### Live Server Mode (Test Against Running Server)

First, start your server in one terminal:

```bash
cd backend
make backend  # or pdm run python start_server.py
```

Then run tests against it in another terminal:

```bash
cd backend
pdm run pytest tests/test_swing_detection_ws.py::test_swing_detection_three_swings -xvs --base-url http://localhost:8001
```

This mode:
- Connects to your existing server
- Server logs appear in the server terminal (not test output)
- Useful for debugging server-side issues
- Allows testing against different server configurations

#### Frame Extraction Options

By default, tests extract frames from the video before each run and clean up afterward. You can control this behavior:

```bash
# Preserve extracted frames after test (don't cleanup)
pdm run pytest tests/test_swing_detection_ws.py::test_swing_detection_three_swings -xvs --no-cleanup

# Run again - will reuse existing frames (faster)
pdm run pytest tests/test_swing_detection_ws.py::test_swing_detection_three_swings -xvs --no-cleanup
```

Benefits of `--no-cleanup`:
- Faster repeated test runs (no re-extraction)
- Can inspect extracted frames in `tests/fixtures/extracted_frames/test_video/`
- Useful for debugging what frames are being sent

#### Combined Options

You can combine live server mode with frame preservation:

```bash
# Test against live server and preserve frames
pdm run pytest tests/test_swing_detection_ws.py::test_swing_detection_three_swings -xvs \
  --base-url http://localhost:8001 \
  --no-cleanup
```

#### Manual Testing Tools

For interactive testing and debugging:

```bash
# Run standalone test against live server
cd backend
pdm run python test_swing_detection_live.py --base http://localhost:8001

# With verbose output
pdm run python test_swing_detection_live.py --base http://localhost:8001 --verbose
```

This provides detailed output including:
- Frame-by-frame sending progress
- Response status breakdown
- Detected swings with confidence scores
- Any errors encountered

### Test Cases

#### 1. Three Swing Detection Test (`test_swing_detection_three_swings`)

**Purpose**: Verify that the system correctly detects 3 complete golf swings in the test video.

**Behavior**:
- Streams all 73 frames from the test video
- Simulates iOS app behavior with continuous streaming
- Resets image queue after each swing detection
- Validates that exactly 3 swings are detected

**Expected Output**:
```
✅ SWING DETECTED at 9.68s!
   Queue size: 30 frames
   Context window: 4.67s
   Context size: 750 KB

✅ SWING DETECTED at 16.36s!
   Queue size: 20 frames
   Context window: 4.67s
   Context size: 750 KB

✅ SWING DETECTED at 21.03s!
   Queue size: 14 frames
   Context window: 4.34s
   Context size: 700 KB

✅ SWING DETECTED at 24.04s!
   Queue size: 9 frames
   Context window: 2.67s
   Context size: 450 KB
```

Note: The AI model may detect 3-4 swings depending on how it interprets partial swings at the beginning/end of the video.

#### 2. Memory Trimming Test (`test_swing_detection_memory_trimming`)

**Purpose**: Verify that frames older than 5 seconds are removed from context.

**Behavior**:
- Sends frames spanning more than 5 seconds
- Checks that context window never exceeds the 5-second threshold
- Validates rolling window implementation

#### 3. Continuous Streaming Test (`test_swing_detection_continuous_streaming`)

**Purpose**: Verify WebSocket handles continuous frame streaming without errors.

**Behavior**:
- Streams 20 frames continuously
- Validates all responses have correct status
- Ensures no connection drops or errors

### WebSocket Protocol

#### Client → Server Message Format

```json
{
  "timestamp": 1.12,              // Video-relative timestamp in seconds
  "image_base64": "..."          // Base64-encoded JPEG image
}
```

#### Server → Client Response Format

**Swing Detected:**
```json
{
  "status": "evaluated",
  "swing_detected": true,
  "timestamp": 2.45,
  "context_window": 1.34,        // Time span of frames in context
  "context_size": 650            // Approximate size in KB
}
```

**Awaiting More Data:**
```json
{
  "status": "awaiting_more_data",
  "context_window": 0.67,
  "context_size": 350
}
```

### Implementation Details

#### LangChain Integration

The service uses LangChain's `ConversationBufferMemory` to maintain context across frames:

```python
self.memory = ConversationBufferMemory(return_messages=True)
self.conversation = ConversationChain(
    llm=self.llm,
    memory=self.memory
)
```

This allows the LLM to understand the temporal sequence of frames and detect complete swing patterns.

#### Swing Detection Logic

1. **Frame Accumulation**: Images are buffered until time span ≥ 1.25 seconds
2. **LLM Analysis**: Google Gemini Flash analyzes the image sequence
3. **Pattern Recognition**: LLM identifies complete swing phases:
   - Setup/Address
   - Takeaway and backswing
   - Transition at top
   - Downswing through impact
   - Follow-through to finish
4. **Context Reset**: Memory cleared after swing detection for next swing

#### Performance Optimizations

- **Image Compression**: Frames resized to 640x480 max, JPEG quality 75
- **Selective Detail**: Most recent frame uses "high" detail, others use "low"
- **Memory Management**: Rolling window prevents unbounded memory growth
- **Async Processing**: Non-blocking WebSocket and LLM calls

### Troubleshooting

#### Common Issues

1. **"Connection refused" error**
   - Ensure backend server is running
   - Check WebSocket URL matches server configuration

2. **No swings detected**
   - Verify Google API key is set correctly
   - Check frame extraction completed successfully
   - Review LLM responses in debug logs

3. **Memory/performance issues**
   - Adjust `MAX_IMAGE_BUFFER` if needed
   - Reduce image quality settings
   - Check system resources

#### Debug Mode

Enable detailed logging:

```python
# In test file
logging.basicConfig(level=logging.DEBUG)
```

This shows:
- Frame-by-frame processing
- LLM prompts and responses
- Memory management operations
- WebSocket communication details

### Future Enhancements

1. **Performance Metrics**
   - Add timing measurements for LLM calls
   - Track memory usage over time
   - Monitor WebSocket latency

2. **Additional Test Cases**
   - Test with different video types (practice swings, partial swings)
   - Simulate network interruptions
   - Test concurrent connections

3. **CI/CD Integration**
   - Automate frame extraction in CI pipeline
   - Add performance regression tests
   - Include load testing scenarios