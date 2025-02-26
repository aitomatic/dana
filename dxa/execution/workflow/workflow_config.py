"""Configuration utilities for workflows."""

from pathlib import Path
from typing import Dict, Optional

from ..execution_config import ExecutionConfig

class WorkflowConfig(ExecutionConfig):
    """Utilities for loading and managing workflow configurations."""
    
    @classmethod
    def get_base_path(cls) -> Path:
        """Get base path for configuration files."""
        return Path(__file__).parent

    @classmethod
    def format_node_description(cls, description: str, prompt_ref: str, 
                                custom_prompts: Optional[Dict[str, str]] = None) -> str:
        """Format node description with prompt."""
        # If description is empty, use the prompt as the description
        if not description:
            return cls.get_prompt(prompt_ref, custom_prompts)
        
        # Otherwise, return the description as is
        return description 