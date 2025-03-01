"""Configuration utilities for execution components."""

import inspect
import os
from pathlib import Path
from typing import Dict, Any, Optional
from ..common.utils import load_yaml_config


class ExecutionConfig:
    """Centralized configuration management for all execution components."""
    
    @classmethod
    def get_base_path(cls, for_class=None) -> Path:
        """Get base path for the given the_class."""
        if not for_class:
            for_class = cls

        # Get the file where the class is defined
        file_path = inspect.getfile(for_class)
    
        # Convert to absolute path if it's not already
        abs_path = os.path.abspath(file_path)
    
        return Path(abs_path).parent
    
    @classmethod
    def get_config_path(cls, for_class=None, path: Optional[str] = None) -> Path:
        """Get path to configuration file.
        
        Args:
            the_class: The class that is requesting the config path
            path: Full path to config file, OR relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            
        Returns:
            Full path to the configuration file
        """
        # If path is already a full path, return it
        if not path:
            path = "default"

        if Path(path).exists():
            return Path(path)

        # Normalize path separators (convert dots to slashes)
        path = path.replace(".", "/")

        if not for_class:
            for_class = cls
        
        # Build the full path
        return cls.get_base_path(for_class=for_class) / "config" / f"{path}.yaml"
    
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

        config_path = cls.get_config_path(for_class=for_class, path=path)
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
        # print(f"Warning: Prompt '{prompt_name}' not found in config '{config_path}'")
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
                if "{objective}" in display_text and objective:
                    display_text = display_text.replace("{objective}", f"{{objective}} (Will be: \"{objective}\")")
                
                # For planning prompt, show what previous_output will be
                if "{previous_output}" in display_text:
                    display_text = display_text.replace("{previous_output}",
                                                        "{previous_output} (Will be output from previous step)")
                    
                # For backward compatibility
                if "{problem_analysis}" in display_text:
                    display_text = display_text.replace("{problem_analysis}",
                                                        "{problem_analysis} (Will be output from ANALYZE step)")
                    
                if "{reasoning_result}" in display_text:
                    display_text = display_text.replace("{reasoning_result}",
                                                        "{reasoning_result} (Will be output from execution steps)")
                        
                return display_text
        
        # If we get here, we didn't find a matching prompt in the config
        # Try custom prompts as a last resort
        if custom_prompts and prompt_ref in custom_prompts:
            raw_prompt_text = custom_prompts.get(prompt_ref, "")
            
            if raw_prompt_text:
                # For display purposes only, show the objective
                display_text = raw_prompt_text
                if "{objective}" in display_text and objective:
                    display_text = display_text.replace("{objective}", f"{{objective}} (Will be: \"{objective}\")")
                
                # For planning prompt, show what previous_output will be
                if "{previous_output}" in display_text:
                    display_text = display_text.replace("{previous_output}",
                                                        "{previous_output} (Will be output from previous step)")
                    
                # For backward compatibility
                if "{problem_analysis}" in display_text:
                    display_text = display_text.replace("{problem_analysis}",
                                                        "{problem_analysis} (Will be output from ANALYZE step)")
                    
                if "{reasoning_result}" in display_text:
                    display_text = display_text.replace("{reasoning_result}",
                                                        "{reasoning_result} (Will be output from execution steps)")
                        
                return display_text
        
        # If all else fails, return empty string
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
