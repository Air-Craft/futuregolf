"""
LangChain-based vision model provider
"""
import asyncio
import json
from typing import List, Dict, Any
from PIL import Image
import logging
import os

# Set API key before importing langchain
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.interfaces import VisionModel

logger = logging.getLogger(__name__)


class LangChainVisionModel(VisionModel):
    """LangChain implementation of vision model using Google Gemini"""
    
    def __init__(self, model_name: str, temperature: float = 0.1, max_tokens: int = 300):
        """
        Initialize LangChain vision model
        
        Args:
            model_name: Name of the model (e.g., "gemini-1.5-flash")
            temperature: Model temperature for generation
            max_tokens: Maximum tokens in response
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LangChain model
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_tokens
        )
    
    async def analyze_images(self, images: List[Image.Image], prompt: str) -> Dict[str, Any]:
        """
        Analyze images using LangChain
        
        Args:
            images: List of PIL images
            prompt: Analysis prompt
            
        Returns:
            Analysis results as dictionary
        """
        try:
            # Create message with images
            message_content = [{"type": "text", "text": prompt}]
            
            # Add images to the message
            for image in images:
                message_content.append({
                    "type": "image",
                    "image": image
                })
            
            # Create human message with all content
            human_msg = HumanMessage(content=message_content)
            
            # Run generation (LangChain handles async internally)
            result = await self.llm.ainvoke([human_msg])
            
            # Parse response
            response_text = result.content.strip()
            
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
            
            logger.info(f"LangChain analysis result: {parsed_result}")
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error in LangChain vision analysis: {e}")
            return {
                "swing_detected": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, str]:
        """Get model information"""
        return {
            "provider": "langchain",
            "model": self.model_name,
            "temperature": str(self.temperature),
            "max_tokens": str(self.max_tokens)
        }