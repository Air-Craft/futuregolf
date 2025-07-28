# FutureGolf 🏌️

AI-powered golf swing analyzer with real-time coaching feedback.

## Quick Start

### 🚀 One-Command Startup

```bash
# Option 1: Shell script (recommended)
./start.sh

# Option 2: Make command
make start

# Option 3: npm script
npm start
```

### 🛠️ First Time Setup

```bash
# Setup development environment
make setup

# Or manually:
cd backend && python -m ..venv ..venv && source ..venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install
```

## Individual Services

### Backend Only
```bash
# Option 1: Make
make backend

# Option 2: Direct
cd backend && source ..venv/bin/activate && python start_server.py
```

### Frontend Only
```bash
# Option 1: Make
make frontend

# Option 2: Direct
cd frontend && npx expo start --ios
```

## Configuration

### Environment Variables

#### Google Cloud Credentials
Need your `gcs-credential.json` in `backend/`

#### Backend Configuration
Edit `backend/.env`:
```bash
# Required for TTS functionality
OPENAI_API_KEY=your_openai_api_key_here

# Network Configuration (for device testing)
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://192.168.1.228:8081,exp://192.168.1.228:8081

# Database (already configured)
DATABASE_URL=postgresql://...
Running on Neon. Ask Quinn for this or setup your own (its free).


# Google Gemini AI (already configured)
GEMINI_API_KEY=...
```

#### Frontend Configuration
Edit `frontend/.env`:
```bash
# Development API Configuration
DEV_API_HOST=192.168.1.228
DEV_API_PORT=8000
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.228:8000/api/v1

# Environment
NODE_ENV=development
```

### Service URLs
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:8081
- **API Docs**: http://localhost:8000/docs

## Device Testing 📱

### WiFi Setup (Physical Device)
1. **Find your local IP**:
   ```bash
   # On macOS/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Or use the startup script which shows network info
   ./start.sh
   ```

2. **Update environment files with your IP**:
   - `backend/.env`: Add your IP to `CORS_ORIGINS`
   - `frontend/.env`: Set `EXPO_PUBLIC_API_BASE_URL=http://YOUR_IP:8000/api/v1`

3. **Start services**:
   ```bash
   ./start.sh
   ```

4. **Connect device**:
   - Install **Expo Go** app on your phone
   - Scan the QR code that appears in terminal
   - App will connect to your local backend server

### Testing TTS on Device
- Navigate to **Test** tab → **Test TTS Widget**
- Or go to **Analysis** → Select analysis → **Coaching** → Play button
- TTS audio will play through device speakers with animated popup

## Features

### 🎯 Core Features
- **Video Recording**: Capture golf swings from multiple angles
- **AI Analysis**: Google Gemini AI analyzes swing mechanics
- **TTS Coaching**: OpenAI TTS with synchronized popup widget
- **Swing Metrics**: Detailed analysis with body angles and recommendations

### 🎮 TTS Popup Widget
- **OpenAI TTS Integration**: High-quality voice synthesis with 6 voice options
- **Animated Pulse**: Scales 0.8-1.5x synchronized with speech rhythm  
- **Blur Background**: Translucent overlay works over any content
- **Real-time RMS**: Audio-visual synchronization at 60fps
- **Cross-fade**: Smooth transitions between speech and action modes
- **Global Management**: App-wide TTS service with automatic cleanup

## Testing

### TTS Widget
1. **Test Screen**: Go to "Test" tab → "Test TTS Widget"
2. **Coaching Screen**: Analysis → Any analysis → Coaching tab → Play button

### API Endpoints
- `GET /health` - Service health check
- `POST /api/v1/tts/stream` - Stream TTS audio (OpenAI)
- `POST /api/v1/tts/generate` - Generate complete TTS audio
- `GET /api/v1/tts/voices` - Available voices (6 OpenAI voices)
- `GET /api/v1/tts/health` - TTS service health check
- `POST /api/v1/video-analysis/analyze/{id}` - Start video analysis
- `GET /api/v1/video-analysis/user/analyses` - Get user analyses

## Development

### Architecture
- **Backend**: FastAPI + PostgreSQL + OpenAI TTS + Google Gemini
- **Frontend**: React Native + Expo + Custom TTS Widget + Audio Analysis
- **Database**: Neon PostgreSQL with JSONB analysis storage
- **AI**: Google Gemini (video analysis) + OpenAI (TTS) + MediaPipe (pose detection)
- **Storage**: Google Cloud Storage for video files

### Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy, OpenAI API, Google Gemini
- **Frontend**: React Native, Expo, Expo AV, Custom Audio Analysis
- **Database**: PostgreSQL (Neon) with JSONB fields
- **AI/ML**: Google Gemini AI, OpenAI TTS, MediaPipe Pose Detection
- **Audio**: Real-time RMS analysis, synchronized animations

## Troubleshooting

### Common Issues
1. **TTS Not Working**: Check `OPENAI_API_KEY` in `.env`
2. **Backend Won't Start**: Check if port 8000 is available
3. **Frontend Won't Start**: Try `npx expo start --clear`

### Cleanup
```bash
# Stop all services
make clean

# Or manually
pkill -f "python start_server.py"
pkill -f "expo start"
```

## Commands Reference

```bash
# Development
make start       # Start both services
make backend     # Start backend only
make frontend    # Start frontend only
make setup       # Setup environment
make clean       # Stop all services
make help        # Show help

# Scripts
./start.sh       # All-in-one startup
npm start        # Alternative startup
```

## Status

- ✅ **Phase 1**: Infrastructure & Backend Setup
- ✅ **Phase 2**: Core UI Components  
- ✅ **Phase 3**: Video Analysis Pipeline
- ✅ **Phase 4**: OpenAI TTS & Synchronized Popup Widget
- 🎯 **Current**: Production-ready with advanced TTS integration

### Implementation Complete
- ✅ **OpenAI TTS Streaming**: Real-time high-quality voice synthesis
- ✅ **Synchronized Animation**: Audio-visual feedback with 60fps updates
- ✅ **Complete UI**: Professional mobile app with all core features
- ✅ **Video Analysis**: End-to-end pipeline from recording to coaching
- ✅ **Testing Infrastructure**: Unit tests, mock systems, E2E testing

---

**Ready to analyze your golf swing? Run `./start.sh` and start improving your game!** 🏌️‍♂️
