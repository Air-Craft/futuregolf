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

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


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
            # Prepare parts for Gemini
            parts = [prompt]
            parts.extend(images)
            
            # Run generation
            response = await asyncio.to_thread(
                self.model.generate_content,
                parts
            )
            
            # Parse response
            response_text = response.text.strip()
            
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
            
        except Exception as e:
            logger.error(f"Error in Gemini vision analysis: {e}")
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