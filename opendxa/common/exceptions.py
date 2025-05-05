"""Common exceptions for DXA."""

from typing import Optional, Dict, Any


class OpenDXAError(Exception):
    """Base class for DXA exceptions."""
    pass


class ConfigurationError(OpenDXAError):
    """Configuration related errors."""
    pass


class LLMError(OpenDXAError):
    """LLM related errors."""
    pass


class LLMProviderError(LLMError):
    """Error from an LLM provider API."""
    
    def __init__(self, provider: str, status_code: Optional[int], message: str):
        """Initialize LLMProviderError.
        
        Args:
            provider: The provider name (e.g., 'openai', 'anthropic')
            status_code: The HTTP status code (if available)
            message: The error message
        """
        self.provider = provider
        self.status_code = status_code
        error_msg = f"{provider} API error" + (f" (status {status_code})" if status_code else "") + f": {message}"
        super().__init__(error_msg)


class LLMRateLimitError(LLMProviderError):
    """Error due to rate limiting."""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Error due to authentication failure."""
    pass


class LLMContextLengthError(LLMProviderError):
    """Error due to context length exceeded."""
    pass


class LLMResponseError(LLMError):
    """Error due to problems with an LLM response."""
    
    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None):
        """Initialize LLMResponseError.
        
        Args:
            message: The error message
            response: The raw response data (if available)
        """
        self.response = response
        super().__init__(message)


class ResourceError(OpenDXAError):
    """Resource related errors."""
    pass


class NetworkError(OpenDXAError):
    """Network related errors."""
    pass


class WebSocketError(OpenDXAError):
    """WebSocket related errors."""
    pass


class ReasoningError(OpenDXAError):
    """Reasoning related errors."""
    pass


class AgentError(OpenDXAError):
    """Agent related errors."""
    pass


class CommunicationError(OpenDXAError):
    """Communication related errors."""
    pass


class ValidationError(OpenDXAError):
    """Validation related errors."""
    pass


class StateError(OpenDXAError):
    """State related errors."""
    pass


class DXAMemoryError(OpenDXAError):
    """Memory related errors."""
    pass


class DXAContextError(OpenDXAError):
    """Context related errors."""
    pass