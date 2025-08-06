from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables FIRST
load_dotenv()

# Import only TTS router for testing
from app.api.tts import router as tts_router

app = FastAPI(
    title="FutureGolf TTS Test API",
    description="Testing TTS functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only TTS router
app.include_router(tts_router)

@app.get("/")
async def root():
    return {"message": "TTS Test Server is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TTS Test API"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)