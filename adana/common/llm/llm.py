#!/usr/bin/env python3
"""
Adana LLM Library - Minimal API for LLM Integration

A simple, clean interface for interacting with any LLM provider.
Follows KISS principle with just the essential methods most clients need.
"""

import structlog

from ..config import config_manager
from .providers.factory import create_provider
from .types import LLMMessage, LLMProvider, LLMResponse, ProviderError


logger = structlog.get_logger()

import time

from .debug_logger import get_debug_logger


debug_logger = get_debug_logger()


class LLM:
    """
    Stateless LLM interface - KISS principle applied.

    This LLM class is stateless - it does not maintain conversation history.
    The caller is responsible for managing conversation context.

    Essential methods:
    - chat(messages) - for conversations with full context
    - ask(question, system_prompt) - for single questions
    - stream(messages) - for streaming responses
    - switch_provider() - to change LLM provider

    Usage Examples:

    1. Single Question:
       llm = LLM(provider="openai", model="gpt-4")
       answer = await llm.ask("What is 2+2?")

    2. Conversation with Context:
       llm = LLM(provider="anthropic", model="claude-3-sonnet")
       messages = [
           LLMMessage(role="system", content="You are a helpful assistant"),
           LLMMessage(role="user", content="Hello"),
           LLMMessage(role="assistant", content="Hi there!"),
           LLMMessage(role="user", content="How are you?")
       ]
       response = await llm.chat(messages)

    3. Quick One-off Questions:
       answer = await LLM.ask("Hello", provider="openai", model="gpt-4-turbo")

    4. Check Available Models:
       models = LLM.get_provider_models("openai")
       print(models)  # {'gpt-3.5-turbo': 'gpt-3.5-turbo', 'gpt-4': 'gpt-4', ...}

    Available Models (from config):
    - OpenAI: gpt-3.5-turbo, gpt-4, gpt-4-turbo
    - Anthropic: claude-3-haiku, claude-3-sonnet, claude-3-opus
    - Groq: llama3-8b-8192, llama3-70b-8192, mixtral-8x7b-32768
    - Ollama: llama2, codellama, mistral (and any locally installed models)
    - Moonshot: moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
    - Hugging Face: microsoft/DialoGPT-medium, facebook/blenderbot-400M-distill, google/flan-t5-large
    - Qwen: qwen-turbo, qwen-plus, qwen-max, qwen-long
    - DeepSeek: deepseek-chat, deepseek-coder, deepseek-coder-6.7b, deepseek-coder-33b
    - OpenRouter: Multiple providers (OpenAI, Anthropic, Meta, Mistral, Google, Qwen, DeepSeek, etc.)
    """

    def __init__(self, provider: str | LLMProvider | None = None, model: str | None = None):
        """
        Initialize LLM with a provider.

        Args:
            provider: Provider name ('openai', 'anthropic', 'ollama') or provider instance
            model: Model name to use (defaults to provider's default)
        """
        if isinstance(provider, str):
            # Create provider by name
            self.provider = create_provider(provider, model=model)
            self.provider_name = provider
        elif isinstance(provider, LLMProvider):
            # Use provided instance
            self.provider = provider
            self.provider_name = "custom"
        else:
            # Auto-select first available provider by priority
            first_provider = config_manager.get_first_available_provider()
            if first_provider:
                self.provider = create_provider(first_provider, model=model)
                self.provider_name = first_provider
            else:
                # Fallback to OpenAI if no providers available
                self.provider = create_provider("openai", model=model)
                self.provider_name = "openai"

        self.model = getattr(self.provider, "model", "unknown")

    async def chat(self, messages: list[LLMMessage], **kwargs) -> str:
        """
        Send messages and get a response.

        Args:
            messages: List of LLMMessage objects representing the full conversation context
            **kwargs: Additional parameters for the LLM call

        Returns:
            The response content as a string

        Raises:
            ValueError: If messages list is empty
            ProviderError: If the provider operation fails
        """
        response = await self.chat_response(messages, **kwargs)
        return response.content

    async def chat_response(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """
        Send messages and get a full LLM response with metadata.

        Args:
            messages: List of LLMMessage objects representing the full conversation context
            **kwargs: Additional parameters for the LLM call

        Returns:
            Full LLMResponse object with content, tool_calls, usage, etc.

        Raises:
            ValueError: If messages list is empty
            ProviderError: If the provider operation fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        # Debug logging - log the request
        request_id = debug_logger.log_request(provider=self.provider_name, model=self.model, messages=messages, **kwargs)
        start_time = time.time()

        try:
            # Create agent label for logging if agent info is available
            agent_label = ""
            if "agent_id" in kwargs and "agent_type" in kwargs:
                short_id = kwargs["agent_id"][:8] + "..." if len(kwargs["agent_id"]) > 8 else kwargs["agent_id"]
                agent_label = f" [{kwargs['agent_type']}({short_id})]"

            # Filter out agent parameters before passing to provider
            provider_kwargs = {k: v for k, v in kwargs.items() if k not in ["agent_id", "agent_type"]}

            logger.info("Starting chat", provider=self.provider_name, message_count=len(messages), agent=agent_label)
            response = await self.provider.chat(messages, **provider_kwargs)
            logger.info("Chat completed", provider=self.provider_name, response_length=len(response.content), agent=agent_label)

            # Debug logging - log the response
            duration_ms = (time.time() - start_time) * 1000
            debug_logger.log_response(
                request_id=request_id, response=response, provider=self.provider_name, model=self.model, duration_ms=duration_ms
            )
            # Log full response content for detailed debugging
            if response.content:
                debug_logger.log_full_response_content(
                    request_id=request_id, content=response.content, provider=self.provider_name, model=self.model
                )

            return response
        except Exception as e:
            # Create agent label for error logging if agent info is available
            agent_label = ""
            if "agent_id" in kwargs and "agent_type" in kwargs:
                short_id = kwargs["agent_id"][:8] + "..." if len(kwargs["agent_id"]) > 8 else kwargs["agent_id"]
                agent_label = f" [{kwargs['agent_type']}({short_id})]"

            logger.error("Chat failed", provider=self.provider_name, error=str(e), agent=agent_label)

            # Debug logging - log the error
            debug_logger.log_error(error=e, context="chat_response", request_id=request_id, provider=self.provider_name, model=self.model)

            raise ProviderError(f"Chat failed with {self.provider_name}: {e}") from e

    def chat_response_sync(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """
        Synchronous version of chat_response - runs the async version in a new event loop.

        Args:
            messages: List of LLMMessage objects representing the full conversation context
            **kwargs: Additional parameters for the LLM call

        Returns:
            Full LLMResponse object with content, tool_calls, usage, etc.

        Raises:
            ValueError: If messages list is empty
            ProviderError: If the provider operation fails
        """
        import asyncio

        # Use asyncio.run which handles event loop creation properly
        try:
            # Check if we're already in an async context
            try:
                asyncio.get_running_loop()
                # We're in an async context, but this is a sync method
                # This should not normally happen, but if it does, raise an error
                raise RuntimeError("chat_response_sync() cannot be called from within an async context. Use chat_response() instead.")
            except RuntimeError:
                # No running loop, which is expected for sync method
                pass

            # Create new event loop and run the async method
            return asyncio.run(self.chat_response(messages, **kwargs))
        except Exception:
            # Handle any other asyncio-related errors by using asyncio.run
            return asyncio.run(self.chat_response(messages, **kwargs))

    async def ask(self, question: str, system_prompt: str | None = None, **kwargs) -> str:
        """
        Ask a single question and get an answer.

        Args:
            question: The question to ask
            system_prompt: Optional system prompt to set context
            **kwargs: Additional parameters for the LLM call

        Returns:
            The answer as a string

        Raises:
            ValueError: If question is empty
            ProviderError: If the provider operation fails
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        messages = []

        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))

        messages.append(LLMMessage(role="user", content=question))

        return await self.chat(messages, **kwargs)

    async def stream(self, messages: list[LLMMessage], **kwargs):
        """
        Stream a response from the LLM.

        Args:
            messages: List of LLMMessage objects representing the full conversation context
            **kwargs: Additional parameters for the LLM call

        Yields:
            Chunks of the response as they arrive

        Raises:
            ValueError: If messages list is empty
            ProviderError: If the provider operation fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        try:
            # Create agent label for logging if agent info is available
            agent_label = ""
            if "agent_id" in kwargs and "agent_type" in kwargs:
                short_id = kwargs["agent_id"][:8] + "..." if len(kwargs["agent_id"]) > 8 else kwargs["agent_id"]
                agent_label = f" [{kwargs['agent_type']}({short_id})]"

            # Filter out agent parameters before passing to provider
            provider_kwargs = {k: v for k, v in kwargs.items() if k not in ["agent_id", "agent_type"]}

            logger.info("Starting stream", provider=self.provider_name, message_count=len(messages), agent=agent_label)
            async for chunk in self.provider.stream(messages, **provider_kwargs):
                yield chunk.content
            logger.info("Stream completed", provider=self.provider_name, agent=agent_label)
        except Exception as e:
            # Create agent label for error logging if agent info is available
            agent_label = ""
            if "agent_id" in kwargs and "agent_type" in kwargs:
                short_id = kwargs["agent_id"][:8] + "..." if len(kwargs["agent_id"]) > 8 else kwargs["agent_id"]
                agent_label = f" [{kwargs['agent_type']}({short_id})]"

            logger.error("Stream failed", provider=self.provider_name, error=str(e), agent=agent_label)
            raise ProviderError(f"Stream failed with {self.provider_name}: {e}") from e

    def switch_provider(self, provider: str, model: str | None = None):
        """
        Switch to a different LLM provider.

        Args:
            provider: Provider name ('openai', 'anthropic', 'ollama', etc.)
            model: Model to use (defaults to provider's default)
        """
        self.provider = create_provider(provider, model=model)
        self.provider_name = provider
        self.model = getattr(self.provider, "model", "unknown")
        logger.info("Switched LLM provider", provider=provider, model=self.model)

    @staticmethod
    async def ask_question(question: str, provider: str | None = None, model: str | None = None, **kwargs) -> str:
        """
        Quick static method to ask a single question.

        Args:
            question: The question to ask
            provider: Provider to use (defaults to first available by priority)
            model: Model to use (defaults to provider's default)
            **kwargs: Additional parameters

        Returns:
            The answer as a string
        """
        llm = LLM(provider=provider, model=model)
        return await llm.ask(question, **kwargs)

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available providers."""
        return config_manager.get_available_providers()

    @staticmethod
    def is_provider_available(provider: str) -> bool:
        """Check if a provider is available."""
        return config_manager.is_provider_available(provider)

    @staticmethod
    def get_provider_models(provider: str) -> dict[str, str]:
        """Get available models for a provider."""
        return config_manager.get_provider_models(provider)

    @staticmethod
    def show_config_documentation():
        """Display configuration information from adana/config.json."""
        import json
        from pathlib import Path

        # Load the config file
        config_path = Path(__file__).parent.parent.parent / "config.json"

        try:
            with open(config_path) as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return

        print("📚 Adana LLM Configuration")
        print("=" * 50)

        # Required environment variables (from config)
        print("\n🔑 Required Environment Variables:")
        print("-" * 30)
        providers = config.get("llm", {}).get("providers", {})
        for provider, info in providers.items():
            api_key_env = info.get("api_key_env")
            if api_key_env:
                name = info.get("name", provider)
                print(f"  {api_key_env:<25} - {name} API key")

        # Optional environment variables (from config)
        print("\n⚙️  Optional Environment Variables:")
        print("-" * 30)
        for provider, info in providers.items():
            base_url_env = info.get("base_url_env")
            if base_url_env:
                name = info.get("name", provider)
                print(f"  {base_url_env:<25} - Override {name} endpoint")

            api_version_env = info.get("api_version_env")
            if api_version_env:
                name = info.get("name", provider)
                print(f"  {api_version_env:<25} - Override {name} API version")

        # Show available providers
        print("\n🤖 Available Providers:")
        print("-" * 30)
        for provider, info in providers.items():
            name = info.get("name", provider)
            priority = info.get("priority", 0)
            api_key_env = info.get("api_key_env")
            if api_key_env:
                print(f"  {provider:<12} - {name} (priority: {priority}, requires {api_key_env})")
            else:
                print(f"  {provider:<12} - {name} (priority: {priority}, no API key required)")

        print("\n💡 Example .env file:")
        print("-" * 30)
        print("# Required API Keys")
        for _provider, info in providers.items():
            api_key_env = info.get("api_key_env")
            if api_key_env:
                print(f"# {api_key_env}=your-{api_key_env.lower().replace('_', '-')}-here")

        print("\n# Optional: Custom endpoints and settings")
        for _provider, info in providers.items():
            base_url_env = info.get("base_url_env")
            if base_url_env:
                print(f"# {base_url_env}=your-custom-endpoint")

            api_version_env = info.get("api_version_env")
            if api_version_env:
                print(f"# {api_version_env}=your-api-version")

        print("\n🎯 Quick Start:")
        print("-" * 30)
        print("1. Set at least one API key from the required list above")
        print("2. For Azure: Update the base_url in adana/config.json")
        print("3. For Ollama: Set OLLAMA_API_KEY='ollama' to enable local Ollama")
        print("4. Run: python examples/llm_example.py")
