"""Common exceptions for DXA."""

class DXAError(Exception):
    """Base class for DXA exceptions."""
    pass

class ConfigurationError(DXAError):
    """Configuration related errors."""
    pass

class LLMError(DXAError):
    """LLM related errors."""
    pass 

class ResourceError(DXAError):
    """Resource related errors."""
    pass

class NetworkError(DXAError):
    """Network related errors."""
    pass

class WebSocketError(DXAError):
    """WebSocket related errors."""
    pass

class ReasoningError(DXAError):
    """Reasoning related errors."""
    pass

class AgentError(DXAError):
    """Agent related errors."""
    pass

class CommunicationError(DXAError):
    """Communication related errors."""
    pass

class ValidationError(DXAError):
    """Validation related errors."""
    pass

class StateError(DXAError):
    """State related errors."""
    pass

class DXAMemoryError(DXAError):
    """Memory related errors."""
    pass

class DXAContextError(DXAError):
    """Context related errors."""
    pass