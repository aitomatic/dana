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

    Supports any model from any provider configured on the LlamaStack server.

    API keys for external providers are managed server-side.
    """

    def __init__(self, base_url: str | None = None, model: str | None = None, **kwargs):
        """
        Initialize LlamaStack provider. API keys are managed LS-side.

        Args:
            base_url: LlamaStack server URL (defaults to LLAMA_STACK_URL env var or localhost:8321)
            model: Model identifier in format "provider/model-name". If None, automatically selects
                   the first available LLM model from LlamaStack.
            **kwargs: Additional arguments
        """
        try:
            self.client = LlamaStackClientManager.get_client()
        except Exception as e:
            raise ProviderError(f"Failed to initialize LlamaStack client: {e}")

        # Get available models from LlamaStack
        available_llm_models = self._get_available_llm_models()

        if model is None:
            # No model specified - pick first available LLM model
            if not available_llm_models:
                raise ProviderError(
                    "No model specified and no LLM models available in LlamaStack. "
                    "Please specify a model or ensure LlamaStack has at least one LLM model registered."
                )
            first_model = available_llm_models[0]
            model_id = getattr(first_model, "identifier", None) or getattr(first_model, "id", None) or getattr(first_model, "name", None)
            if not model_id:
                raise ProviderError("Available model found but has no identifier")
            self.model = model_id
            logger.info("Auto-selected first available LLM model from LlamaStack", model=self.model)
        else:
            # Model specified - verify it's available or try to register it
            model_identifiers = []
            for m in available_llm_models:
                model_id = getattr(m, "identifier", None) or getattr(m, "id", None) or getattr(m, "name", None)
                if model_id:
                    model_identifiers.append(model_id)

            if model not in model_identifiers:
                # Try to register the model
                if "/" in model:
                    provider_id, provider_model_id = model.split("/", 1)
                else:
                    provider_id = None
                    provider_model_id = model

                model_type: Literal["llm", "embedding"] = "llm"

                try:
                    if provider_id:
                        self.client.models.register(
                            model_id=model,
                            model_type=model_type,
                            provider_model_id=provider_model_id,
                            provider_id=provider_id,
                        )
                    else:
                        # Don't pass provider_id if None (it defaults to omit)
                        self.client.models.register(
                            model_id=model,
                            model_type=model_type,
                            provider_model_id=provider_model_id,
                        )
                    logger.info("Registered model with LlamaStack", model=model, provider_id=provider_id)

                    # Verify the model is now available
                    updated_models = self._get_available_llm_models()
                    updated_identifiers = []
                    for m in updated_models:
                        model_id = getattr(m, "identifier", None) or getattr(m, "id", None) or getattr(m, "name", None)
                        if model_id:
                            updated_identifiers.append(model_id)
                    if model not in updated_identifiers:
                        raise ProviderError(
                            f"Model '{model}' was registered but is not available in LlamaStack. "
                            "Please verify the model identifier and provider configuration."
                        )
                except Exception as register_error:
                    error_str = str(register_error)
                    # If model already exists, that's fine - it's already registered
                    if "already exists" in error_str.lower():
                        logger.debug("Model already registered with LlamaStack", model=model)
                        # Re-check availability after registration attempt
                        updated_models = self._get_available_llm_models()
                        updated_identifiers = []
                        for m in updated_models:
                            model_id = getattr(m, "identifier", None) or getattr(m, "id", None) or getattr(m, "name", None)
                            if model_id:
                                updated_identifiers.append(model_id)
                        if model not in updated_identifiers:
                            raise ProviderError(
                                f"Model '{model}' was marked as existing but is not available in LlamaStack. "
                                "Please verify the model identifier and provider configuration."
                            )
                    else:
                        # Registration failed - raise error
                        raise ProviderError(f"Failed to register model '{model}' with LlamaStack: {error_str}")

            self.model = model
            logger.debug("Using specified model", model=self.model)

        logger.info("LlamaStack provider initialized", model=self.model)

    def _get_available_llm_models(self) -> list:
        """
        Get available LLM models from LlamaStack.

        Returns:
            List of model objects that are LLM type (not embeddings)
        """
        try:
            registered_models = self.client.models.list()
            # Handle both list response and object with .data attribute
            if isinstance(registered_models, list):
                models_list = registered_models
            elif hasattr(registered_models, "data") and registered_models.data is not None:
                models_list = registered_models.data
            else:
                models_list = []

            # Filter for LLM type models (not embeddings)
            llm_models = []
            for model in models_list:
                # Check if it's an LLM (not embedding) model
                model_type = getattr(model, "model_type", None)
                model_id = getattr(model, "identifier", None)

                # If identifier is None, try other possible attributes
                if model_id is None:
                    model_id = getattr(model, "id", None) or getattr(model, "name", None)

                # Include models that are LLM type (or None, which we assume is LLM)
                if (model_type is None or model_type == "llm") and model_id:
                    llm_models.append(model)

            return llm_models
        except Exception as e:
            logger.error("Failed to list models from LlamaStack", error=str(e))
            raise ProviderError(f"Failed to list models from LlamaStack: {e}")

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
            response = self.client.chat.completions.create(model=self.model, messages=openai_messages, **kwargs)

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

    async def stream(self, messages: list[LLMMessage], **kwargs):
        """Stream a response from LlamaStack."""
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

            # Enable streaming
            kwargs["stream"] = True

            # Call LlamaStack API with streaming
            stream = self.client.chat.completions.create(model=self.model, messages=openai_messages, **kwargs)

            # Yield chunks
            async for chunk in stream:
                if hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        # Create a simple response-like object for the chunk
                        from ..types import LLMResponse

                        yield LLMResponse(
                            content=delta.content,
                            model=getattr(chunk, "model", self.model),
                            usage=None,
                            finish_reason=None,
                            tool_calls=None,
                        )
        except Exception as e:
            logger.error("LlamaStack streaming error", error=str(e))
            raise ProviderError(f"LlamaStack streaming error: {e}")
