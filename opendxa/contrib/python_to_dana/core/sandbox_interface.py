"""
Sandbox Interface Protocol for Python-to-Dana Integration

Provides a clean protocol interface that wraps the existing DanaSandbox
and prepares for future process isolation.
"""

from typing import Any, Protocol

from opendxa.contrib.python_to_dana.core.exceptions import DanaCallError
from opendxa.dana.sandbox.dana_sandbox import DanaSandbox
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class SandboxInterface(Protocol):
    """Interface to Dana Sandbox - process boundary abstraction."""
    
    def reason(self, prompt: str, options: dict | None = None) -> Any:
        """Core reasoning function."""
        ...
    
class DefaultSandboxInterface:
    """Default implementation of SandboxInterface using existing DanaSandbox."""
    
    def __init__(self, debug: bool = False, context: SandboxContext | None = None):
        """Initialize the sandbox interface."""
        self._sandbox = DanaSandbox(debug=debug, context=context)
    
    def reason(self, prompt: str, options: dict | None = None) -> Any:
        """Execute Dana reasoning function.
        
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
        """
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
                if not isinstance(temp, (int, float)) or not (0.0 <= temp <= 2.0):
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
            prompt = repr(prompt)
            if options:
                # Convert Python dict to Dana dict format
                options_str = self._format_options_for_dana(options)
                dana_code = f'reason("{prompt}", {options_str})'
            else:
                dana_code = f'reason("{prompt}")'
            result = self._sandbox.eval(dana_code, filename="<python-to-dana>")
            
            if not result.success:
                raise DanaCallError(
                    f"Dana reasoning failed: {result.error}",
                    original_error=result.error
                )
            
            return result.result
            
        except Exception as e:
            if isinstance(e, DanaCallError):
                raise
            raise DanaCallError(f"Failed to execute Dana reasoning: {e}", original_error=e)
    
    
    def _format_options_for_dana(self, options: dict) -> str:
        """Format Python options dict as Dana dict syntax."""
        if not options:
            return "{}"
        
        # Convert Python dict to Dana dict format
        items = []
        for key, value in options.items():
            # Format value based on type
            if isinstance(value, str):
                # Escape special characters for Dana string format
                escaped_value = value.replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
                formatted_value = f'"{escaped_value}"'
            elif isinstance(value, bool):
                formatted_value = "true" if value else "false"
            elif isinstance(value, (int, float)):
                formatted_value = str(value)
            else:
                # For other types, convert to string and quote
                str_value = str(value).replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
                formatted_value = f'"{str_value}"'
            
            items.append(f'"{key}": {formatted_value}')
        
        return "{" + ", ".join(items) + "}"
    
    @property 
    def sandbox(self) -> DanaSandbox:
        """Access to underlying sandbox (for advanced usage)."""
        return self._sandbox 