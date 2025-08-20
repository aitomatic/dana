"""
In-Process Sandbox Interface for Python-to-Dana Integration

Provides in-process execution of Dana code while maintaining sandbox boundaries.
This is the default implementation that runs Dana in the same Python process.
"""

from typing import Any

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.lang.sandbox_context import SandboxContext
from dana.integrations.python.to_dana.core.exceptions import DanaCallError
from dana.integrations.python.to_dana.core.reasoning_cache import ReasoningCache


class InProcessSandboxInterface:
    """In-process implementation of SandboxInterface using existing DanaSandbox.

    This implementation runs Dana code in the same Python process as the caller,
    providing the best performance while maintaining sandbox security boundaries.

    Features intelligent caching of reasoning results for improved performance.
    """

    def __init__(
        self,
        debug: bool = False,
        context: SandboxContext | None = None,
        enable_cache: bool = True,
        cache_max_size: int = 1000,
        cache_ttl_seconds: float = 300.0,
    ):
        """Initialize the in-process sandbox interface.

        Args:
            debug: Enable debug mode for detailed logging
            context: Sandbox context for configuration and state
            enable_cache: Enable reasoning result caching
            cache_max_size: Maximum number of cached results
            cache_ttl_seconds: Time-to-live for cached results in seconds
        """
        self._debug = debug
        self._context = context
        self._sandbox = DanaSandbox(debug_mode=debug, context=context)

        # Initialize caching
        self._enable_cache = enable_cache
        if enable_cache:
            self._cache = ReasoningCache(max_size=cache_max_size, ttl_seconds=cache_ttl_seconds)
            if debug:
                print(f"DEBUG: InProcessSandboxInterface initialized with cache: max_size={cache_max_size}, ttl={cache_ttl_seconds}s")
        else:
            self._cache = None

    def reason(self, prompt: str, options: dict | None = None) -> Any:
        """Execute Dana reasoning function in-process with caching.

        Args:
            prompt: The question or prompt to send to the LLM
            options: Optional parameters for LLM configuration:
                - system_message: Custom system message (default: helpful assistant)
                - temperature: Controls randomness (default: 0.7)
                - max_tokens: Limit on response length
                - format: Output format ("text" or "json")
                - enable_ipv: Enable IPV optimization (default: True)
                - use_original: Force use of original implementation (default: False)

        Returns:
            The LLM's response to the prompt

        Raises:
            DanaCallError: If the Dana reasoning call fails or invalid options provided
        """
        # Check cache first if enabled
        if self._enable_cache and self._cache is not None:
            cached_result = self._cache.get(prompt, options)
            if cached_result is not None:
                if self._debug:
                    print(f"DEBUG: Cache HIT for prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
                return cached_result
            elif self._debug:
                print(f"DEBUG: Cache MISS for prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")

        # Validate options parameter
        if options is not None:
            if not isinstance(options, dict):
                raise DanaCallError("Options parameter must be a dictionary")

            # Validate option keys
            valid_keys = {"system_message", "temperature", "max_tokens", "format", "enable_ipv", "use_original"}
            invalid_keys = set(options.keys()) - valid_keys
            if invalid_keys:
                raise DanaCallError(f"Invalid option keys: {invalid_keys}. Valid keys: {valid_keys}")

            # Validate option values
            if "temperature" in options:
                temp = options["temperature"]
                if not isinstance(temp, int | float) or not (0.0 <= temp <= 2.0):
                    raise DanaCallError("temperature must be a number between 0.0 and 2.0")

            if "max_tokens" in options:
                max_tokens = options["max_tokens"]
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    raise DanaCallError("max_tokens must be a positive integer")

            if "format" in options:
                fmt = options["format"]
                if fmt not in ["text", "json"]:
                    raise DanaCallError("format must be 'text' or 'json'")

            if "enable_ipv" in options:
                if not isinstance(options["enable_ipv"], bool):
                    raise DanaCallError("enable_ipv must be a boolean")

            if "use_original" in options:
                if not isinstance(options["use_original"], bool):
                    raise DanaCallError("use_original must be a boolean")

        # Build Dana code to call the reason function
        # We need to format the options properly for Dana
        try:
            if options:
                # Convert Python dict to Dana dict format
                options_str = self._format_options_for_dana(options)
                dana_code = f'reason("""{prompt}""", {options_str})'
            else:
                dana_code = f'reason("""{prompt}""")'

            if self._debug:
                print(f"DEBUG: InProcessSandboxInterface executing Dana code: {dana_code[:100]}{'...' if len(dana_code) > 100 else ''}")

            result = self._sandbox.execute_string(dana_code, filename="<python-to-dana>")

            if not result.success:
                raise DanaCallError(f"Dana reasoning failed: {result.error}", original_error=result.error)

            # Cache successful result if caching is enabled
            if self._enable_cache and self._cache is not None and result.result is not None:
                cached_successfully = self._cache.put(prompt, options, result.result)
                if self._debug and cached_successfully:
                    print(f"DEBUG: Cached result for prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")

            return result.result

        except Exception as e:
            if isinstance(e, DanaCallError):
                raise
            raise DanaCallError(f"Failed to execute Dana reasoning: {e}", original_error=e)

    def execute_function(self, func_name: str, args: tuple = (), kwargs: dict | None = None) -> Any:
        """Execute a Dana function with given arguments.

        Args:
            func_name: Name of the Dana function to execute
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the Dana function execution (may be an EagerPromise object)

        Raises:
            DanaCallError: If the Dana function call fails
        """
        try:
            # Build Dana function call
            if args and kwargs:
                # Mix of positional and keyword arguments
                args_str = ", ".join(repr(arg) for arg in args)
                kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
                call_str = f"{func_name}({args_str}, {kwargs_str})"
            elif args:
                # Only positional arguments
                args_str = ", ".join(repr(arg) for arg in args)
                call_str = f"{func_name}({args_str})"
            elif kwargs:
                # Only keyword arguments
                kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
                call_str = f"{func_name}({kwargs_str})"
            else:
                # No arguments
                call_str = f"{func_name}()"

            if self._debug:
                print(f"DEBUG: InProcessSandboxInterface executing Dana function call: {call_str}")

            result = self._sandbox.execute_string(call_str, filename=f"<{func_name}>")

            if not result.success:
                raise DanaCallError(f"Dana function call failed: {result.error}", original_error=result.error)

            # The result may be an EagerPromise object - this is expected behavior
            # Promise transparency will handle resolution when the result is accessed
            return result.result

        except Exception as e:
            if isinstance(e, DanaCallError):
                raise
            raise DanaCallError(f"Failed to execute Dana function '{func_name}': {e}", original_error=e)

    def exec_module(self, file_path: str) -> Any:
        """Execute a Dana module from a file path.

        Args:
            file_path: Path to the Dana (.na) file to execute

        Returns:
            The execution result containing context and any return values

        Raises:
            DanaCallError: If the Dana module execution fails
        """
        try:
            if self._debug:
                print(f"DEBUG: InProcessSandboxInterface executing Dana module from: {file_path}")

            # Read the Dana module file
            with open(file_path, encoding="utf-8") as f:
                dana_code = f.read()

            # Execute the module through the sandbox
            result = self._sandbox.execute_string(dana_code, filename=file_path)

            if not result.success:
                raise DanaCallError(f"Dana module execution failed: {result.error}", original_error=result.error)

            return result

        except FileNotFoundError:
            raise DanaCallError(f"Dana module file not found: {file_path}")
        except PermissionError:
            raise DanaCallError(f"Permission denied reading Dana module: {file_path}")
        except Exception as e:
            if isinstance(e, DanaCallError):
                raise
            raise DanaCallError(f"Failed to execute Dana module from '{file_path}': {e}", original_error=e)

    def _format_options_for_dana(self, options: dict) -> str:
        """Format Python options dict as Dana dict syntax.

        Args:
            options: Python dictionary of options

        Returns:
            String representation in Dana dict format
        """
        if not options:
            return "{}"

        # Convert Python dict to Dana dict format
        items = []
        for key, value in options.items():
            # Format value based on type
            if isinstance(value, str):
                # Escape special characters for Dana string format
                escaped_value = value.replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
                formatted_value = f'"{escaped_value}"'
            elif isinstance(value, bool):
                formatted_value = "true" if value else "false"
            elif isinstance(value, int | float):
                formatted_value = str(value)
            else:
                # For other types, convert to string and quote
                str_value = str(value).replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
                formatted_value = f'"{str_value}"'

            items.append(f'"{key}": {formatted_value}')

        return "{" + ", ".join(items) + "}"

    def get_cache_stats(self) -> dict[str, Any] | None:
        """Get cache statistics if caching is enabled.

        Returns:
            Cache statistics dictionary or None if caching is disabled
        """
        if self._enable_cache and self._cache is not None:
            return self._cache.get_stats()
        return None

    def clear_cache(self):
        """Clear the reasoning cache if enabled."""
        if self._enable_cache and self._cache is not None:
            self._cache.clear()
            if self._debug:
                print("DEBUG: Reasoning cache cleared")

    def get_cache_info(self) -> str:
        """Get formatted cache information for debugging."""
        if self._enable_cache and self._cache is not None:
            return self._cache.get_cache_info()
        return "Caching disabled"

    @property
    def sandbox(self) -> DanaSandbox:
        """Access to underlying sandbox (for advanced usage)."""
        return self._sandbox

    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enable_cache

    def close(self):
        """Close the sandbox interface.

        For in-process implementation, this clears the cache and performs cleanup.
        """
        if self._debug:
            print("DEBUG: InProcessSandboxInterface closing")

        # Clear cache on close
        if self._enable_cache and self._cache is not None:
            self._cache.clear()

        # No specific cleanup needed for in-process sandbox
