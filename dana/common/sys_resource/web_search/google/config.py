"""Google search service configuration."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from .exceptions import ConfigurationError

load_dotenv()


def _mask_api_key(api_key: str) -> str:
    """Mask API key for secure logging."""
    if not api_key or len(api_key) < 8:
        return "****"
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]


@dataclass
class GoogleSearchConfig:
    """Configuration for Google Custom Search service."""

    # Required API credentials
    api_key: str
    cse_id: str

    # Search settings
    max_results: int = 10
    timeout_seconds: int = 30

    # Content extraction settings
    enable_content_extraction: bool = True
    max_content_length: int = 50000
    content_timeout: int = 15
    max_concurrent_extractions: int = 10

    # Result filtering settings
    skip_domains: list[str] = field(
        default_factory=lambda: [
            "youtube.com",
            "facebook.com",
            "twitter.com",
            "pinterest.com",
            "instagram.com",
            "linkedin.com",
            "reddit.com",
            "tiktok.com",
        ]
    )

    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate configuration parameters."""
        if not self.api_key:
            raise ConfigurationError("Google Search API key is required")

        if not self.cse_id:
            raise ConfigurationError("Google Custom Search Engine ID is required")

        if self.max_results <= 0:
            raise ConfigurationError("max_results must be positive")

        if self.max_results > 10:
            raise ConfigurationError("max_results cannot exceed 10 (Google API limit)")

        if self.timeout_seconds <= 0:
            raise ConfigurationError("timeout_seconds must be positive")

        if self.content_timeout <= 0:
            raise ConfigurationError("content_timeout must be positive")

        if self.max_concurrent_extractions <= 0:
            raise ConfigurationError("max_concurrent_extractions must be positive")

    def __str__(self) -> str:
        """String representation with masked API credentials."""
        return (
            f"GoogleSearchConfig("
            f"api_key={_mask_api_key(self.api_key)}, "
            f"cse_id={self.cse_id[:8]}..., "
            f"max_results={self.max_results}, "
            f"content_extraction={self.enable_content_extraction})"
        )


def load_google_config() -> GoogleSearchConfig:
    """
    Load Google search configuration from environment variables.

    Returns:
        GoogleSearchConfig: Loaded configuration

    Raises:
        ConfigurationError: If required environment variables are missing
    """
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id = os.getenv("GOOGLE_SEARCH_CX")

    if not api_key:
        raise ConfigurationError("GOOGLE_SEARCH_API_KEY environment variable is required")

    if not cse_id:
        raise ConfigurationError("GOOGLE_SEARCH_CX environment variable is required")

    # Optional configuration with defaults
    config = GoogleSearchConfig(
        api_key=api_key,
        cse_id=cse_id,
        max_results=int(os.getenv("GOOGLE_SEARCH_MAX_RESULTS", "10")),
        timeout_seconds=int(os.getenv("GOOGLE_SEARCH_TIMEOUT", "30")),
        enable_content_extraction=os.getenv("ENABLE_CONTENT_EXTRACTION", "true").lower() == "true",
        max_content_length=int(os.getenv("GOOGLE_SEARCH_MAX_CONTENT_LENGTH", "50000")),
        content_timeout=int(os.getenv("GOOGLE_SEARCH_CONTENT_TIMEOUT", "15")),
        max_concurrent_extractions=int(os.getenv("GOOGLE_SEARCH_MAX_CONCURRENT", "10")),
    )

    return config
