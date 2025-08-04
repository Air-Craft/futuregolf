from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import os
import httpx
from config.api import API_VERSION_PREFIX


from database.utils import get_db_session
from core.providers.vision_gemini import GeminiVisionProvider


router = APIRouter(prefix=API_VERSION_PREFIX, tags=["system"])


async def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")



@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "FutureGolf API"}

@router.get("/full-health", tags=["Health"])
async def full_health(session: AsyncSession = Depends(get_db_session), openai_api_key: str = Depends(get_openai_api_key)):
    """
    Provides a full health check of the system, including database connectivity
    and third-party service availability.
    """
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1")
    
    # Database health check
    db_health = {"status": "disconnected"}
    try:
        result = await session.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_health["status"] = "connected"
            if debug_mode:
                tables = await session.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'"))
                table_details = []
                for table in tables:
                    count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table[0]}"))
                    table_details.append({"table": table[0], "records": count_result.scalar()})
                db_health["details"] = table_details
    except Exception as e:
        db_health["error"] = str(e)

    # Gemini health check
    gemini_health = {"status": "unhealthy"}
    try:
        gemini_provider = GeminiVisionProvider()
        if await gemini_provider.is_healthy():
            gemini_health["status"] = "healthy"
    except Exception as e:
        gemini_health["error"] = str(e)

    # OpenAI TTS health check
    openai_health = {"status": "unhealthy"}
    try:
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        
        headers = {"Authorization": f"Bearer {openai_api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.openai.com/v1/models", headers=headers)
            response.raise_for_status()
            openai_health["status"] = "healthy"
    except Exception as e:
        openai_health["error"] = str(e)

    return {
        "database": db_health,
        "gemini": gemini_health,
        "openai_tts": openai_health,
    }

