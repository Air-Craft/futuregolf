# FutureGolf Backend API

A modern golf management system API built with FastAPI.

## Quick Start

### 1. Setup Virtual Environment

```bash
# Create virtual environment
python3 -m .venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit the `.env` file with your database credentials and other settings.

### 4. Run the Server

```bash
# Option 1: Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using the startup script
python start_server.py

# Option 3: Using python directly
python main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative API docs**: http://localhost:8000/redoc

## API Endpoints

- `GET /` - Hello World endpoint
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

## Development

The server runs with auto-reload enabled in development mode, so changes to your code will automatically restart the server.

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── start_server.py     # Server startup script
├── .venv/              # Virtual environment (ignored in git)
└── README.md          # This file
```

## Running Analysis Tests

### Complete Video Analysis Test

The backend includes a comprehensive test that processes a golf swing video through the complete analysis pipeline, generating all output types and exporting them as JSON files.

#### Prerequisites

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

#### Run Complete Analysis Test

```bash
# Run the complete analysis test with your test video
python tests/test_complete_analysis.py

# Or using pytest for more detailed output
pytest tests/test_complete_analysis.py -v -s

# Run all tests
pytest tests/ -v
```

#### Test Output

The test processes `tests/test_video.mov` and generates 5 JSON output files in `test_results/`:

1. **`pose_data_output.json`** - MediaPipe pose landmarks for server-side video compositing
2. **`swing_analysis_output.json`** - Swing phase breakdown with coaching tips for frontend display
3. **`coaching_script_output.json`** - Text-to-speech statements with timestamps for voice overlay
4. **`video_metadata_output.json`** - Composited video information and metadata
5. **`complete_analysis_summary.json`** - Combined overview of all analysis results

#### Console Output Example

```
🎬 ================================================================================
🎬 FUTUREGOLF COMPLETE ANALYSIS TEST
🎬 ================================================================================
📁 VALIDATING TEST VIDEO
📊 Video properties:
   • File size: 918.5KB
   • Resolution: 768x432
   • Duration: 10.01s
   • FPS: 29.97
   • Total frames: 300
✅ Video validation complete

🔍 STEP 1: MediaPipe Pose Detection
• Processing frame 30/300 (10%) - 1.2s elapsed
• Processing frame 60/300 (20%) - 2.4s elapsed
✅ Pose detection complete: 300 frames in 12.5s

🤖 STEP 2: Gemini Visual Analysis (8fps)
• Extracting frames at 8fps: 80 frames selected
• Setup phase: 0.0-2.0s ✅
• Backswing phase: 2.0-4.5s ✅
✅ Swing analysis complete

🎙️ STEP 3: Coaching Script Generation
• Created 8 coaching statements
• Total script duration: 42.3s
✅ Coaching script complete

🎥 STEP 4: Video Compositing
• Overlaying skeleton lines on 300 frames
• Adding tip text at timestamps
✅ Composited video metadata generated

💾 STEP 5: Exporting Results
• Pose detection data: pose_data_output.json ✅
• Swing phase analysis: swing_analysis_output.json ✅
• TTS coaching script: coaching_script_output.json ✅
• Composited video info: video_metadata_output.json ✅
• Complete analysis summary: complete_analysis_summary.json ✅

📊 ANALYSIS COMPLETE
🎯 Overall Score: 8.1/10
⏱️ Processing Time: 15.2s
📁 Files Generated: 5 JSON files
✅ All outputs saved to test_results/
```

#### Viewing Results

```bash
# View the complete summary
cat test_results/complete_analysis_summary.json

# View specific analysis types
cat test_results/swing_analysis_output.json
cat test_results/coaching_script_output.json

# List all generated files
ls -la test_results/
```

#### Understanding the Outputs

- **Pose Data**: Raw MediaPipe landmarks used by the server to composite skeleton lines onto video frames
- **Swing Analysis**: Structured phase breakdown (setup, backswing, impact, etc.) with timestamps and coaching tips for frontend display
- **Coaching Script**: Text-to-speech statements synchronized to video timestamps for voice coaching overlay
- **Video Metadata**: Information about the composited video with visual overlays and annotations

## Next Steps

1. Set up your database connection in the `.env` file
2. Create database models and migrations  
3. Add authentication and authorization
4. Implement your golf management features
5. Run analysis tests to validate the video processing pipeline
6. Deploy to production