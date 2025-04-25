"""Configuration utilities for execution components."""

from pathlib import Path
from typing import Dict, Any, Optional, ClassVar, Union, List, TypedDict
import logging
from opendxa.common.utils.misc import Misc
from opendxa.common.mixins.configurable import Configurable

# Configure logger
logger = logging.getLogger(__name__)

class GraphConfig(TypedDict):
    """Type definition for graph configuration."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class ExecutionConfig(Configurable):
    """Centralized configuration management for all execution components."""
    
    # Class-level default configuration
    default_config: ClassVar[Dict[str, Any]] = {
        "available_resources": [],
        "reasoning": {},
        "prompts": {}
    }
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None, **overrides):
        """Initialize execution config.
        
        Args:
            config_path: Optional path to config file
            **overrides: Configuration overrides
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__(config_path=config_path, **overrides)
        
    @classmethod
    def load_config(cls, path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Args:
            path: Full path to config file, OR relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            
        Returns:
            Loaded configuration dictionary
            
        Raises:
            ConfigurationError: If configuration cannot be loaded
            ValueError: If configuration is invalid
        """
        try:
            config_path = cls.get_yaml_path(path=path)
            config = Misc.load_yaml_config(config_path)
            
            # Validate basic structure
            if not isinstance(config, dict):
                raise ValueError(f"Configuration must be a dictionary, got {type(config)}")
                
            return config
            
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {path}: {str(e)}") from e
    
    @classmethod
    def get_prompt(cls,
                   config_path: Optional[str] = None,
                   prompt_ref: Optional[str] = None, 
                   custom_prompts: Optional[Dict[str, str]] = None) -> str:
        """Get prompt by reference.
        
        Args:
            config_path: Path to config file relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            prompt_ref: Reference to prompt in format "path/to/config.prompt_name"
                       (e.g., "default.DEFINE" or "basic/prosea.ANALYZE")
            custom_prompts: Optional custom prompts to override defaults
            
        Returns:
            Raw prompt text
            
        Raises:
            ValueError: If prompt reference is invalid
        """
        if not prompt_ref:
            return ""
            
        prompt_ref = str(prompt_ref)
        
        # Try custom prompts first
        if custom_prompts and prompt_ref in custom_prompts:
            return custom_prompts[prompt_ref]
            
        # Extract prompt name and config path
        if "." not in prompt_ref:
            logger.warning("Prompt reference must be in format 'config_name.prompt_name', got '%s'", prompt_ref)
            return ""
            
        config_path, prompt_name = prompt_ref.rsplit(".", maxsplit=1)
        
        try:
            # Load the config
            config = cls.load_config(path=config_path)
            
            # Look for the prompt in the config
            if config and "prompts" in config:
                prompts = config.get("prompts", {})
                return prompts.get(prompt_name, "")
                
        except Exception as e:
            logger.warning("Failed to load prompt '%s': %s", prompt_ref, str(e))
            
        return ""
    
    @classmethod
    def get_graph_config(cls, path: str) -> GraphConfig:
        """Get graph configuration.
        
        Args:
            path: Path to config file relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            
        Returns:
            Graph configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        config = cls.load_config(path)
        
        # Validate graph structure
        if not isinstance(config.get("nodes", []), list):
            raise ValueError("Graph configuration must have a 'nodes' list")
            
        if not isinstance(config.get("edges", []), list):
            raise ValueError("Graph configuration must have an 'edges' list")
        
        # Extract graph-specific configuration
        nodes = config.get("nodes", [])
        edges = config.get("edges", [])
        metadata = {k: v for k, v in config.items() 
                    if k not in ["nodes", "edges", "prompts"]}
                   
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": metadata
        }
    
    def _validate_config(self) -> None:
        """Validate configuration.
        
        This method extends the base Configurable validation with execution-specific checks.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Call base class validation first
        super()._validate_config()
        
        # Validate field types
        self._validate_type("available_resources", list)
        self._validate_type("reasoning", dict)
        self._validate_type("prompts", dict)
        
        # Validate required fields
        self._validate_required("available_resources")
        self._validate_required("reasoning")
        self._validate_required("prompts")
        
        # Validate reasoning structure
        reasoning = self.config.get("reasoning", {})
        if not isinstance(reasoning, dict):
            raise ValueError("Reasoning configuration must be a dictionary")
            
        # Validate prompts structure
        prompts = self.config.get("prompts", {})
        if not isinstance(prompts, dict):
            raise ValueError("Prompts configuration must be a dictionary")
            
        # Validate available resources
        resources = self.config.get("available_resources", [])
        if not isinstance(resources, list):
            raise ValueError("Available resources must be a list")
            
        # Validate each resource is a string
        for resource in resources:
            if not isinstance(resource, str):
                raise ValueError(f"Resource must be a string, got {type(resource)}")
