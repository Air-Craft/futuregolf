# DEVOPS


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



## Important Considerations

- Videos should be processed server-side for consistency
- Use polling for real-time progress updates during analysis
- Store analysis results as JSONB in PostgreSQL for flexibility
- Implement proper error handling for AI service failures
- Consider implementing request queuing for video analysis


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

