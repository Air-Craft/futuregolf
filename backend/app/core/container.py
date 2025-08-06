"""
Dependency injection container
"""
from typing import Dict, Any, Type, Optional
import logging

from app.core.interfaces import VisionModel, PromptLoader, ConfigProvider
from app.core.providers.vision_gemini import GeminiVisionProvider
from app.core.providers.prompt_loader import FilePromptLoader
from app.core.providers.config_provider import EnvironmentConfigProvider

logger = logging.getLogger(__name__)


class DIContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
    
    def register(self, interface: Type, instance: Any):
        """Register a service instance"""
        self._services[interface] = instance
        logger.debug(f"Registered {interface.__name__} with instance {type(instance).__name__}")
    
    def register_factory(self, interface: Type, factory: callable):
        """Register a factory function for lazy initialization"""
        self._factories[interface] = factory
        logger.debug(f"Registered factory for {interface.__name__}")
    
    def get(self, interface: Type) -> Any:
        """Get a service by interface"""
        # Check if already instantiated
        if interface in self._services:
            return self._services[interface]
        
        # Check if factory exists
        if interface in self._factories:
            instance = self._factories[interface]()
            self._services[interface] = instance
            return instance
        
        raise ValueError(f"No service registered for {interface.__name__}")
    
    def has(self, interface: Type) -> bool:
        """Check if a service is registered"""
        return interface in self._services or interface in self._factories


# Global container instance
container = DIContainer()


def configure_container(config_module: Optional[Any] = None):
    """
    Configure the DI container with default providers
    
    Args:
        config_module: Optional configuration module to use
    """
    # Register config provider
    config_provider = EnvironmentConfigProvider(config_module)
    container.register(ConfigProvider, config_provider)
    
    # Register prompt loader
    prompt_loader = FilePromptLoader()
    container.register(PromptLoader, prompt_loader)
    
    # Register vision model factory
    def create_vision_model():
        # Check if mock is requested
        import os
        if os.getenv("USE_MOCK_VISION") == "true":
            from app.core.providers.vision_mock import MockVisionModel
            logger.info("Using mock vision model for testing")
            return MockVisionModel()
        
        config = container.get(ConfigProvider)
        model_name = config.get("LLM_MODEL", "gemini-1.5-flash")
        
        # Remove prefix if present
        if model_name.startswith("gemini/"):
            model_name = model_name.replace("gemini/", "")
        
        return GeminiVisionProvider(
            model_name=model_name,
            temperature=0.1,
            max_tokens=300
        )
    
    container.register_factory(VisionModel, create_vision_model)
    
    logger.info("DI container configured successfully")