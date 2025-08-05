"""Miscellaneous utilities."""

import asyncio
import base64
import hashlib
import inspect

# Configure asyncio to only warn about tasks taking longer than 30 seconds
# (LLM operations typically take 1-10 seconds, so this avoids false warnings)
import logging
import uuid
import warnings
from collections.abc import Callable
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from dana.common.types import BaseResponse

asyncio_logger = logging.getLogger("asyncio")
asyncio_logger.setLevel(logging.ERROR)


# Configure asyncio slow task threshold
def configure_asyncio_threshold():
    """Configure asyncio to use a 30-second threshold for slow task warnings."""
    try:
        # Get the current event loop policy
        policy = asyncio.get_event_loop_policy()

        # Set slow task threshold to 30 seconds (default is usually 0.1 seconds)
        if hasattr(policy, "_slow_callback_duration"):
            policy._slow_callback_duration = 30.0
        else:
            # Alternative: set environment variable before asyncio is used
            import os

            os.environ["PYTHONASYNCIOSLOWTASKTHRESHOLD"] = "30.0"
    except Exception:
        # Fallback: suppress warnings if configuration fails
        warnings.filterwarnings("ignore", message=".*asyncio.*", category=RuntimeWarning)


# Apply the configuration
configure_asyncio_threshold()


class ParsedArgKwargsResults(BaseModel):
    matched_args: list[Any]
    matched_kwargs: dict[str, Any]
    varargs: list[Any]
    varkwargs: dict[str, Any]
    unmatched_args: list[Any]
    unmatched_kwargs: dict[str, Any]


class Misc:
    """A collection of miscellaneous utility methods."""

    @staticmethod
    @lru_cache(maxsize=128)
    def load_yaml_config(path: str | Path) -> dict[str, Any]:
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
            path = Misc._resolve_yaml_path(path)

        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def _resolve_yaml_path(path: Path) -> Path:
        """Helper to resolve path with different YAML extensions."""
        # Try .yaml extension
        yaml_path = path.with_suffix(".yaml")
        if yaml_path.exists():
            return yaml_path

        # Try .yml extension
        yml_path = path.with_suffix(".yml")
        if yml_path.exists():
            return yml_path

        raise FileNotFoundError(f"YAML file not found: {path}")

    @staticmethod
    def get_class_by_name(class_path: str) -> type[Any]:
        """Get class by its fully qualified name.

        Example:
            get_class_by_name("dana.common.graph.traversal.Cursor")
        """
        module_path, class_name = class_path.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, class_name)

    @staticmethod
    def get_base_path(for_class: type[Any]) -> Path:
        """Get base path for the given class."""
        return Path(inspect.getfile(for_class)).parent

    @staticmethod
    def get_config_path(
        for_class: type[Any],
        config_dir: str = "config",
        file_extension: str = "cfg",
        default_config_file: str = "default",
        path: str | None = None,
    ) -> Path:
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
            if config_dir == "yaml" and "." in path and not path.endswith((".yaml", ".yml")):
                # Convert dots to slashes
                path_parts = path.split(".")
                path = "/".join(path_parts)

                # Check if the file exists with the path directly
                base_path = Misc.get_base_path(for_class) / config_dir
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
            return Misc.get_base_path(for_class) / config_dir / path

        # Build the full path with the file extension
        return Misc.get_base_path(for_class) / config_dir / f"{path}.{file_extension}"

    @staticmethod
    def safe_asyncio_run(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run a function in an asyncio loop with smart event loop handling.

        This method handles all scenarios:
        - No event loop running: Uses asyncio.run()
        - Event loop running in async context: Uses await
        - Event loop running in sync context: Uses loop.create_task() and run_until_complete()

        This approach eliminates the need for nest_asyncio and works in:
        - Jupyter notebooks
        - FastMCP environments
        - Standard Python scripts
        - Any async framework

        Args:
            func: The async function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the async function
        """
        # Check if we're already in an event loop
        try:
            asyncio.get_running_loop()
            # We're in a running event loop
            return Misc._run_in_existing_loop(func, *args, **kwargs)
        except RuntimeError:
            # No event loop is running, we can use asyncio.run()
            return asyncio.run(func(*args, **kwargs))

    @staticmethod
    def _run_in_existing_loop(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run a function in an existing event loop.

        This method handles the case where we're already in an event loop
        and need to execute an async function. It uses a thread-based approach
        to avoid interfering with the existing event loop.
        """
        # Use a thread-based approach to avoid event loop conflicts
        import concurrent.futures

        def run_in_thread():
            # Create a new event loop in this thread and run the function
            return asyncio.run(func(*args, **kwargs))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()

    @staticmethod
    def get_field(obj: dict | object, field_name: str, default: Any = None) -> Any:
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

    @staticmethod
    def has_field(obj: dict | object, field_name: str) -> bool:
        """Check if an object has a field."""
        if isinstance(obj, dict):
            return field_name in obj
        return hasattr(obj, field_name)

    @staticmethod
    def generate_base64_uuid(length: int | None = None) -> str:
        """Generate a base64-encoded UUID with optional length truncation.

        Args:
            length: Optional length to truncate the UUID to. If None, returns full UUID.
                   Must be between 1 and 22 (full base64-encoded UUID length).

        Returns:
            A base64-encoded UUID string, optionally truncated to the specified length.

        Raises:
            ValueError: If length is not between 1 and 22
        """
        # Generate a UUID4 (random UUID)
        uuid_bytes = uuid.uuid4().bytes

        # Encode to base64 and make it URL-safe
        encoded = base64.urlsafe_b64encode(uuid_bytes).decode("ascii")

        # Remove padding characters
        encoded = encoded.rstrip("=")

        if length is not None:
            if not 1 <= length <= 22:
                raise ValueError("Length must be between 1 and 22")
            return encoded[:length]

        return encoded

    @staticmethod
    def parse_args_kwargs(func, *args, **kwargs) -> ParsedArgKwargsResults:
        import inspect

        """
        Bind (args, kwargs) to `func`'s signature, returning a dict with:
        - matched_args:      positional args that were bound to named parameters
        - matched_kwargs:    keyword args that were bound to named or kw-only parameters
        - varargs:           values that ended up in func's *args (if it has one)
        - varkwargs:         values that ended up in func's **kwargs (if it has one)
        - unmatched_args:    positional args that couldn't be bound (and no *args present)
        - unmatched_kwargs:  keyword args that couldn't be bound (and no **kwargs present)
        """
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        matched_args = []
        matched_kwargs = {}
        varargs = []
        varkwargs = {}
        unmatched_args = []
        unmatched_kwargs = {}

        # Separate out which parameters are "named positional" (POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD)
        pos_params = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        # Which are keyword-only
        kwonly_params = [p for p in params if p.kind == p.KEYWORD_ONLY]

        # Check if func has *args or **kwargs
        has_var_pos = any(p.kind == p.VAR_POSITIONAL for p in params)
        has_var_kw = any(p.kind == p.VAR_KEYWORD for p in params)

        # 1) Assign positional arguments
        for index, value in enumerate(args):
            if index < len(pos_params):
                # Still within the "named positional" slots
                matched_args.append(value)
            else:
                # No more named positional slots left
                if has_var_pos:
                    varargs.append(value)
                else:
                    unmatched_args.append(value)

        # 2) Assign keyword arguments
        #    If the key matches one of the named parameters (positional or kw-only), consume it.
        named_param_names = {p.name for p in (pos_params + kwonly_params)}
        for key, value in kwargs.items():
            if key in named_param_names:
                matched_kwargs[key] = value
            else:
                if has_var_kw:
                    varkwargs[key] = value
                else:
                    unmatched_kwargs[key] = value

        return ParsedArgKwargsResults(
            matched_args=matched_args,
            matched_kwargs=matched_kwargs,
            varargs=varargs,
            varkwargs=varkwargs,
            unmatched_args=unmatched_args,
            unmatched_kwargs=unmatched_kwargs,
        )

    @staticmethod
    def get_hash(key: str, length: int | None = None) -> str:
        hash_key = hashlib.sha256(key.encode()).hexdigest()
        if length is not None:
            return hash_key[:length]
        return hash_key

    @staticmethod
    def generate_uuid(length: int | None = None) -> str:
        """Generate a UUID with optional length truncation."""
        uuid_str = str(uuid.uuid4())
        if length is not None:
            return uuid_str[:length]
        return uuid_str

    @staticmethod
    def text_to_dict(text: str) -> dict[str, Any]:
        """Parse JSON content from LLM text response."""
        import json
        import re

        # Check if content is wrapped in ```json``` tags
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            # Extract and parse the JSON content
            json_content = json_match.group(1)
            parsed_json = json.loads(json_content)
            return parsed_json
        else:
            try:
                parsed_json = json.loads(text)
                return parsed_json
            except Exception as e:
                raise ValueError(f"Failed to parse JSON: {str(e)}")

    @staticmethod
    def get_response_content(response: BaseResponse) -> Any:
        """Get the content of a BaseResponse."""
        content = Misc.get_field(response, "content", None)
        if content is None:
            raise ValueError(f"No content found in BaseResponse : {response}")
        choices = Misc.get_field(content, "choices", [])
        if len(choices) == 0:
            raise ValueError(f"No choices found in BaseResponse : {response}")
        choice = choices[0]
        message = Misc.get_field(choice, "message", None)
        if message is None:
            raise ValueError(f"No message found in BaseResponse : {response}")
        content = Misc.get_field(message, "content", None)
        if content is None:
            raise ValueError(f"No content found in BaseResponse : {response}")
        return content
