"""Agent configuration management."""

from typing import Dict, Any, Optional, ClassVar
from dataclasses import dataclass
from pathlib import Path
import os
import json

@dataclass
class AgentConfig:
    """Agent configuration with defaults and loading logic."""
    
    # Default configuration
    DEFAULT_CONFIG: ClassVar[Dict[str, Any]] = {
        "preferred_models": [
            {
                "name": "openai:gpt-4o-mini",
                "required_api_keys": ["OPENAI_API_KEY"]
            },
            {
                "name": "anthropic:claude-3-opus-20240229",
                "required_api_keys": ["ANTHROPIC_API_KEY"]
            },
            {
                "name": "anthropic:claude-3-sonnet-20240229",
                "required_api_keys": ["ANTHROPIC_API_KEY"]
            },
            {
                "name": "openai:gpt-3.5-turbo",
                "required_api_keys": ["OPENAI_API_KEY"]
            },
            {
                "name": "azure:gpt-4",
                "required_api_keys": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
            }
        ],
        "model": None,  # Will be set to first available model
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    def __init__(self, config_path: Optional[str] = None, **overrides):
        """Initialize agent configuration.
        
        Args:
            config_path: Optional path to JSON config file
            **overrides: Configuration overrides
        """
        # Start with default config
        self.config = self.__class__.DEFAULT_CONFIG.copy()
        
        # Load from file if provided
        if config_path:
            self._load_from_file(config_path)
            
        # Apply overrides
        self.config.update(overrides)
        
        # Find and set the first available model
        self.config["model"] = self._find_first_available_model()
        
        # Update logging config from environment
        self._update_logging_from_env()
    
    def _find_first_available_model(self) -> str:
        """Find the first available model based on API keys.
        
        Returns:
            Name of the first model that has all required API keys available
            
        Raises:
            ValueError: If no models are available
        """
        for model_config in self.config["preferred_models"]:
            # Check if all required API keys are available
            if all(os.getenv(key) for key in model_config["required_api_keys"]):
                return model_config["name"]
                
        # If we get here, no models are available
        raise ValueError(
            "No models available. Please set one of the following API keys:\n" +
            "\n".join(
                f"- {', '.join(model['required_api_keys'])} for {model['name']}"
                for model in self.config["preferred_models"]
            )
        )
    
    def _load_from_file(self, config_path: str) -> None:
        """Load configuration from JSON file.
        
        Searches for the config file in the following order:
        1. Exact path provided
        2. Relative to the config directory
        3. Current working directory
        
        Args:
            config_path: Path to JSON config file
            
        Raises:
            FileNotFoundError: If config file cannot be found
            ValueError: If file is not JSON or JSON is invalid
        """
        # Convert to Path if string
        path = Path(config_path)
        
        # Check file extension
        if path.suffix != '.json':
            raise ValueError("Config file must be .json")
            
        # Try exact path first
        if path.exists():
            return self._load_json_file(path)
            
        # Try relative to config directory
        config_dir = Path(__file__).parent
        config_path = config_dir / path
        if config_path.exists():
            return self._load_json_file(config_path)
            
        # Try current working directory
        cwd_path = Path.cwd() / path
        if cwd_path.exists():
            return self._load_json_file(cwd_path)
            
        # If we get here, file wasn't found in any location
        raise FileNotFoundError(
            f"Config file not found in any location: {config_path}\n"
            f"Tried:\n"
            f"1. {path}\n"
            f"2. {config_dir / path}\n"
            f"3. {Path.cwd() / path}"
        )
    
    def _load_json_file(self, path: Path) -> None:
        """Load and update configuration from a JSON file.
        
        Args:
            path: Path to JSON file
            
        Raises:
            ValueError: If JSON is invalid
        """
        try:
            with open(path, encoding="utf-8") as f:
                file_config = json.load(f)
                self.config.update(file_config)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {path}") from e
        except Exception as e:
            raise ValueError(f"Failed to load config from {path}") from e
    
    def _update_logging_from_env(self) -> None:
        """Update logging configuration from environment variables."""
        # Helper function to safely convert string to int
        def safe_int(value: str, default: int) -> int:
            try:
                # Remove any comments and whitespace
                clean_value = value.split('#')[0].strip()
                return int(clean_value) if clean_value else default
            except (ValueError, AttributeError):
                return default

        self.config["logging"] = {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "dir": os.getenv("LOG_DIR", "logs"),
            "format": os.getenv("LOG_FORMAT", "text"),
            "max_bytes": safe_int(os.getenv("LOG_MAX_BYTES", "1000000"), 1000000),
            "backup_count": safe_int(os.getenv("LOG_BACKUP_COUNT", "5"), 5),
            "console_output": os.getenv("LOG_CONSOLE_OUTPUT", "true").lower() == "true"
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def update(self, config: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        self.config.update(config) 