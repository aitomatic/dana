"""Configuration utilities for execution components."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class ExecutionConfig:
    """Centralized configuration management for all execution components."""
    
    @classmethod
    def get_base_path(cls) -> Path:
        """Get base path for configuration files."""
        return Path(__file__).parent
    
    @classmethod
    def get_config_path(cls, path: str) -> Path:
        """Get path to configuration file.
        
        Args:
            path: Full path to config file, OR relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            
        Returns:
            Full path to the configuration file
        """
        # If path is already a full path, return it
        if Path(path).exists():
            return Path(path)

        # Normalize path separators (convert dots to slashes)
        path = path.replace(".", "/")
        
        # Build the full path
        return cls.get_base_path() / "config" / f"{path}.yaml"
    
    @classmethod
    def load_config(cls, path: str) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Args:
            path: Full path to config file, OR relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            
        Returns:
            Loaded configuration dictionary
        """
        config_path = cls.get_config_path(path)
        
        print(f"Loading config from: {config_path}")
        
        if not config_path.exists():
            print(f"Warning: No configuration found at: {config_path}")
            return {}
            
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    @classmethod
    def get_prompt(cls, config_path=None, prompt_name=None, 
                   prompt_ref=None, 
                   custom_prompts: Optional[Dict[str, str]] = None) -> str:
        """Get prompt by reference.
        
        Args:
            config_path: Path to config file relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            prompt_name: Name of the prompt to get

            OR

            prompt_ref: Reference to prompt in format "path/to/config.prompt_name"
                       (e.g., "default.DEFINE" or "basic/prosea.ANALYZE")

            custom_prompts: Optional custom prompts to override defaults
            
        Returns:
            Raw prompt text
        """
        prompt_ref = str(prompt_ref)

        if not config_path:
            if "." not in prompt_ref:
                print(f"Warning: Prompt reference must be in format 'config_name.prompt_name', got '{prompt_ref}'")
                return ""
        
            # Split the prompt reference into config path and prompt name
            config_path, prompt_name = prompt_ref.rsplit(".", 1)
        
        # Load the config
        config = cls.load_config(config_path)
        
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
        print(f"Warning: Prompt '{prompt_name}' not found in config '{config_path}'")
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
