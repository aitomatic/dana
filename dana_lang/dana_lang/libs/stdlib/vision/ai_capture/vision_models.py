"""Vision model interfaces and implementations."""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, TypedDict, Union, cast

import anthropic
from loguru import logger
from openai import AsyncAzureOpenAI, AsyncOpenAI, AzureOpenAI, OpenAI
from openai.types.chat import ChatCompletionUserMessageParam
from PIL import Image

from .settings import (
    USE_VISION,
    AnthropicAWSBedrockConfig,
    AnthropicVisionConfig,
    AzureOpenAIVisionConfig,
    GeminiVisionConfig,
    ImageQuality,
    OpenAIVisionConfig,
    VisionModelProvider,
    mask_sensitive_string,
)


def create_default_vision_model() -> VisionModel:
    """Create a vision model instance based on environment configuration."""
    logger.info(f"Creating vision model for provider: {USE_VISION}")
    try:
        if USE_VISION == VisionModelProvider.claude:
            return AnthropicVisionModel()
        elif USE_VISION == VisionModelProvider.openai:
            return OpenAIVisionModel()
        elif USE_VISION == VisionModelProvider.gemini:
            return GeminiVisionModel()
        elif USE_VISION == VisionModelProvider.azure_openai:
            return AzureOpenAIVisionModel()
        elif USE_VISION == VisionModelProvider.anthropic_bedrock:
            return AnthropicAWSBedrockVisionModel()
        else:
            error_msg = f"Unsupported vision model type: {USE_VISION}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    except Exception as e:
        logger.error(f"Failed to create vision model: {str(e)}")
        raise


def is_vision_model_installed() -> bool:
    """Check if a vision model is installed."""
    return USE_VISION in [
        VisionModelProvider.claude,
        VisionModelProvider.openai,
        VisionModelProvider.gemini,
        VisionModelProvider.azure_openai,
        VisionModelProvider.anthropic_bedrock,
    ]


class VisionModel(ABC):
    """Abstract base class for vision models."""

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        api_base: str | None = None,
        image_quality: str = ImageQuality.DEFAULT,
        **kwargs: Any,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.image_quality = image_quality
        self._client: Any = None
        self._aclient: Any = None
        self._kwargs = kwargs
        self.last_token_usage: dict[str, int] = {}

        # Log API credentials
        logger.debug(
            f"Using {self.__class__.__name__}\n"
            f"API Key: {mask_sensitive_string(self.api_key)}\n"
            f"API Base: {self.api_base}\n"
            f"Model: {self.model}\n"
        )

        if not self.api_key:
            logger.error("API key is required")
            raise ValueError("API key is required")
        # if not self.api_base:
        #     logger.error("API base is required")
        #     raise ValueError("API base is required")

    def log_token_usage(self, usage_data: dict[str, int]) -> None:
        """Log token usage statistics."""
        self.last_token_usage = usage_data
        logger.info(f"Token usage: {usage_data}")

    @staticmethod
    def convert_image_to_base64(image: Image.Image) -> tuple[str, str]:
        """Convert PIL Image to base64 string."""
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=95)  # High quality JPEG
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str, "image/jpeg"

    @property
    @abstractmethod
    def client(self) -> Any:
        """Synchronous client getter."""

    @property
    @abstractmethod
    def aclient(self) -> Any:
        """Asynchronous client getter."""

    @abstractmethod
    async def process_image_async(self, image: Union[Image.Image, list[Image.Image]], prompt: str, **kwargs: Any) -> str:
        """Process one or more images asynchronously with the given prompt."""

    @abstractmethod
    def process_image(self, image: Union[Image.Image, list[Image.Image]], prompt: str, **kwargs: Any) -> str:
        """Process one or more images synchronously with the given prompt."""

    @abstractmethod
    async def process_text_async(self, messages: list[Any], **kwargs: Any) -> str:
        """Process text asynchronously with the given prompt."""


class ImageSource(TypedDict):
    type: str
    media_type: str
    data: str


class ImageContent(TypedDict):
    type: str
    source: ImageSource


class TextContent(TypedDict):
    type: str
    text: str


class ImageUrlSource(TypedDict):
    type: str
    url: str
    detail: str


class ImageUrlContent(TypedDict):
    type: str
    image_url: ImageUrlSource


ContentItem = Union[ImageContent, TextContent, ImageUrlContent]


class AnthropicVisionModel(VisionModel):
    """Implementation for Anthropic Claude Vision models."""

    MAX_IMAGES_PER_REQUEST = 100
    MAX_IMAGE_SIZE = (8000, 8000)
    MAX_BATCH_IMAGE_SIZE = (2000, 2000)
    OPTIMAL_IMAGE_SIZE = 1568  # Maximum recommended dimension
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    def __init__(
        self,
        model: str = AnthropicVisionConfig.model,
        api_key: str = AnthropicVisionConfig.api_key,
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, api_key=api_key, **kwargs)

    def _optimize_image(self, image: Image.Image, is_batch: bool = False) -> Image.Image:
        """Optimize image size according to Anthropic's recommendations."""
        max_size = self.MAX_BATCH_IMAGE_SIZE if is_batch else self.MAX_IMAGE_SIZE
        width, height = image.size

        # Check if image exceeds maximum dimensions
        if width > max_size[0] or height > max_size[1]:
            raise ValueError(f"Image dimensions exceed maximum allowed size of {max_size}")

        # Optimize to recommended size if larger
        if width > self.OPTIMAL_IMAGE_SIZE or height > self.OPTIMAL_IMAGE_SIZE:
            ratio = min(self.OPTIMAL_IMAGE_SIZE / width, self.OPTIMAL_IMAGE_SIZE / height)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def _calculate_image_tokens(self, image: Image.Image) -> int:
        """Calculate approximate token usage for an image."""
        width, height = image.size
        return int((width * height) / 750)

    def _prepare_content(self, image: Union[Image.Image, list[Image.Image]], prompt: str) -> list[ContentItem]:
        """Prepare content for Anthropic API with proper image formatting."""
        content: list[ContentItem] = []
        images = [image] if isinstance(image, Image.Image) else image

        # Validate number of images
        if len(images) > self.MAX_IMAGES_PER_REQUEST:
            raise ValueError(f"Maximum {self.MAX_IMAGES_PER_REQUEST} images allowed per request")

        # Process each image
        is_batch = len(images) > 1
        for idx, img in enumerate(images, 1):
            # Optimize image
            optimized_img = self._optimize_image(img, is_batch)

            # Add image label for multiple images
            if is_batch:
                content.append(TextContent(type="text", text=f"Image {idx}:"))

            # Convert and validate image size
            image_data, media_type = self.convert_image_to_base64(optimized_img)
            if len(image_data) > self.MAX_FILE_SIZE:
                raise ValueError(f"Image {idx} exceeds maximum file size of 5MB")

            content.append(
                ImageContent(
                    type="image",
                    source=ImageSource(
                        type="base64",
                        media_type=media_type,
                        data=image_data,
                    ),
                )
            )

        # Add prompt text at the end
        content.append(TextContent(type="text", text=prompt))
        return content

    @property
    def client(self) -> anthropic.Client:
        if self._client is None:
            self._client = anthropic.Client(api_key=self.api_key)
        return cast(anthropic.Client, self._client)

    @property
    def aclient(self) -> anthropic.AsyncClient:
        if self._aclient is None:
            self._aclient = anthropic.AsyncClient(api_key=self.api_key)
        return cast(anthropic.AsyncClient, self._aclient)

    async def process_image_async(self, image: Union[Image.Image, list[Image.Image]], prompt: str, **kwargs: Any) -> str:
        """Process image(s) using Claude Vision asynchronously."""
        content = self._prepare_content(image, prompt)

        # Handle system parameter correctly
        request_params = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.0),
            "messages": [{"role": "user", "content": content}],
            "stream": kwargs.get("stream", False),
        }

        # Only add system if it's provided
        if "system" in kwargs and kwargs["system"] is not None:
            system = kwargs["system"]
            if not isinstance(system, list):
                system = [system]
            request_params["system"] = system

        # Add metadata if provided
        if "metadata" in kwargs:
            request_params["metadata"] = kwargs["metadata"]

        response = await self.aclient.messages.create(**request_params)

        # Log token usage
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }
        self.log_token_usage(usage)

        return str(response.content[0].text)

    def process_image(self, image: Union[Image.Image, list[Image.Image]], prompt: str, **kwargs: Any) -> str:
        """Process image(s) using Claude Vision synchronously."""
        content = self._prepare_content(image, prompt)

        # Handle system parameter correctly
        request_params = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.0),
            "messages": [{"role": "user", "content": content}],
            "stream": kwargs.get("stream", False),
        }

        # Only add system if it's provided
        if "system" in kwargs and kwargs["system"] is not None:
            system = kwargs["system"]
            if not isinstance(system, list):
                system = [system]
            request_params["system"] = system

        # Add metadata if provided
        if "metadata" in kwargs:
            request_params["metadata"] = kwargs["metadata"]

        response = self.client.messages.create(**request_params)

        # Log token usage
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }
        self.log_token_usage(usage)

        return str(response.content[0].text)

    async def process_text_async(self, messages: list[Any], **kwargs: Any) -> str:
        """Process text using Claude Vision asynchronously."""
        request_params = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.0),
            "messages": messages,
        }

        response = await self.aclient.messages.create(**request_params)

        # Log token usage
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }
        self.log_token_usage(usage)

        return str(response.content[0].text)


class OpenAIVisionModel(VisionModel):
    """Implementation for OpenAI GPT-4 Vision models."""

    def __init__(
        self,
        model: str = OpenAIVisionConfig.model,
        api_key: str = OpenAIVisionConfig.api_key,
        api_base: str = OpenAIVisionConfig.api_base,
        image_quality: str = ImageQuality.DEFAULT,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            model=model,
            api_key=api_key,
            api_base=api_base,
            image_quality=image_quality,
            **kwargs,
        )
        if "max_tokens" in kwargs:
            self.max_tokens = kwargs["max_tokens"]
        else:
            self.max_tokens = OpenAIVisionConfig.max_tokens
        if "temperature" in kwargs:
            self.temperature = kwargs["temperature"]
        else:
            self.temperature = OpenAIVisionConfig.temperature

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        return cast(OpenAI, self._client)

    @property
    def aclient(self) -> AsyncOpenAI:
        if self._aclient is None:
            self._aclient = AsyncOpenAI(api_key=self.api_key, base_url=self.api_base)
        return cast(AsyncOpenAI, self._aclient)

    def _prepare_content(self, image: Union[Image.Image, list[Image.Image]], prompt: str) -> list[ContentItem]:
        """Prepare content for OpenAI API."""
        content: list[ContentItem] = []
        images = [image] if isinstance(image, Image.Image) else image

        for img in images:
            base64_image, _ = self.convert_image_to_base64(img)
            content.append(
                ImageUrlContent(
                    type="image_url",
                    image_url=ImageUrlSource(
                        type="base64",
                        url=f"data:image/jpeg;base64,{base64_image}",
                        detail=self.image_quality,
                    ),
                )
            )

        content.append(TextContent(type="text", text=prompt))
        return content

    async def process_image_async(self, image: Union[Image.Image, list[Image.Image]], prompt: str, **kwargs: Any) -> str:
        """Process image(s) using OpenAI Vision asynchronously."""
        content = self._prepare_content(image, prompt)

        message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": content,  # type: ignore
        }

        response = await self.aclient.chat.completions.create(
            model=self.model,
            messages=[message],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=kwargs.get("stream", False),
        )

        # Log token usage
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        self.log_token_usage(usage)

        return response.choices[0].message.content or ""

    def process_image(self, image: Union[Image.Image, list[Image.Image]], prompt: str, **kwargs: Any) -> str:
        """Process image(s) using OpenAI Vision synchronously."""
        content = self._prepare_content(image, prompt)

        message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": content,  # type: ignore
        }
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[message],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=kwargs.get("stream", False),
        )

        # Log token usage
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        self.log_token_usage(usage)

        return response.choices[0].message.content or ""

    async def process_text_async(self, messages: list[Any], **kwargs: Any) -> str:
        """Process text using OpenAI Vision asynchronously."""
        response = await self.aclient.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            stream=kwargs.get("stream", False),
        )

        # Log token usage
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        self.log_token_usage(usage)

        return response.choices[0].message.content or ""


class GeminiVisionModel(OpenAIVisionModel):
    """Implementation for Google's Gemini Vision models using OpenAI compatibility."""

    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    def __init__(
        self,
        model: str = GeminiVisionConfig.model,
        api_key: str = GeminiVisionConfig.api_key,
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, api_key=api_key, api_base=self.GEMINI_BASE_URL, **kwargs)


class AzureOpenAIVisionModel(OpenAIVisionModel):
    """Implementation for Azure OpenAI Vision models."""

    def __init__(
        self,
        model: str = AzureOpenAIVisionConfig.model,
        api_key: str = AzureOpenAIVisionConfig.api_key,
        api_base: str = AzureOpenAIVisionConfig.api_base,
        image_quality: str = ImageQuality.DEFAULT,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            model=model,
            api_key=api_key,
            api_base=api_base,
            image_quality=image_quality,
            **kwargs,
        )
        self.api_version = AzureOpenAIVisionConfig.api_version

    @property
    def client(self) -> AzureOpenAI:
        if self._client is None:
            self._client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.api_base,  # type: ignore
            )
        return cast(AzureOpenAI, self._client)

    @property
    def aclient(self) -> AsyncAzureOpenAI:
        if self._aclient is None:
            self._aclient = AsyncAzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.api_base,  # type: ignore
            )

        return cast(AsyncAzureOpenAI, self._aclient)


class AnthropicAWSBedrockVisionModel(AnthropicVisionModel):
    """Implementation for Anthropic Claude Vision models via AWS Bedrock.

    Extends the standard AnthropicVisionModel but uses Bedrock client instead.
    """

    def __init__(
        self,
        model: str = AnthropicAWSBedrockConfig.model,
        api_key: str = AnthropicAWSBedrockConfig.api_key,
        **kwargs: Any,
    ) -> None:
        # Skip AnthropicVisionModel's __init__ and call VisionModel's __init__ directly
        VisionModel.__init__(self, model=model, api_key=api_key, **kwargs)
        self.aws_access_key_id = AnthropicAWSBedrockConfig.aws_access_key_id
        self.aws_secret_access_key = AnthropicAWSBedrockConfig.aws_secret_access_key
        self.aws_session_token = AnthropicAWSBedrockConfig.aws_session_token
        self.aws_region = AnthropicAWSBedrockConfig.aws_region
        self.aws_vpc_endpoint_url = AnthropicAWSBedrockConfig.aws_vpc_endpoint_url

    @property
    def client(self) -> Any:  # type: ignore
        """Get synchronous Bedrock client."""
        if self._client is None:
            if self.aws_vpc_endpoint_url:
                self._client = anthropic.AnthropicBedrock(
                    aws_access_key=self.aws_access_key_id,
                    aws_secret_key=self.aws_secret_access_key,
                    aws_session_token=self.aws_session_token,
                    aws_region=self.aws_region,
                    base_url=self.aws_vpc_endpoint_url,
                )
            else:
                self._client = anthropic.AnthropicBedrock(
                    aws_access_key=self.aws_access_key_id,
                    aws_secret_key=self.aws_secret_access_key,
                    aws_session_token=self.aws_session_token,
                    aws_region=self.aws_region,
                )
        return self._client

    @property
    def aclient(self) -> Any:  # type: ignore
        """Get asynchronous Bedrock client."""
        if self._aclient is None:
            if self.aws_vpc_endpoint_url:
                self._aclient = anthropic.AsyncAnthropicBedrock(
                    aws_access_key=self.aws_access_key_id,
                    aws_secret_key=self.aws_secret_access_key,
                    aws_session_token=self.aws_session_token,
                    aws_region=self.aws_region,
                    base_url=self.aws_vpc_endpoint_url,
                )
            else:
                self._aclient = anthropic.AsyncAnthropicBedrock(
                    aws_access_key=self.aws_access_key_id,
                    aws_secret_key=self.aws_secret_access_key,
                    aws_session_token=self.aws_session_token,
                    aws_region=self.aws_region,
                )
        return self._aclient

    # Reusing all the image processing methods from the parent class
