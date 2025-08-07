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

from app.core.interfaces import VisionModel

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


class GeminiVisionProvider(VisionModel):
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
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
            )
        )

    async def analyze_video(self, video_path: str, prompt: str) -> Dict[str, Any]:
        """
        Analyze a video file using Gemini.
        """
        try:
            logger.info(f"Uploading video to Gemini: {video_path}")
            video_file = genai.upload_file(path=video_path)
            
            # Wait for the file to be processed
            import time
            while video_file.state.name == "PROCESSING":
                logger.info("Waiting for video to be processed...")
                time.sleep(1)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name != "ACTIVE":
                raise ValueError(f"File failed to process. State: {video_file.state.name}")

            logger.info(f"Calling Gemini API with model: {self.model_name}")
            response = self.model.generate_content([prompt, video_file])
            
            # Try to parse as JSON, if it fails return the raw text
            try:
                parsed_result = json.loads(response.text.strip())
                return parsed_result
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse Gemini response as JSON: {e}")
                logger.debug(f"Raw response: {response.text[:500]}...")
                # Return a structured error response
                return {
                    "error": "Failed to parse response as JSON",
                    "raw_response": response.text,
                    "_metadata": {
                        "error": str(e),
                        "video_duration": 0,
                        "analysis_duration": 0
                    }
                }

        except Exception as e:
            logger.error(f"Error in Gemini video analysis: {e}", exc_info=True)
            return {
                "error": str(e),
                "_metadata": {
                    "error": str(e),
                    "video_duration": 0,
                    "analysis_duration": 0
                }
            }
        finally:
            if 'video_file' in locals():
                genai.delete_file(video_file.name)

    async def is_healthy(self) -> bool:
        """Check if the Gemini API is healthy by listing available models."""
        try:
            api_key = get_api_key()
            if not api_key:
                logger.error("Cannot check Gemini health: No API key configured")
                return False
            
            models = [m for m in genai.list_models()]
            return len(models) > 0
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}", exc_info=True)
            return False
    
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