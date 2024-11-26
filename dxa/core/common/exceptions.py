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

class ExpertiseError(Exception):
    """Exception raised for expertise-related errors."""
    pass 