"""
Main Dana Module Implementation for Python-to-Dana Integration

Provides the familiar Python API for Dana functions while maintaining
sandbox security boundaries.
"""

from typing import Any

from opendxa.contrib.python_to_dana.core.exceptions import DanaCallError
from opendxa.contrib.python_to_dana.core.sandbox_interface import DefaultSandboxInterface
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
        
        # Context manager for resource management
        with dana.get_llm() as llm:
            # Use llm directly if needed
            pass
    """
    
    def __init__(self, debug: bool = False):
        """Initialize the Dana module."""
        self._sandbox_interface = DefaultSandboxInterface(debug=debug)
        self._debug = debug
        self._call_count = 0
    
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
                print(f"DEBUG: Dana call #{self._call_count}: reason('{prompt[:50]}{'...' if len(prompt) > 50 else ''}', {options})")
            
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
    def sandbox(self):
        """Access to underlying sandbox interface (for advanced usage)."""
        return self._sandbox_interface
    
    def __repr__(self) -> str:
        """String representation of Dana module."""
        debug_status = "debug" if self._debug else "normal"
        return f"Dana(mode={debug_status}, calls={self._call_count})" 