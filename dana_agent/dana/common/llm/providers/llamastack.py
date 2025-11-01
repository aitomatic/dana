"""
LlamaStack Provider Implementation

Integrates with Meta's Llama Stack - a unified interface for inference across
multiple LLM providers (Llama, OpenAI, Anthropic, DeepSeek, etc.).

LlamaStack acts as a local server that proxies to multiple configured providers.
API keys for external providers are configured on the LlamaStack server side,
not in this code. Uses OpenAI-compatible API, similar to OpenRouter.
"""

from typing import Literal

import structlog

from ...llamastack.client import LlamaStackClientManager
from ..types import LLMMessage, LLMProvider, LLMResponse, ProviderError


logger = structlog.get_logger()


class LlamaStackProvider(LLMProvider):
    """
    LlamaStack API provider - unified interface for multiple LLM providers.

    Supports any model from any provider configured on the LlamaStack server
    (e.g., meta-llama/Llama-3.2-3B-Instruct, deepseek/deepseek-coder,
    openai/gpt-4, anthropic/claude-3-opus, etc.).

    API keys for external providers are managed server-side.
    """

    def __init__(self, base_url: str | None = None, model: str = "meta-llama/Llama-3.2-3B-Instruct", **kwargs):
        """
        Initialize LlamaStack provider. API keys are managed LS-side.

        Args:
            base_url: LlamaStack server URL (defaults to LLAMA_STACK_URL env var or localhost:8321)
            model: Model identifier in format "provider/model-name"
            **kwargs: Additional arguments
        """
        self.model = model
        try:
            self.client = LlamaStackClientManager.get_client()
        except Exception as e:
            raise ProviderError(f"Failed to initialize LlamaStack client: {e}")

        # Register model if not already registered
        try:
            registered_models = self.client.models.list()
            if hasattr(registered_models, "data") and registered_models.data is not None:
                models_list = registered_models.data
            else:
                models_list = []
            model_identifiers = [m.identifier for m in models_list] if models_list else []

            if self.model not in model_identifiers:
                if "/" in self.model:
                    provider_id, provider_model_id = self.model.split("/", 1)
                else:
                    provider_id = None
                    provider_model_id = self.model

                model_type: Literal["llm", "embedding"] = "llm"

                if provider_id:
                    self.client.models.register(
                        model_id=self.model,
                        model_type=model_type,
                        provider_model_id=provider_model_id,
                        provider_id=provider_id,
                    )
                else:
                    # Don't pass provider_id if None (it defaults to omit)
                    self.client.models.register(
                        model_id=self.model,
                        model_type=model_type,
                        provider_model_id=provider_model_id,
                    )
                logger.info("Registered model with LlamaStack", model=self.model, provider_id=provider_id)
            else:
                logger.debug("Model already registered with LlamaStack", model=self.model)
        except Exception as e:
            logger.warning("Failed to register model with LlamaStack", model=self.model, error=str(e))

        logger.info("LlamaStack provider initialized", model=self.model)

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to LlamaStack and get a response."""
        try:
            # Convert our message format to OpenAI format
            openai_messages = []
            for msg in messages:
                if msg.role == "system":
                    openai_messages.append({"role": "system", "content": msg.content})
                elif msg.role == "user":
                    openai_messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    openai_messages.append({"role": "assistant", "content": msg.content})

            # Call LlamaStack API (OpenAI-compatible)
            response = await self.client.chat.completions.create(model=self.model, messages=openai_messages, **kwargs)

            # Convert response to our format
            choice = response.choices[0]
            message = choice.message

            # Handle both text responses and function calls
            if hasattr(message, "tool_calls") and message.tool_calls and choice.finish_reason == "tool_calls":
                # Pass through function calls for base_agent to handle
                content = ""
                tool_calls = message.tool_calls
            else:
                # Standard text response
                content = message.content or ""
                tool_calls = None

            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None,
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls,
            )
        except Exception as e:
            logger.error("LlamaStack API error", error=str(e))
            raise ProviderError(f"LlamaStack API error: {e}")
