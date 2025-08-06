from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

# Load environment variables FIRST before any other imports
load_dotenv()

# Configure logging right after loading environment variables
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)
logger.info(f"Log level set to {log_level}")

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
from app.api.auth_register import router as auth_register_router
from app.api.auth_login import router as auth_login_router
from app.api.auth_oauth import router as auth_oauth_router
from app.api.auth_password import router as auth_password_router
from app.api.user_profile import router as user_profile_router
from app.api.session_management import router as session_management_router
from app.api.video_upload import router as video_upload_router
from app.api.video_analysis import router as video_analysis_router
from app.api.analysis import router as analysis_router  # New UUID-based analysis router
from app.api.tts import router as tts_router
from app.api.swing_detection_ws import router as swing_detection_ws_router
from app.api.health_check import router as health_check_router
from app.config.api import API_TITLE, API_DESCRIPTION, API_VERSION

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
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
app.include_router(analysis_router)  # New UUID-based analysis endpoints
app.include_router(tts_router)
app.include_router(swing_detection_ws_router)
app.include_router(health_check_router)

@app.get("/")
async def root():
    """
    Root endpoint - Hello World
    """
    return {"message": "Hello World from FutureGolf API!"}



if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
