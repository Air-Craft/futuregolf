"""
File-based prompt loader implementation
"""
from pathlib import Path
from typing import List
import logging

from core.interfaces import PromptLoader

logger = logging.getLogger(__name__)


class FilePromptLoader(PromptLoader):
    """Load prompts from text files"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize prompt loader
        
        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = Path(prompts_dir)
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory {prompts_dir} does not exist")
            self.prompts_dir.mkdir(parents=True, exist_ok=True)
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt by name
        
        Args:
            prompt_name: Name of the prompt (without extension)
            
        Returns:
            Prompt text
            
        Raises:
            FileNotFoundError: If prompt file not found
        """
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
        
        logger.debug(f"Loaded prompt '{prompt_name}' from {prompt_file}")
        return prompt
    
    def list_prompts(self) -> List[str]:
        """List available prompts"""
        prompt_files = self.prompts_dir.glob("*.txt")
        return [f.stem for f in prompt_files]