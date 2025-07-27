# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPORTANT: Always Check Specifications First

When lacking context about what to do next or how to implement features, ALWAYS check the specification documents in this order:

1. **`Spec/OVERVIEW.md`** - Core project vision, tech stack, and development strategy
2. **Domain-specific specifications** based on your work area:
   - **Backend work**: Check `Spec/Backend/` for API design, AI analysis, auth, database, storage
   - **Frontend work**: Check `Spec/Frontend/` for user journey, video recording/playback, TTS, navigation
   - **Business logic**: Check `Spec/Business/` for subscription model and monetization
   - **Testing**: Check `Spec/Testing/` for testing strategy and scenarios

These specifications contain the authoritative requirements and implementation details organized by functional domain.

## Project Overview

FutureGolf is an AI-powered golf swing analyzer mobile application that records golf swings, analyzes them using AI, and provides personalized coaching feedback with advanced text-to-speech capabilities.

See Spec/OVERVIEW.md for more details

## Development Approach

This project follows E2D TDD (End-to-End Test-Driven Development) methodology. All features should be developed with tests written first. See OVERVIEW.md for more details


## Key Development Commands

### Quick Start (Recommended)
```bash
./start.sh                          # Start both backend and frontend
make start                           # Alternative using Make
npm start                            # Alternative using npm
```

### Individual Services
```bash
# Backend only
cd backend && source venv/bin/activate && python start_server.py

# Frontend only  
cd frontend && npx expo start --ios

# Using Make commands
make backend                         # Start backend only
make frontend                        # Start frontend only
make setup                           # Setup development environment
make clean                           # Stop all services
```

### Legacy Commands
```bash
python setup_neon_database.py       # Initialize/test database
python test_gcs_connection.py       # Test Google Cloud Storage
```

### Database Information
- **Connection**: Configured in `backend/.env` with Neon endpoint
- **Models**: Located in `backend/models/` (fixed reserved word conflicts)
- **Initialization**: Use `setup_neon_database.py` to create tables

### Storage Information
- **Bucket**: `fg-video` on Google Cloud Storage
- **Credentials**: `backend/gcs-credential.json` (protected in .gitignore)
- **Service**: `backend/services/storage_service.py` for operations



## API Design Notes

The backend implements these key endpoints:
- Video upload endpoint (`/api/v1/videos/upload`)
- Analysis polling endpoint for progress updates (`/api/v1/video-analysis/video/{id}`)
- Results retrieval endpoint (`/api/v1/video-analysis/user/analyses`)
- User authentication endpoints (`/api/v1/auth/*`)
- TTS streaming endpoints (`/api/v1/tts/stream`, `/api/v1/tts/generate`)
- Health check endpoints (`/health`, `/api/v1/tts/health`)

## Important Considerations

- Videos should be processed server-side for consistency
- Use polling for real-time progress updates during analysis
- Store analysis results as JSONB in PostgreSQL for flexibility
- Implement proper error handling for AI service failures
- Consider implementing request queuing for video analysis

## Current Status

**Phase 1: COMPLETED** ✅

All Phase 1 infrastructure has been successfully implemented and is operational:

### Infrastructure Complete
- **Backend**: Python FastAPI with full authentication system
- **Frontend**: React Native/Expo application initialized
- **Database**: PostgreSQL on Neon with all tables created
- **Storage**: Google Cloud Storage bucket `fg-video` configured
- **MCP Servers**: Both Neon and iOS simulator MCPs working

### Database Connection
- **URL**: Configured in `backend/.env` with proper endpoint parameter
- **Tables**: 6 tables created (users, videos, video_analyses, subscriptions, payments, usage_records)
- **Status**: Fully operational with PostgreSQL 17.5 on Neon

### Important Fixed Issues
- **SQLAlchemy Models**: Fixed reserved word conflicts (`metadata` → `technical_metadata`, `usage_metadata`)
- **MCP Configuration**: Proper format in `.mcp.json` with `type: "stdio"` and `env: {}` structure
- **Neon Connection**: Added endpoint parameter for SNI support, removed `channel_binding`

**Phase 2 & 3: Video Analysis Pipeline IMPLEMENTED** ✅

Core video analysis functionality has been implemented and tested:

### Video Analysis Complete
- **Gemini Integration**: Real Google Gemini AI video analysis working
- **Frame-based Timing**: Precise swing phase detection using frame numbers
- **Single Swing Detection**: Fixed multi-swing hallucination bug with improved prompts
- **Video Compositor**: Text overlays with wrapping, phase indicators, quality scores
- **Coaching Script**: Sports commentary generation (TTS-ready)
- **Complete Pipeline**: End-to-end analysis from video upload to composited output

### Key Fixes Implemented
- **Multi-swing Bug**: Updated prompt to clarify single vs multi-swing detection
- **Frame Validation**: Added validation to prevent impossible frame numbers beyond video length
- **Text Wrapping**: Implemented proper text wrapping for video overlays to prevent overflow
- **Quality Display**: Added quality score display under swing phase indicator during follow-through
- **Font Rendering**: Improved antialiasing and font quality for video text overlays

### Known Issues (Deferred)
- **Coaching Script Hallucination**: Script contains detailed commentary beyond the 2-3 analysis points
- **Prompt Saving**: Prompts not currently saved to results folder for inspection

**Phase 4: OpenAI TTS & Popup Widget COMPLETED** ✅

Advanced TTS system with synchronized popup widget has been implemented:

### TTS Integration Complete
- **OpenAI TTS API**: High-quality voice synthesis with 6 voice options
- **Streaming Architecture**: Real-time audio generation and playback
- **Global TTS Manager**: Singleton service managing all TTS operations
- **Audio Analysis**: Real-time RMS extraction with smoothing algorithms

### TTS Popup Widget Complete
- **Animated Pulse Circle**: Scales 0.8-1.5x based on real-time RMS values
- **Blur Background**: Translucent overlay working over any content
- **Audio-Visual Sync**: 60fps updates with smooth animation
- **Cross-fade Transitions**: Smooth transitions between speech and action modes
- **App-wide Integration**: Automatically appears when TTS is active

### Testing Infrastructure
- **Mock Audio System**: Realistic audio patterns for development testing
- **Unit Tests**: Comprehensive test suite for widget behavior
- **Screenshot Testing**: Visual testing utilities and specifications
- **E2E Integration**: Complete testing from API to UI

### Key Features Implemented
✅ **OpenAI TTS Streaming**: Real-time audio generation and streaming  
✅ **Synchronized Animation**: Pulse circle matches speech rhythm  
✅ **Audio Analysis**: RMS extraction with smoothing for smooth animation  
✅ **Global Management**: App-wide TTS service with proper cleanup  
✅ **Error Handling**: Graceful fallbacks and user feedback  
✅ **Performance Optimized**: Native animations with 60fps updates  

### Quick Testing
- **Test Screen**: Go to Test tab → "Test TTS Widget"
- **Coaching Screen**: Analysis → Any analysis → Coaching tab → Play button
- **Voice Options**: 6 OpenAI voices (alloy, echo, fable, onyx, nova, shimmer)

### Ready for Production
All core functionality is operational including advanced TTS with synchronized visual feedback. The application provides a complete end-to-end experience from video recording to AI analysis to professional coaching feedback with synchronized animations.

## Google Gemini API v2 Migration (2025-01-17)

The codebase has been successfully migrated from the legacy `google-generativeai` library to the new `google-genai` v2 API:

### Migration Changes
- **Library Update**: Changed from `google-generativeai==0.8.3` to `google-genai`
- **Import Changes**: Updated from `import google.generativeai as genai` to `from google import genai`
- **Client Architecture**: Moved from direct model instantiation to centralized `genai.Client(api_key=...)`
- **API Method Updates**: All file operations and content generation now use client-based methods

### Updated Files
- `backend/requirements.txt` - Updated dependency
- `backend/services/video_analysis_service.py` - Full v2 API migration
- `backend/analyze_video.py` - Updated analysis script

### New Methods
- **File Upload**: `client.aio.files.upload(path=video_path)`
- **Content Generation**: `client.aio.models.generate_content(model=..., contents=..., config=..., safety_settings=...)`
- **File Management**: `client.aio.files.get(name=...)` and `client.aio.files.delete(name=...)`

### Testing Tools
- `backend/test_gemini_migration.py` - Verification script for migration
- `backend/analyze_video.py` - Enhanced with model selection and full prompt display

### Usage
```bash
# Test migration
python backend/test_gemini_migration.py

# Analyze videos with different models
npm run analyze-video video.mp4                    # gemini-2.5-flash (default)
npm run analyze-video-pro video.mp4                # gemini-2.5-pro
python backend/analyze_video.py video.mp4 --model gemini-2.5-pro --show-full-prompt
```

The migration maintains all existing functionality while providing access to the latest Gemini API features and improved performance.

## Environment Configuration

### Device Testing via WiFi
The application is configured for physical device testing via WiFi:

- **Frontend**: Environment-based API configuration using `.env` files
- **Backend**: Network host binding and CORS configuration for device access
- **Current Setup**: Configured for IP 192.168.1.228 with appropriate CORS origins

### Environment Files
- **Backend**: `backend/.env` contains OpenAI API key, database URL, network configuration
- **Frontend**: `frontend/.env` contains API base URL for device testing
- **Startup**: `./start.sh` script shows network information and QR code for device connection

### Testing Process
1. Run `./start.sh` to start both services
2. Install Expo Go on device
3. Scan QR code to connect to development server
4. Test TTS functionality with real audio output on device

## File Cleanup

### Recent Changes
- **Removed**: `test_analysis_complete.py` (redundant validation-only test)
- **Kept**: `test_complete_analysis.py` (comprehensive end-to-end testing with real video processing)

### Testing Architecture
- **Unit Tests**: Widget and component testing with mocks
- **Integration Tests**: Complete pipeline testing with real Gemini API
- **E2E Tests**: Full video analysis pipeline from upload to output