"""Configuration utilities for execution components."""

from pathlib import Path
from typing import Dict, Any, Optional, Type, ClassVar, Union
from opendxa.common.config_manager import load_yaml_config
from opendxa.common.utils import get_config_path
from opendxa.common.mixins.configurable import Configurable
from opendxa.common.exceptions import ConfigurationError


class ExecutionConfig(Configurable):
    """Centralized configuration management for all execution components."""
    
    # Class-level default configuration
    default_config: ClassVar[Dict[str, Any]] = {
        "base_path": None,
        "config_dir": "yaml",
        "default_config_file": "default",
        "file_extension": "yaml"
    }
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None, **overrides):
        """Initialize execution config.
        
        Args:
            config_path: Optional path to config file
            **overrides: Configuration overrides
        """
        super().__init__(config_path=config_path, **overrides)
        
    @classmethod
    def get_yaml_path(cls, for_class: Optional[Type[Any]] = None, path: Optional[str] = None) -> Path:
        """Get path to a configuration file."""

        if not for_class:
            for_class = cls

        # If path contains a dot, it's a reference to a nested config
        # Convert dots to slashes and ensure we don't append .yaml twice
        if path and "." in path and not path.endswith(".yaml") and not path.endswith(".yml"):
            path_parts = path.split(".")
            path = "/".join(path_parts)
            
            # Check if the file exists with .yaml extension
            from_class_path = get_config_path(
                for_class=for_class,
                path=f"{path}.yaml",
                config_dir="yaml",
                default_config_file="default",
                file_extension="yaml"
            )
            
            if from_class_path.exists():
                return from_class_path
                
            # Check if the file exists with .yml extension
            from_class_path = get_config_path(
                for_class=for_class,
                path=f"{path}.yml",
                config_dir="yaml",
                default_config_file="default",
                file_extension="yaml"
            )
            
            if from_class_path.exists():
                return from_class_path

        # Default behavior
        return get_config_path(for_class=for_class,
                               path=path,
                               config_dir="yaml",
                               default_config_file="default",
                               file_extension="yaml")
    
    @classmethod
    def load_config(cls, for_class=None, path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Args:
            path: Full path to config file, OR relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            
        Returns:
            Loaded configuration dictionary
        """
        if not for_class:
            for_class = cls

        config_path = cls.get_yaml_path(for_class=for_class, path=path)
        return load_yaml_config(config_path)
    
    @classmethod
    def get_prompt(cls,
                   for_class=None,
                   config_path=None,
                   prompt_ref=None, 
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
        """
        if not for_class:
            for_class = cls

        prompt_ref = str(prompt_ref)

        # If config_path is a full path to a YAML file, extract the directory and filename
        if config_path and (str(config_path).endswith('.yaml') or str(config_path).endswith('.yml')):
            # Use the file directly if it exists
            config_file = Path(config_path)
            if config_file.exists():
                # Load the config directly
                config = load_yaml_config(config_file)
                
                # Extract the prompt name from prompt_ref
                prompt_name = prompt_ref.rsplit(".", maxsplit=1)[-1]
                
                # Look for the prompt in the config
                if config and "prompts" in config:
                    prompts = config.get("prompts", {})
                    prompt_text = prompts.get(prompt_name, "")
                    
                    if prompt_text:
                        return prompt_text
        
        # Normal processing for relative paths
        if config_path:
            # Make sure the prompt_name has only the last component (without the config_path)
            prompt_name = prompt_ref.rsplit(".", maxsplit=1)[-1]
        else:
            if "." not in prompt_ref:
                print(f"Warning: Prompt reference must be in format 'config_name.prompt_name', got '{prompt_ref}'")
                return ""
        
            # Split the prompt reference into config path and prompt name
            config_path, prompt_name = prompt_ref.rsplit(".", maxsplit=1)
        
        # Load the config
        config = cls.load_config(path=config_path)

        # Look for the prompt in the config
        if config and "prompts" in config:
            prompts = config.get("prompts", {})
            prompt_text = prompts.get(prompt_name, "")
            
            if prompt_text:
                return prompt_text
        
        # If not found in config, try custom prompts
        if custom_prompts and prompt_ref in custom_prompts:
            return custom_prompts.get(prompt_ref, "")
        
        # If all else fails, return empty string
        return ""
    
    @classmethod
    def get_graph_config(cls, path: str) -> Dict[str, Any]:
        """Get graph configuration.
        
        Args:
            path: Path to config file relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            
        Returns:
            Graph configuration dictionary
        """
        config = cls.load_config(path)
        
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
    
    @classmethod
    def get_display_prompt(cls, prompt_ref: str, objective: Optional[str] = None, 
                           custom_prompts: Optional[Dict[str, str]] = None) -> str:
        """Get prompt formatted for display with placeholders explained."""
        if "." not in prompt_ref:
            return ""
        
        # Split the prompt reference into parts
        parts = prompt_ref.split(".")
        prompt_name = parts[-1]  # Last part is always the prompt name
        config_path = ".".join(parts[:-1])  # All but the last part is the config path
        
        # Load the config directly using the full path
        config = cls.load_config(config_path)
        
        # If we found a valid config with prompts
        if config and "prompts" in config:
            prompts = config.get("prompts", {})
            raw_prompt_text = prompts.get(prompt_name, "")
            
            if raw_prompt_text:
                # For display purposes only, show the objective
                display_text = raw_prompt_text
                if objective:
                    display_text = f"Objective: {objective}\n\n{display_text}"
                return display_text
        
        return ""
    
    @classmethod
    def format_node_description(cls, description: str, prompt_ref: str, 
                                custom_prompts: Optional[Dict[str, str]] = None) -> str:
        """Format node description with prompt.
        
        Args:
            description: Original node description
            prompt_ref: Reference to prompt
            custom_prompts: Optional custom prompts to override defaults
            
        Returns:
            Formatted description
        """
        # If description is empty, use the prompt as the description
        if not description:
            return cls.get_prompt(prompt_ref=prompt_ref, custom_prompts=custom_prompts)
        
        # Otherwise, return the description as is
        return description

    def _validate_config(self) -> None:
        """Validate configuration.
        
        This method extends the base Configurable validation with execution-specific checks.
        """
        # Call base class validation first
        super()._validate_config()
        
        # Validate execution-specific fields
        if not self.config.get("config_dir"):
            raise ValueError("config_dir must be set")
            
        if not self.config.get("default_config_file"):
            raise ValueError("default_config_file must be set")
            
        if not self.config.get("file_extension"):
            raise ValueError("file_extension must be set")
            
        if self.config["file_extension"] not in ["yaml", "yml"]:
            raise ValueError("file_extension must be 'yaml' or 'yml'")
        
        # Validate field types
        available_resources = self.config.get("available_resources", [])
        if not isinstance(available_resources, list):
            self.error("Invalid type for field 'available_resources': expected list")
            raise ConfigurationError("'available_resources' must be a list")
            
        reasoning = self.config.get("reasoning", {})
        if not isinstance(reasoning, dict):
            self.error("Invalid type for field 'reasoning': expected dict")
            raise ConfigurationError("'reasoning' must be a dictionary")
