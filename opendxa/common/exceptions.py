"""Common exceptions for DXA."""

class OpenDXAError(Exception):
    """Base class for DXA exceptions."""
    pass

class ConfigurationError(OpenDXAError):
    """Configuration related errors."""
    pass

class LLMError(OpenDXAError):
    """LLM related errors."""
    pass 

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