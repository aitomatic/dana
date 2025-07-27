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
