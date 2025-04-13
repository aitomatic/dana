"""Miscellaneous utilities."""

from importlib import import_module
from typing import Type, Any, Optional, Callable, Union
from pathlib import Path
import inspect
import asyncio
import nest_asyncio

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
