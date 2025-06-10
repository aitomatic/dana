"""
Main Dana Module Implementation for Python-to-Dana Integration

Provides the familiar Python API for Dana functions while maintaining
sandbox security boundaries.
"""

from typing import Any

from opendxa.contrib.python_to_dana.core.exceptions import DanaCallError
from opendxa.contrib.python_to_dana.core.inprocess_sandbox import InProcessSandboxInterface
from opendxa.contrib.python_to_dana.core.subprocess_sandbox import SUBPROCESS_ISOLATION_CONFIG, SubprocessSandboxInterface
from opendxa.contrib.python_to_dana.utils.converter import validate_and_convert


class Dana:
    """
    Main Dana module implementation.
    
    This class provides the Python-friendly interface to Dana's capabilities
    while maintaining security boundaries through the sandbox interface.
    
    Example usage:
        from opendxa.dana import dana
        
        result = dana.reason("What is 2+2?")
        print(result)
        
        # With options
        result = dana.reason("Analyze this text", {
            "temperature": 0.5,
            "max_tokens": 100
        })
        
        # With subprocess isolation (future)
        dana_isolated = Dana(use_subprocess_isolation=True)
        result = dana_isolated.reason("What is 2+2?")
    """
    
    def __init__(self, debug: bool = False, use_subprocess_isolation: bool = False):
        """Initialize the Dana module.
        
        Args:
            debug: Enable debug mode
            use_subprocess_isolation: Use subprocess isolation (placeholder - not implemented yet)
        """
        self._debug = debug
        self._use_subprocess_isolation = use_subprocess_isolation
        self._call_count = 0
        
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
                print(f"DEBUG: Dana call #{self._call_count} ({isolation_mode}): reason('{prompt[:50]}{'...' if len(prompt) > 50 else ''}', {options})")
            
            result = self._sandbox_interface.reason(prompt, options)
            
            if self._debug:
                print(f"DEBUG: Call #{self._call_count} succeeded, result type: {type(result)}")
            
            return result
        
        except Exception as e:
            if self._debug:
                print(f"DEBUG: Call #{self._call_count} failed: {type(e).__name__}: {e}")
            
            if isinstance(e, (TypeError, DanaCallError)):
                raise
            raise DanaCallError(f"Unexpected error in reasoning: {e}", original_error=e)
    
    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self._debug
    
    @property
    def is_subprocess_isolated(self) -> bool:
        """Check if using subprocess isolation."""
        return self._use_subprocess_isolation and hasattr(self._sandbox_interface, 'is_subprocess_isolated') and self._sandbox_interface.is_subprocess_isolated
    
    @property 
    def sandbox(self):
        """Access to underlying sandbox interface (for advanced usage)."""
        return self._sandbox_interface
    
    def restart_subprocess(self):
        """Restart the Dana subprocess (if using subprocess isolation)."""
        if hasattr(self._sandbox_interface, 'restart_subprocess'):
            self._sandbox_interface.restart_subprocess()
        elif self._debug:
            print("DEBUG: Subprocess restart not available for in-process sandbox")
    
    def close(self):
        """Close the Dana instance and cleanup resources."""
        if hasattr(self._sandbox_interface, 'close'):
            self._sandbox_interface.close()
    
    def __repr__(self) -> str:
        """String representation of Dana module."""
        debug_status = "debug" if self._debug else "normal"
        isolation_status = "subprocess-isolated" if self.is_subprocess_isolated else "in-process"
        return f"Dana(mode={debug_status}, isolation={isolation_status}, calls={self._call_count})"
    
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