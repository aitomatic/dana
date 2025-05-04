"""Reasoning configuration management."""

from typing import Dict, Union, Optional, ClassVar, Any
from pathlib import Path
from opendxa.common.mixins.configurable import Configurable

class ReasoningConfig(Configurable):
    """Manages reasoning configuration loading and access."""
    
    # Class-level default configuration
    default_config: ClassVar[Dict[str, Any]] = {
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
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize reasoning configuration.
        
        Args:
            config_path: Optional path to config file. If None, uses default.
        """
        if config_path is None:
            config_path = Path(__file__).parent / "yaml" / "default.yaml"
        super().__init__(config_path=config_path)
    
    def _validate_config(self) -> None:
        """Validate configuration.
        
        This method extends the base Configurable validation with reasoning-specific checks.
        """
        # Call base class validation first
        super()._validate_config()
        
        # Validate required fields
        if not self.config.get("name"):
            raise ValueError("Configuration must have a 'name' field")
            
        if not self.config.get("description"):
            raise ValueError("Configuration must have a 'description' field")
            
        if not self.config.get("nodes"):
            raise ValueError("Configuration must have a 'nodes' field")
            
        if not self.config.get("prompts"):
            raise ValueError("Configuration must have a 'prompts' field")
    
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