"""Reasoning configuration management."""

import logging
from typing import Dict, Union, Optional
from pathlib import Path
import yaml
from io import StringIO

logger = logging.getLogger("dxa.execution.reasoning")

class ReasoningConfig:
    """Manages reasoning configuration loading and access."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize reasoning configuration.
        
        Args:
            config_path: Optional path to config file. If None, uses default.
        """
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[Union[str, Path]] = None) -> Dict:
        """Load reasoning configuration from YAML file.
        
        Args:
            config_path: Optional path to config file. If None, uses default.
            
        Returns:
            Dictionary containing the configuration
        """
        if config_path is None:
            config_path = Path(__file__).parent / "yaml" / "default.yaml"
            
        try:
            if isinstance(config_path, (str, Path)):
                with open(config_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            else:
                data = yaml.safe_load(StringIO(str(config_path)))
        except Exception as e:
            logger.warning(f"Failed to load reasoning config: {e}. Using default configuration.")
            data = {
                "name": "default",
                "description": "Default reasoning pattern",
                "nodes": [
                    {"id": "ANALYZE", "description": "Analyze the task"},
                    {"id": "REASON", "description": "Reason about the solution"},
                    {"id": "CONCLUDE", "description": "Conclude with an answer"}
                ],
                "prompts": {
                    "ANALYZE": "Analyze the following task:\n\n{objective}",
                    "REASON": "Reason about the solution:\n\n{objective}",
                    "CONCLUDE": "Conclude with an answer:\n\n{objective}"
                }
            }
            
        return data
    
    def get_prompt(self, prompt_ref: str) -> Optional[str]:
        """Get a prompt template by reference.
        
        Args:
            prompt_ref: Reference to the prompt in the configuration
            
        Returns:
            Prompt template if found, None otherwise
        """
        return self.config.get("prompts", {}).get(prompt_ref)
    
    def get_nodes(self) -> list:
        """Get the list of nodes from the configuration.
        
        Returns:
            List of node configurations
        """
        return self.config.get("nodes", [])
    
    def get_name(self) -> str:
        """Get the configuration name.
        
        Returns:
            Configuration name
        """
        return self.config.get("name", "default")
    
    def get_description(self) -> str:
        """Get the configuration description.
        
        Returns:
            Configuration description
        """
        return self.config.get("description", "Default reasoning pattern") 