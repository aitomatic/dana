"""Vision model settings and configurations."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from loguru import logger

load_dotenv(override=True)


def mask_sensitive_string(value: str | None, visible_chars: int = 4) -> str:
    """Mask sensitive string showing only first few characters."""
    if not value:
        return ""
    return value[:visible_chars] + "*" * (len(value) - visible_chars)


def validate_required_config(name: str, value: str | None, provider: str) -> None:
    """Validate required configuration value."""
    if not value:
        error_msg = f"Missing required configuration '{name}' for {provider}"
        logger.error(error_msg)
        raise ValueError(error_msg)


class VisionModelProvider:
    claude = "claude"
    openai = "openai"
    azure_openai = "azure-openai"
    gemini = "gemini"
    openai_alike = "openai-alike"
    anthropic_bedrock = "anthropic_bedrock"


# Default vision model configuration
USE_VISION = os.getenv("USE_VISION", VisionModelProvider.openai).lower()
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "20"))


# Image quality settings
class ImageQuality:
    """Image quality settings for vision models."""

    LOW_RES = "low"  # 512px x 512px
    HIGH_RES = "high"  # max 768px x 2000px
    DEFAULT = HIGH_RES


@dataclass
class VisionModelConfig:
    """Base configuration for vision models."""

    model: str
    api_key: str | None = None
    api_base: str | None = None
    image_quality: str = ImageQuality.DEFAULT

    def validate(self, provider: str) -> None:
        """Validate configuration."""
        validate_required_config("model", self.model, provider)
        validate_required_config("api_key", self.api_key, provider)


class AnthropicVisionConfig(VisionModelConfig):
    """Configuration for Anthropic Claude Vision models."""

    api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    def __post_init__(self) -> None:
        """Validate Anthropic configuration."""
        self.validate("Anthropic Claude")


class OpenAIVisionConfig(VisionModelConfig):
    """Configuration for OpenAI GPT-4 Vision models."""

    api_key: str = os.getenv("OPENAI_VISION_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("OPENAI_VISION_MODEL", "") or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    api_base: str = os.getenv("OPENAI_VISION_BASE_URL", "") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "5000"))
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))

    def __post_init__(self) -> None:
        """Validate OpenAI configuration."""
        self.validate("OpenAI")


class GeminiVisionConfig(VisionModelConfig):
    """Configuration for Google Gemini Vision models."""

    api_key: str = os.getenv("GEMINI_API_KEY", "")
    model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-04-17")

    def __post_init__(self) -> None:
        """Validate Gemini configuration."""
        self.validate("Google Gemini")


class AzureOpenAIVisionConfig(VisionModelConfig):
    """Configuration for Azure OpenAI Vision models."""

    api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    model: str = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
    api_base: str = os.getenv("AZURE_OPENAI_API_URL", "https://aitomaticjapaneast.openai.azure.com")
    api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-11-01-preview")

    def __post_init__(self) -> None:
        """Validate Azure OpenAI configuration."""
        self.validate("Azure OpenAI")
        validate_required_config("api_version", self.api_version, "Azure OpenAI")
        validate_required_config("api_base", self.api_base, "Azure OpenAI")


class AnthropicAWSBedrockConfig(VisionModelConfig):
    """Configuration for Anthropic Claude Vision models via AWS Bedrock."""

    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "dummy")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "dummy")
    aws_session_token: str | None = os.getenv("AWS_SESSION_TOKEN", None)
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_vpc_endpoint_url: str = os.getenv("AWS_BEDROCK_VPC_ENDPOINT_URL", "")
    model: str = os.getenv("ANTHROPIC_BEDROCK_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0")  # noqa
    api_key: str = os.getenv("ANTHROPIC_BEDROCK_API_KEY", "dummy")  # dont need this
