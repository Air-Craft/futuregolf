"""
Configuration provider implementation
"""
from typing import Dict, Any
import os
from dotenv import load_dotenv

from app.core.interfaces import ConfigProvider

# Load environment variables
load_dotenv()


class EnvironmentConfigProvider(ConfigProvider):
    """Configuration provider that reads from environment variables and config modules"""
    
    def __init__(self, config_module: Any = None):
        """
        Initialize config provider
        
        Args:
            config_module: Optional config module to load values from
        """
        self.config_module = config_module
        self._cache: Dict[str, Any] = {}
        
        # Load config from module if provided
        if config_module:
            for attr in dir(config_module):
                if not attr.startswith('_'):
                    value = getattr(config_module, attr)
                    if not callable(value) and not isinstance(value, type):
                        self._cache[attr] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        First checks environment variables, then cached config values
        """
        # Check environment variable first
        env_value = os.getenv(key)
        if env_value is not None:
            # Try to parse as number
            try:
                if '.' in env_value:
                    return float(env_value)
                return int(env_value)
            except ValueError:
                # Return as string
                return env_value
        
        # Check cache
        return self._cache.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        # Combine environment variables and cached values
        all_config = dict(os.environ)
        all_config.update(self._cache)
        return all_config