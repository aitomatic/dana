"""Custom exceptions for DXA."""

class DXAError(Exception):
    """Base class for all DXA exceptions."""
    pass

class ResourceError(DXAError):
    """Base class for resource-related errors."""
    pass

class LLMError(ResourceError):
    """Exception raised for LLM-related errors."""
    pass

class ExpertError(ResourceError):
    """Error in expert resource interaction."""
    pass

class DXAMemoryError(ResourceError):
    """Exception raised for memory-related errors."""
    pass

class ReasoningError(DXAError):
    """Error in reasoning process."""
    pass

class ParseError(ReasoningError):
    """Error parsing LLM response."""
    pass

class ValidationError(DXAError):
    """Error validating data."""
    pass

class ConfigurationError(DXAError):
    """Error in configuration."""
    pass

class AgentError(DXAError):
    """Error in agent operation."""
    pass

class ExpertiseError(DXAError):
    """Exception raised for expertise-related errors."""
    pass

class DXAConnectionError(DXAError):
    """Error in establishing connections."""
    pass

class NetworkError(DXAConnectionError):
    """Network-related errors."""
    pass

class WebSocketError(NetworkError):
    """WebSocket-specific errors."""
    pass

class CommunicationError(DXAError):
    """Error in communication between components."""
    pass

class StateError(DXAError):
    """Error in state management."""
    pass 