"""Common error types for DXA."""

class DXAError(Exception):
    """Base class for all DXA errors."""
    pass

class DXAConnectionError(Exception):
    """Base class for all DXA connection errors."""
    pass

class ResourceError(DXAError):
    """Error in resource operations."""
    pass

class NetworkError(DXAError):
    """Error in network operations."""
    pass

class WebSocketError(NetworkError):
    """WebSocket-specific errors."""
    pass

class ReasoningError(DXAError):
    """Error in reasoning operations."""
    pass

class ConfigurationError(DXAError):
    """Error in configuration."""
    pass

class AgentError(DXAError):
    """Error in agent operations."""
    pass

class CommunicationError(DXAError):
    """Error in communication between components."""
    pass

class ValidationError(DXAError):
    """Error in data validation."""
    pass

class StateError(DXAError):
    """Error in state management."""
    pass 