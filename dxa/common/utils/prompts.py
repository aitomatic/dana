"""Utility for managing and formatting prompts."""

from typing import Dict, Any, Optional, Union
import yaml
from pathlib import Path
import re

class Prompts:
    """Generic prompt management utility."""
    
    @classmethod
    def load_from_yaml(cls, yaml_data: Union[str, Dict, Path]) -> Dict[str, str]:
        """Load prompts from YAML configuration."""
        # Handle different input types
        if isinstance(yaml_data, (str, Path)):
            with open(yaml_data, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml_data
            
        return data.get('prompts', {})
    
    @classmethod
    def format_prompt(cls, template: str, **kwargs) -> str:
        """Format a prompt template with provided variables."""
        # First, handle standard Python format string replacements
        formatted = template.format(**kwargs)
        
        # Then handle any custom placeholder patterns like <variable_name>
        for key, value in kwargs.items():
            placeholder = f"<{key}>"
            if placeholder in formatted:
                formatted = formatted.replace(placeholder, str(value))
                
        return formatted
    
    @classmethod
    def get_prompt(cls, prompt_type: str, prompt_templates: Dict[str, str], **kwargs) -> str:
        """Get and format a prompt by type."""
        if prompt_type not in prompt_templates:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
            
        template = prompt_templates[prompt_type]
        return cls.format_prompt(template, **kwargs) 