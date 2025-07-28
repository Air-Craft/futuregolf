"""
TTS (Text-to-Speech) API endpoints using OpenAI's TTS service
Provides streaming audio generation for real-time playback
"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Iterator
import openai
import os
import io
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/api/v1/tts",
    tags=["TTS"],
    responses={404: {"description": "Not found"}},
)

# Initialize OpenAI client
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        client = None
    else:
        client = openai.OpenAI(api_key=api_key)
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    client = None

# Request model
class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    model: Optional[str] = "tts-1"  # tts-1 or tts-1-hd
    speed: Optional[float] = 1.0    # 0.25 to 4.0
    response_format: Optional[str] = "mp3"  # mp3, opus, aac, flac

# Supported voices
AVAILABLE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

@router.post("/stream")
async def stream_tts(request: TTSRequest):
    """
    Stream TTS audio from OpenAI
    
    This endpoint generates speech from text and streams it back
    as audio data that can be played in real-time.
    """
    try:
        # Check if OpenAI client is available
        if client is None:
            raise HTTPException(
                status_code=503,
                detail="TTS service unavailable. OpenAI API key not configured."
            )
        
        # Validate voice
        if request.voice not in AVAILABLE_VOICES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid voice. Available voices: {', '.join(AVAILABLE_VOICES)}"
            )
        
        # Validate speed
        if not 0.25 <= request.speed <= 4.0:
            raise HTTPException(
                status_code=400,
                detail="Speed must be between 0.25 and 4.0"
            )
        
        # Validate text length
        if len(request.text) > 4096:
            raise HTTPException(
                status_code=400,
                detail="Text must be 4096 characters or less"
            )
        
        logger.info(f"Generating TTS for {len(request.text)} characters with voice '{request.voice}'")
        
        # Generate speech using OpenAI
        response = client.audio.speech.create(
            model=request.model,
            voice=request.voice,
            input=request.text,
            speed=request.speed,
            response_format=request.response_format
        )
        
        # Stream the audio data
        def generate_audio():
            # OpenAI returns an iterator of bytes
            for chunk in response.iter_bytes(chunk_size=1024):
                yield chunk
        
        # Set appropriate content type based on format
        content_types = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac"
        }
        
        return StreamingResponse(
            generate_audio(),
            media_type=content_types.get(request.response_format, "audio/mpeg"),
            headers={
                "Cache-Control": "no-cache",
                "X-Content-Type-Options": "nosniff",
                "X-TTS-Voice": request.voice,
                "X-TTS-Model": request.model,
            }
        )
        
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in TTS generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during TTS generation"
        )

@router.get("/voices")
async def get_available_voices():
    """
    Get list of available TTS voices
    """
    return {
        "voices": [
            {"id": "alloy", "name": "Alloy", "description": "Neutral and balanced"},
            {"id": "echo", "name": "Echo", "description": "Warm and conversational"},
            {"id": "fable", "name": "Fable", "description": "Expressive and dynamic"},
            {"id": "onyx", "name": "Onyx", "description": "Deep and authoritative"},
            {"id": "nova", "name": "Nova", "description": "Friendly and upbeat"},
            {"id": "shimmer", "name": "Shimmer", "description": "Soft and pleasant"}
        ],
        "default": "alloy"
    }

@router.post("/generate")
async def generate_tts(request: TTSRequest):
    """
    Generate TTS audio and return as a complete file
    
    This endpoint is useful for generating shorter audio clips
    that don't need streaming.
    """
    try:
        # Check if OpenAI client is available
        if client is None:
            raise HTTPException(
                status_code=503,
                detail="TTS service unavailable. OpenAI API key not configured."
            )
        
        # Validate inputs (same as stream endpoint)
        if request.voice not in AVAILABLE_VOICES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid voice. Available voices: {', '.join(AVAILABLE_VOICES)}"
            )
        
        if not 0.25 <= request.speed <= 4.0:
            raise HTTPException(
                status_code=400,
                detail="Speed must be between 0.25 and 4.0"
            )
        
        if len(request.text) > 4096:
            raise HTTPException(
                status_code=400,
                detail="Text must be 4096 characters or less"
            )
        
        logger.info(f"Generating complete TTS for {len(request.text)} characters")
        
        # Generate speech
        response = client.audio.speech.create(
            model=request.model,
            voice=request.voice,
            input=request.text,
            speed=request.speed,
            response_format=request.response_format
        )
        
        # Get all audio data
        audio_data = response.content
        
        # Set appropriate content type
        content_types = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac"
        }
        
        return Response(
            content=audio_data,
            media_type=content_types.get(request.response_format, "audio/mpeg"),
            headers={
                "Content-Length": str(len(audio_data)),
                "X-TTS-Voice": request.voice,
                "X-TTS-Model": request.model,
            }
        )
        
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in TTS generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during TTS generation"
        )

@router.post("/coaching")
async def generate_coaching_tts(request: TTSRequest):
    """
    Generate TTS audio optimized for golf coaching feedback
    
    Uses optimized voice settings for clear, professional coaching delivery.
    """
    try:
        # Check if OpenAI client is available
        if client is None:
            raise HTTPException(
                status_code=503,
                detail="TTS service unavailable. OpenAI API key not configured."
            )
        
        # Override with coaching-optimized settings
        coaching_voice = "onyx"  # Deep, authoritative male voice
        coaching_model = "tts-1-hd"  # Higher quality
        coaching_speed = 1.2  # Balanced speed for energy and clarity
        
        logger.info(f"Generating coaching TTS for {len(request.text)} characters")
        
        # Generate speech with coaching settings
        response = client.audio.speech.create(
            model=coaching_model,
            voice=coaching_voice,
            input=request.text,
            speed=coaching_speed,
            response_format="mp3"
        )
        
        # Get all audio data
        audio_data = response.content
        
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Length": str(len(audio_data)),
                "X-TTS-Voice": coaching_voice,
                "X-TTS-Model": coaching_model,
                "X-TTS-Type": "coaching",
            }
        )
        
    except openai.APIError as e:
        logger.error(f"OpenAI API error in coaching TTS: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Coaching TTS generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in coaching TTS: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during coaching TTS generation"
        )

@router.get("/health")
async def tts_health_check():
    """
    Check if TTS service is available
    """
    try:
        # Check if API key is configured
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "status": "error",
                "message": "OpenAI API key not configured"
            }
        
        # Could add a test generation here if needed
        return {
            "status": "healthy",
            "service": "OpenAI TTS",
            "available_voices": AVAILABLE_VOICES
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }