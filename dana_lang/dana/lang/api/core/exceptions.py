"""Custom exceptions for Dana API."""


class DanaAPIException(Exception):
    """Base exception for Dana API."""

    pass


class AgentNotFoundError(DanaAPIException):
    """Raised when an agent is not found."""

    pass


class TopicNotFoundError(DanaAPIException):
    """Raised when a topic is not found."""

    pass


class DocumentNotFoundError(DanaAPIException):
    """Raised when a document is not found."""

    pass


class ConversationNotFoundError(DanaAPIException):
    """Raised when a conversation is not found."""

    pass


class ValidationError(DanaAPIException):
    """Raised when validation fails."""

    pass


class DatabaseError(DanaAPIException):
    """Raised when database operations fail."""

    pass


class CodeGenerationError(DanaAPIException):
    """Raised when code generation fails."""

    pass


class DomainKnowledgeError(DanaAPIException):
    """Raised when domain knowledge operations fail."""

    pass


class AgentGenerationError(DanaAPIException):
    """Raised when agent generation fails."""

    pass


class LLMServiceError(DanaAPIException):
    """Raised when LLM service operations fail."""

    pass


class ConfigurationError(DanaAPIException):
    """Raised when configuration is invalid."""

    pass


class AuthenticationError(DanaAPIException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(DanaAPIException):
    """Raised when authorization fails."""

    pass


class RateLimitError(DanaAPIException):
    """Raised when rate limit is exceeded."""

    pass


class TimeoutError(DanaAPIException):
    """Raised when operations timeout."""

    pass


class NetworkError(DanaAPIException):
    """Raised when network operations fail."""

    pass
