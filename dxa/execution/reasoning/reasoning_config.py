"""Configuration utilities for reasoning."""

from typing import Dict, Optional
from pathlib import Path

from ..execution_config import ExecutionConfig

class ReasoningConfig(ExecutionConfig):
    """Utilities for loading and managing reasoning configurations."""
    
    @classmethod
    def get_config_path(cls, config_ref: str) -> Path:
        """Get path to reasoning configuration file."""
        return super().get_config_path(config_ref, "reasoning")
    
    @classmethod
    def load_yaml(cls, reasoning_name: str) -> Dict:
        """Load reasoning configuration from YAML file."""
        return super().load_config(reasoning_name, "reasoning")

    @classmethod
    def reload_config(cls, reasoning_name: str) -> Dict:
        """Force reload of reasoning configuration from YAML file."""
        return super().load_config(reasoning_name, "reasoning")

    @classmethod
    def get_prompt(cls, prompt_ref: str, objective: Optional[str] = None, 
                   custom_prompts: Optional[Dict[str, str]] = None) -> str:
        """Get prompt by reference."""
        variables = {'objective': objective or ''}
        return super().get_prompt(prompt_ref, variables, custom_prompts)
    
    @classmethod
    def format_node_description(cls, description: str, prompt_ref: str, 
                                objective: Optional[str] = None, 
                                custom_prompts: Optional[Dict[str, str]] = None) -> str:
        """Format node description with prompt."""
        if not prompt_ref:
            return description
            
        # Get the prompt text
        prompt_text = cls.get_prompt(prompt_ref, objective, custom_prompts)
        if not prompt_text:
            return description
            
        # Replace placeholders
        if "{prompt}" in description:
            description = description.replace("{prompt}", prompt_text)
            
        # Handle specific prompt placeholders
        _, prompt_name = prompt_ref.split(".", 1)
        placeholder = "{" + prompt_name + "_prompt}"
        if placeholder in description:
            description = description.replace(placeholder, prompt_text)
            
        return description 