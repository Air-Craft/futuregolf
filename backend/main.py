from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables FIRST before any other imports
load_dotenv()

# Debug: Check environment on startup
if os.getenv('CHECK_ENV'):
    print("=== Server Environment Check ===")
    for key in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY']:
        val = os.getenv(key)
        if val:
            print(f"{key}: {len(val)} chars")
        else:
            print(f"{key}: Not set")

# Import authentication routers AFTER loading env vars
from api.auth_register import router as auth_register_router
from api.auth_login import router as auth_login_router
from api.auth_oauth import router as auth_oauth_router
from api.auth_password import router as auth_password_router
from api.user_profile import router as user_profile_router
from api.session_management import router as session_management_router
from api.video_upload import router as video_upload_router
from api.video_analysis import router as video_analysis_router
from api.tts import router as tts_router
from api.recording_voice import router as recording_voice_router
from api.recording_swing import router as recording_swing_router
from api.swing_detection_ws import router as swing_detection_ws_router
from api.debug_info import router as debug_router

app = FastAPI(
    title="FutureGolf API",
    description="A modern golf management system API with comprehensive authentication",
    version="1.0.0"
)

# Add CORS middleware with environment-based origins
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routers
app.include_router(auth_register_router)
app.include_router(auth_login_router)
app.include_router(auth_oauth_router)
app.include_router(auth_password_router)
app.include_router(user_profile_router)
app.include_router(session_management_router)
app.include_router(video_upload_router)
app.include_router(video_analysis_router)
app.include_router(tts_router)
app.include_router(recording_voice_router)
app.include_router(recording_swing_router)
app.include_router(swing_detection_ws_router)
app.include_router(debug_router)

@app.get("/")
async def root():
    """
    Root endpoint - Hello World
    """
    return {"message": "Hello World from FutureGolf API!"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "FutureGolf API"}

@app.get("/api/v1/auth/config")
async def get_auth_config():
    """
    Get authentication configuration
    """
    return {
        "success": True,
        "config": {
            "password_min_length": 8,
            "password_require_uppercase": True,
            "password_require_lowercase": True,
            "password_require_digit": True,
            "password_require_special": True,
            "access_token_expire_minutes": 30,
            "refresh_token_expire_days": 7,
            "email_verification_expire_hours": 24,
            "password_reset_expire_hours": 1,
            "oauth_providers": ["google", "microsoft", "linkedin"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)