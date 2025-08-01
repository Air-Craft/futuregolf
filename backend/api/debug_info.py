"""Debug endpoint to check system status"""
from fastapi import APIRouter
import os
from core.container import container
from core.interfaces import VisionModel, ConfigProvider

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/env")
async def check_environment():
    """Check environment variables"""
    keys = ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY']
    env_status = {}
    
    for key in keys:
        val = os.getenv(key)
        env_status[key] = f"{len(val)} chars" if val else "Not set"
    
    return {"environment": env_status}

@router.get("/vision-model")
async def check_vision_model():
    """Check vision model status"""
    try:
        vision_model = container.get(VisionModel)
        model_info = vision_model.get_model_info()
        
        # Try to get API key status from Gemini provider
        from core.providers.vision_gemini import get_api_key
        api_key = get_api_key()
        
        return {
            "model_info": model_info,
            "api_key_configured": bool(api_key),
            "api_key_length": len(api_key) if api_key else 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "model_info": None,
            "api_key_configured": False
        }