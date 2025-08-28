"""
Main Dana Module Implementation for Python-to-Dana Integration

Provides the familiar Python API for Dana functions while maintaining
sandbox security boundaries. Now includes module import capabilities.
"""

import inspect
import os
from typing import Any

from dana.integrations.python.to_dana.core.exceptions import DanaCallError
from dana.integrations.python.to_dana.core.inprocess_sandbox import InProcessSandboxInterface
from dana.integrations.python.to_dana.core.module_importer import install_import_hook, list_available_modules, uninstall_import_hook
from dana.integrations.python.to_dana.core.subprocess_sandbox import SUBPROCESS_ISOLATION_CONFIG, SubprocessSandboxInterface
from dana.integrations.python.to_dana.utils.converter import validate_and_convert


def _get_caller_directory() -> str:
    """Get the directory of the script that called enable_module_imports."""
    # Look through the call stack to find the first frame outside this module
    for frame_info in inspect.stack():
        frame_path = frame_info.filename
        # Skip frames from this module and the inspect module itself
        if not frame_path.endswith("dana_module.py") and "inspect.py" not in frame_path:
            return os.path.dirname(os.path.abspath(frame_path))
    # Fallback to current working directory if we can't determine caller
    return os.getcwd()


class Dana:
    """
    Main Dana module implementation with module import capabilities.

    This class provides the Python-friendly interface to Dana's capabilities
    while maintaining security boundaries through the sandbox interface.
    Now supports direct importing of Dana .na files in Python code.

    Example usage:
        from dana.dana import dana

        # Traditional reasoning
        result = dana.reason("What is 2+2?")
        print(result)

        # Enable module imports
        dana.enable_module_imports()

        # Now you can import Dana modules directly
        import simple_math
        result = simple_math.add(5, 3)
        print(result)

        # List available modules
        modules = dana.list_modules()
        print(f"Available Dana modules: {modules}")
    """

    def __init__(self, debug: bool = False, use_subprocess_isolation: bool = False, enable_imports: bool = False):
        """Initialize the Dana module.

        Args:
            debug: Enable debug mode
            use_subprocess_isolation: Use subprocess isolation (placeholder - not implemented yet)
            enable_imports: Automatically enable module imports on initialization
        """
        self._debug = debug
        self._use_subprocess_isolation = use_subprocess_isolation
        self._call_count = 0
        self._imports_enabled = False
        self._closed = False

        # TODO: Remove this check when subprocess isolation is implemented
        if use_subprocess_isolation and not SUBPROCESS_ISOLATION_CONFIG["enabled"]:
            if debug:
                print("DEBUG: Subprocess isolation requested but not yet implemented, falling back to in-process")
            use_subprocess_isolation = False

        # Initialize the appropriate sandbox interface
        if use_subprocess_isolation:
            self._sandbox_interface = SubprocessSandboxInterface(debug=debug)
        else:
            self._sandbox_interface = InProcessSandboxInterface(debug=debug)

        # Enable imports if requested
        if enable_imports:
            self.enable_module_imports()

    def reason(self, prompt: str, options: dict | None = None) -> Any:
        """
        Core reasoning function using Dana's LLM capabilities.

        Args:
            prompt: The question or prompt to send to the LLM
            options: Optional parameters for LLM configuration:
                - system_message: str - Custom system message (default: helpful assistant)
                - temperature: float - Controls randomness (0.0-2.0, default: 0.7)
                - max_tokens: int - Limit on response length
                - format: str - Output format ("text" or "json")
                - enable_ipv: bool - Enable IPV optimization (default: True)
                - use_original: bool - Force use of original implementation (default: False)

        Returns:
            The LLM's response to the prompt

        Raises:
            TypeError: If prompt is not a string or options is not a dict
            DanaCallError: If the Dana reasoning call fails or invalid options provided
        """
        # Validate input types
        prompt = validate_and_convert(prompt, str, "argument 'prompt'")

        if options is not None:
            options = validate_and_convert(options, dict, "argument 'options'")

        try:
            self._call_count += 1
            if self._debug:
                isolation_mode = "subprocess-isolated" if self._use_subprocess_isolation else "in-process"
                print(
                    f"DEBUG: Dana call #{self._call_count} ({isolation_mode}): reason('{prompt[:50]}{'...' if len(prompt) > 50 else ''}', {options})"
                )

            result = self._sandbox_interface.reason(prompt, options)

            if self._debug:
                print(f"DEBUG: Call #{self._call_count} succeeded, result type: {type(result)}")

            return result

        except Exception as e:
            if self._debug:
                print(f"DEBUG: Call #{self._call_count} failed: {type(e).__name__}: {e}")

            if isinstance(e, TypeError | DanaCallError):
                raise
            raise DanaCallError(f"Unexpected error in reasoning: {e}", original_error=e)

    def enable_module_imports(self, search_paths: list[str] | None = None) -> None:
        """Enable importing Dana .na files directly in Python.

        Args:
            search_paths: Optional list of paths to search for .na files.
                         If None, automatically includes the calling script's directory.

        Example:
            dana.enable_module_imports()
            import simple_math  # This will load simple_math.na from the script's directory
            result = simple_math.add(5, 3)
        """
        if not self._imports_enabled:
            # Automatically include calling script's directory if no paths specified
            if search_paths is None:
                caller_dir = _get_caller_directory()
                search_paths = [caller_dir]
            else:
                # Add calling script's directory to user-specified paths if not already included
                caller_dir = _get_caller_directory()
                if caller_dir not in search_paths:
                    search_paths = [caller_dir] + search_paths

            install_import_hook(search_paths=search_paths, sandbox_interface=self._sandbox_interface, debug=self._debug)
            self._imports_enabled = True
            if self._debug:
                print(f"DEBUG: Dana module imports enabled with search paths: {search_paths}")

    def disable_module_imports(self) -> None:
        """Disable Dana module imports."""
        if self._imports_enabled:
            uninstall_import_hook()
            self._imports_enabled = False
            if self._debug:
                print("DEBUG: Dana module imports disabled")

    def list_modules(self, search_paths: list[str] | None = None) -> list[str]:
        """List all available Dana modules.

        Args:
            search_paths: Optional list of paths to search

        Returns:
            List of available module names
        """
        return list_available_modules(search_paths)

    @property
    def imports_enabled(self) -> bool:
        """Check if module imports are enabled."""
        return self._imports_enabled

    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self._debug

    @property
    def is_subprocess_isolated(self) -> bool:
        """Check if using subprocess isolation."""
        return (
            self._use_subprocess_isolation
            and hasattr(self._sandbox_interface, "is_subprocess_isolated")
            and self._sandbox_interface.is_subprocess_isolated
        )

    @property
    def sandbox(self):
        """Access to underlying sandbox interface (for advanced usage)."""
        return self._sandbox_interface

    def restart_subprocess(self):
        """Restart the Dana subprocess (if using subprocess isolation)."""
        if hasattr(self._sandbox_interface, "restart_subprocess"):
            self._sandbox_interface.restart_subprocess()
        elif self._debug:
            print("DEBUG: Subprocess restart not available for in-process sandbox")

    def close(self):
        """Close the Dana instance and cleanup resources."""
        if self._closed:
            return

        self._closed = True

        if self._imports_enabled:
            self.disable_module_imports()

        if hasattr(self._sandbox_interface, "close"):
            self._sandbox_interface.close()

    def __repr__(self) -> str:
        """String representation of Dana module."""
        debug_status = "debug" if self._debug else "normal"
        isolation_status = "subprocess-isolated" if self.is_subprocess_isolated else "in-process"
        imports_status = "imports-enabled" if self._imports_enabled else "imports-disabled"
        return f"Dana(mode={debug_status}, isolation={isolation_status}, {imports_status}, calls={self._call_count})"

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def __del__(self):
        """Cleanup on deletion."""
        self.close()

    def set_debug(self, debug: bool) -> None:
        """Set debug mode for Dana instance.

        Args:
            debug: Enable or disable debug mode
        """
        self._debug = debug
        if hasattr(self._sandbox_interface, "debug"):
            self._sandbox_interface.debug = debug
