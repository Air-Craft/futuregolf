"""
Google Gemini vision model provider (direct API)
"""
import asyncio
import json
from typing import List, Dict, Any
from PIL import Image
import logging
import google.generativeai as genai
import os

from core.interfaces import VisionModel

logger = logging.getLogger(__name__)

# Global API key variable
_api_key = None

def get_api_key():
    """Get API key, loading from environment if needed"""
    global _api_key
    if _api_key is None:
        _api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if _api_key:
            logger.info(f"Loaded API key ({len(_api_key)} chars)")
            genai.configure(api_key=_api_key)
        else:
            logger.warning("No API key found for Gemini. Set GEMINI_API_KEY or GOOGLE_API_KEY")
    return _api_key


class GeminiVisionModel(VisionModel):
    """Direct Gemini API implementation of vision model"""
    
    def __init__(self, model_name: str = "gemini-1.5-flash", temperature: float = 0.1, max_tokens: int = 300):
        """
        Initialize Gemini vision model
        
        Args:
            model_name: Name of the model
            temperature: Model temperature for generation
            max_tokens: Maximum tokens in response
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
    
    async def analyze_images(self, images: List[Image.Image], prompt: str) -> Dict[str, Any]:
        """
        Analyze images using Gemini
        
        Args:
            images: List of PIL images
            prompt: Analysis prompt
            
        Returns:
            Analysis results as dictionary
        """
        try:
            # Check if API key is configured
            api_key = get_api_key()
            if not api_key:
                logger.error("Cannot analyze images: No API key configured")
                return {
                    "swing_detected": False,
                    "confidence": 0.0,
                    "error": "No API key configured"
                }
            
            logger.info(f"Analyzing {len(images)} images with Gemini {self.model_name}")
            
            # Prepare parts for Gemini
            parts = [prompt]
            parts.extend(images)
            
            # Run generation
            logger.debug("Calling Gemini generate_content...")
            response = await asyncio.to_thread(
                self.model.generate_content,
                parts
            )
            
            # Parse response
            response_text = response.text.strip()
            logger.debug(f"Gemini response: {response_text}")
            
            # Try to extract JSON from response
            if "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
                parsed_result = json.loads(json_str)
            else:
                # Fallback if no JSON found
                parsed_result = {
                    "swing_detected": False,
                    "confidence": 0.0,
                    "raw_response": response_text
                }
            
            logger.info(f"Gemini analysis result: {parsed_result}")
            return parsed_result
            
        except asyncio.TimeoutError:
            logger.error("Gemini API call timed out")
            return {
                "swing_detected": False,
                "confidence": 0.0,
                "error": "API timeout"
            }
        except Exception as e:
            logger.error(f"Error in Gemini vision analysis: {e}", exc_info=True)
            return {
                "swing_detected": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, str]:
        """Get model information"""
        return {
            "provider": "gemini",
            "model": self.model_name,
            "temperature": str(self.temperature),
            "max_tokens": str(self.max_tokens)
        }