"""Google search service exceptions."""


class GoogleSearchError(Exception):
    """Base exception for Google search errors."""

    pass


class RateLimitError(GoogleSearchError):
    """Google API rate limit exceeded."""

    pass


class APIKeyError(GoogleSearchError):
    """Invalid or missing API key."""

    pass


class ServiceUnavailableError(GoogleSearchError):
    """Google API service temporarily unavailable."""

    pass


class ContentExtractionError(GoogleSearchError):
    """Error during web content extraction."""

    pass


class ConfigurationError(GoogleSearchError):
    """Configuration validation error."""

    pass
