"""Common error types for the DXA system.

This module defines the error hierarchy used throughout DXA. The error classes
are organized in a logical hierarchy to allow for both specific and general
error handling:

Error Hierarchy:
- DXAError (base)
  |- DXAConnectionError
  |- ResourceError
  |- NetworkError
     |- WebSocketError
  |- ReasoningError
  |- ConfigurationError
  |- AgentError
  |- CommunicationError
  |- ValidationError
  |- StateError

Each error type represents a specific category of failures that can occur
during system operation.
"""

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