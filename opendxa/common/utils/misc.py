"""Miscellaneous utilities."""

from importlib import import_module
from typing import Type, Any, Optional, Callable, Union, Dict
from pathlib import Path
from functools import lru_cache
import os
import inspect
import asyncio
import nest_asyncio
import yaml
from opendxa.common.exceptions import ConfigurationError

# Default agent configuration
DEFAULT_AGENT_CONFIG: Dict[str, Any] = {
    "api_key": None,
    "model": "gpt-4",
    "available_resources": [],
    "reasoning": {
        "strategy": "cot",
        "max_steps": 10
    },
    "logging": {
        "level": "INFO",
        "dir": "logs",
        "format": "text",
        "max_bytes": 1000000,
        "backup_count": 5,
        "console_output": True
    }
}

def load_agent_config(
    agent_type: str,
    config_path: Optional[str] = None,
    **overrides
) -> Dict[str, Any]:
    """Load and validate agent configuration.
    
    Args:
        agent_type: Type of agent to create
        config_path: Optional path to YAML config file
        **overrides: Configuration overrides
        
    Returns:
        Dict containing agent configuration
        
    Raises:
        ConfigurationError: If configuration is invalid
        FileNotFoundError: If config file does not exist
        ValueError: If config values are invalid
    """
    # Start with default config
    config = DEFAULT_AGENT_CONFIG.copy()
    
    # Update with environment variables
    config["api_key"] = os.getenv("OPENAI_API_KEY")
    
    # Load from file if provided
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
            
        if path.suffix not in ('.yaml', '.yml'):
            raise ConfigurationError("Config file must be .yaml or .yml")
            
        try:
            file_config = load_yaml_config(path)
            # Validate before updating
            _validate_agent_config(file_config)
            config.update(file_config)
        except ValueError as e:
            raise ConfigurationError(str(e)) from e
            
    # Apply and validate overrides
    try:
        _validate_agent_config(overrides)
        config.update(overrides)
    except ValueError as e:
        raise ConfigurationError("Invalid override values") from e
        
    # Update logging config from environment
    config["logging"] = {
        "level": str.split(os.getenv("LOG_LEVEL", "INFO"))[0],
        "dir": str.split(os.getenv("LOG_DIR", "logs"))[0],
        "format": str.split(os.getenv("LOG_FORMAT", "text"))[0],
        "max_bytes": int(str.split(os.getenv("LOG_MAX_BYTES", "1000000"))[0]),
        "backup_count": int(str.split(os.getenv("LOG_BACKUP_COUNT", "5"))[0]),
        "console_output": str.split(os.getenv("LOG_CONSOLE_OUTPUT", "true"))[0].lower() == "true"
    }
        
    return config

def _validate_agent_config(config: Dict[str, Any]) -> None:
    """Validate agent configuration.
    
    Args:
        config: Configuration to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Validate field types
    available_resources = config.get("available_resources", [])
    if not isinstance(available_resources, list):
        raise ValueError("'available_resources' must be a list")
        
    reasoning = config.get("reasoning", {})
    if not isinstance(reasoning, dict):
        raise ValueError("'reasoning' must be a dictionary")

@lru_cache(maxsize=128)
def load_yaml_config(path: Union[str, Path]) -> Dict[str, Any]:
    """Load YAML file with caching.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Loaded configuration dictionary
        
    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If YAML parsing fails
    """
    if not isinstance(path, Path):
        path = Path(path)
        
    if not path.exists():
        # Try different extensions if needed
        path = _resolve_yaml_path(path)
        
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def _resolve_yaml_path(path: Path) -> Path:
    """Helper to resolve path with different YAML extensions."""
    # Try .yaml extension
    yaml_path = path.with_suffix('.yaml')
    if yaml_path.exists():
        return yaml_path
        
    # Try .yml extension
    yml_path = path.with_suffix('.yml')
    if yml_path.exists():
        return yml_path
        
    raise FileNotFoundError(f"YAML file not found: {path}")

def get_class_by_name(class_path: str) -> Type[Any]:
    """Get class by its fully qualified name.
    
    Example:
        get_class_by_name("opendxa.common.graph.traversal.Cursor")
    """
    module_path, class_name = class_path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, class_name) 

def get_base_path(for_class: Type[Any]) -> Path:
    """Get base path for the given class."""
    return Path(inspect.getfile(for_class)).parent

def get_config_path(for_class: Type[Any],
                    config_dir: str = "config",
                    file_extension: str = "cfg",
                    default_config_file: str = "default",
                    path: Optional[str] = None) -> Path:
    """Get path to a configuration file.

    Arguments:
        path: Considered first. Full path to service file, OR relative
                to the services directory (e.g., "mcp_echo_service" or
                "mcp_echo_service/mcp_echo_service.py")

        for_class: Considered second. If provided, we will look
                here for the config directory (e.g., "mcp_services/") first

    Returns:
        Full path to the config file, including the file extension
    """

    if not path:
        path = default_config_file
    
    # Support dot notation for relative paths
    if "." in path:
        # Special case for workflow configs with dot notation
        if config_dir == "yaml" and "." in path and not path.endswith(('.yaml', '.yml')):
            # Convert dots to slashes
            path_parts = path.split(".")
            path = "/".join(path_parts)
            
            # Check if the file exists with the path directly
            base_path = get_base_path(for_class) / config_dir
            yaml_path = base_path / f"{path}.{file_extension}"
            if yaml_path.exists():
                return yaml_path
        else:
            # Standard dot to slash conversion
            path = path.replace(".", "/")

    # If the path already exists as is, return it
    if Path(path).exists():
        return Path(path)
    
    # If the path already has the file extension, don't append it again
    if path.endswith(f".{file_extension}"):
        return get_base_path(for_class) / config_dir / path
    
    # Build the full path with the file extension
    return get_base_path(for_class) / config_dir / f"{path}.{file_extension}"

def ensure_asyncio_safety():
    """Check and make sure asyncio is safe to use."""
    try:
        asyncio.get_running_loop()
        # We're in a running event loop (e.g., iPython notebook)
        # For notebooks, we need to ensure we have the result
        # One approach is to use a helper function to wait for the task
        nest_asyncio.apply()
    except RuntimeError:
        # We're not in an asyncio loop
        pass

def safe_asyncio_run(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run a function in an asyncio loop."""
    ensure_asyncio_safety()
    return asyncio.run(func(*args, **kwargs))

def get_field(obj: Union[dict, object], field_name: str, default: Any = None) -> Any:
    """Get a field from either a dictionary or object.
    
    Args:
        obj: The object or dictionary to get the field from
        field_name: The name of the field to get
        default: Default value to return if field is not found
        
    Returns:
        The value of the field if found, otherwise the default value
    """
    if isinstance(obj, dict):
        return obj.get(field_name, default)
    return getattr(obj, field_name, default)
