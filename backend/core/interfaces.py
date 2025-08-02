"""
Core interfaces for dependency injection
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from PIL import Image


class VisionModel(ABC):
    """Abstract base class for vision models"""
    
    @abstractmethod
    async def analyze_images(self, images: List[Image.Image], prompt: str) -> Dict[str, Any]:
        """
        Analyze a sequence of images with a given prompt
        
        Args:
            images: List of PIL images to analyze
            prompt: Text prompt for analysis
            
        Returns:
            Dictionary with analysis results
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Get information about the model"""
        pass


class PromptLoader(ABC):
    """Abstract base class for loading prompts"""
    
    @abstractmethod
    def load_prompt(self, prompt_name: str) -> str:
        """Load a prompt by name"""
        pass
    
    @abstractmethod
    def list_prompts(self) -> List[str]:
        """List available prompts"""
        pass


class ConfigProvider(ABC):
    """Abstract base class for configuration"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        pass