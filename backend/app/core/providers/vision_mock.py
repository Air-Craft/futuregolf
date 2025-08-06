"""Mock vision model for testing"""
import asyncio
import logging
from typing import List, Dict, Any
from PIL import Image

from app.core.interfaces import VisionModel

logger = logging.getLogger(__name__)

# Pre-defined responses for testing
MOCK_RESPONSES = [
    {"swing_detected": False, "confidence": 0.2},  # Frames 0-6 (warming up)
    {"swing_detected": True, "confidence": 0.85},  # Frames 7-13 (first swing)
    {"swing_detected": False, "confidence": 0.3},  # Frames 14-40 (between swings)
    {"swing_detected": True, "confidence": 0.90},  # Frames 41-47 (second swing)
    {"swing_detected": False, "confidence": 0.25}, # Frames 48-80 (between swings)
    {"swing_detected": True, "confidence": 0.88},  # Frames 81-87 (third swing)
    {"swing_detected": False, "confidence": 0.15}, # Frames 88+ (cooling down)
]

class MockVisionModel(VisionModel):
    """Mock implementation of vision model for testing"""
    
    def __init__(self):
        self.call_count = 0
        self.response_delay = 0.1  # Simulate API delay
        
    async def analyze_images(self, images: List[Image.Image], prompt: str) -> Dict[str, Any]:
        """
        Mock analyze images - returns predetermined responses
        
        Args:
            images: List of PIL images
            prompt: Analysis prompt (ignored in mock)
            
        Returns:
            Mock analysis results
        """
        # Simulate processing delay
        await asyncio.sleep(self.response_delay)
        
        # Determine which response to return based on call count
        response_index = min(self.call_count, len(MOCK_RESPONSES) - 1)
        response = MOCK_RESPONSES[response_index].copy()
        
        self.call_count += 1
        
        logger.info(f"Mock vision model call #{self.call_count}: {response}")
        return response
    
    def get_model_info(self) -> Dict[str, str]:
        """Get model information"""
        return {
            "provider": "mock",
            "model": "mock-vision-1.0",
            "temperature": "0.0",
            "max_tokens": "0"
        }