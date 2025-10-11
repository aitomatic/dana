"""
Live tests for all LLM providers

These tests make real API calls to verify provider functionality.
Run with: pytest adana/common/llm/tests/test_providers_live.py -v -m live
"""

import asyncio

import pytest

from adana.common.config import config_manager
from adana.common.llm.llm import LLM


class TestProviderLive:
    """Live tests for all LLM providers."""

    @pytest.mark.live
    @pytest.mark.slow
    def test_all_providers_available(self):
        """Test that all configured providers are available."""
        available_providers = config_manager.get_available_providers()
        expected_providers = ["openai", "anthropic", "groq", "deepseek", "openrouter", "moonshot", "huggingface", "qwen", "azure", "ollama"]

        for provider in expected_providers:
            assert provider in available_providers, f"Provider {provider} not found in available providers"

    @pytest.mark.live
    @pytest.mark.slow
    def test_provider_priorities(self):
        """Test that provider priorities are correctly configured."""
        providers_by_priority = config_manager.get_available_providers_by_priority()

        # Check that we have providers with priorities
        assert len(providers_by_priority) > 0, "No providers found with priorities"

        # Check that priorities are sorted correctly (highest first)
        priorities = [priority for _, priority in providers_by_priority]
        assert priorities == sorted(priorities, reverse=True), "Providers not sorted by priority correctly"

    @pytest.mark.live
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "provider_name", ["openai", "anthropic", "groq", "deepseek", "openrouter", "moonshot", "huggingface", "qwen", "azure", "ollama"]
    )
    def test_provider_creation(self, provider_name):
        """Test that each provider can be created without errors."""
        try:
            llm = LLM(provider=provider_name)
            assert llm.provider_name == provider_name
            assert llm.model is not None
            print(f"✅ {provider_name}: Created successfully with model {llm.model}")
        except Exception as e:
            # Some providers might not have API keys, that's expected
            if "API key" in str(e) or "not found" in str(e).lower():
                print(f"⚠️  {provider_name}: Skipped - {str(e)}")
                pytest.skip(f"Provider {provider_name} not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "provider_name", ["openai", "anthropic", "groq", "deepseek", "openrouter", "moonshot", "huggingface", "qwen", "azure", "ollama"]
    )
    def test_provider_chat(self, provider_name):
        """Test that each provider can handle chat requests."""
        try:
            llm = LLM(provider=provider_name)

            # Test with a simple message
            response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))

            assert response is not None
            assert len(response) > 0
            print(f"✅ {provider_name}: Chat successful - {response[:50]}...")

        except Exception as e:
            # Some providers might not have API keys, that's expected
            if "API key" in str(e) or "not found" in str(e).lower():
                print(f"⚠️  {provider_name}: Skipped - {str(e)}")
                pytest.skip(f"Provider {provider_name} not available: {str(e)}")
            else:
                print(f"❌ {provider_name}: Chat failed - {str(e)}")
                raise

    @pytest.mark.live
    @pytest.mark.slow
    def test_auto_provider_selection(self):
        """Test that the LLM automatically selects the best available provider."""
        try:
            llm = LLM()  # No provider specified, should auto-select
            assert llm.provider_name is not None
            assert llm.model is not None

            # Test that it can actually work
            response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
            assert response is not None
            assert len(response) > 0

            print(f"✅ Auto-selection: Selected {llm.provider_name} with model {llm.model}")
            print(f"   Response: {response[:50]}...")

        except Exception as e:
            if "API key" in str(e) or "not found" in str(e).lower():
                print(f"⚠️  Auto-selection: No providers available - {str(e)}")
                pytest.skip(f"No providers available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.slow
    def test_static_ask_question(self):
        """Test the static ask_question method."""
        try:
            response = asyncio.run(LLM.ask_question("Hello! Please respond with just 'Hi there!'"))
            assert response is not None
            assert len(response) > 0
            print(f"✅ Static ask_question: {response[:50]}...")

        except Exception as e:
            if "API key" in str(e) or "not found" in str(e).lower():
                print(f"⚠️  Static ask_question: No providers available - {str(e)}")
                pytest.skip(f"No providers available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.slow
    def test_stateless_conversation(self):
        """Test stateless conversation functionality with explicit context."""
        try:
            from adana.common.llm.types import LLMMessage

            llm = LLM()

            # Test conversation with explicit context management
            messages1 = [LLMMessage(role="user", content="Hello! My name is TestUser.")]
            response1 = asyncio.run(llm.chat(messages1))
            assert response1 is not None

            # Test follow-up with full context
            messages2 = [
                LLMMessage(role="user", content="Hello! My name is TestUser."),
                LLMMessage(role="assistant", content=response1),
                LLMMessage(role="user", content="What's my name?"),
            ]
            response2 = asyncio.run(llm.chat(messages2))
            assert response2 is not None

            print("✅ Stateless conversation: Context managed externally")
            print(f"   First response: {response1[:50]}...")
            print(f"   Second response: {response2[:50]}...")

        except Exception as e:
            if "API key" in str(e) or "not found" in str(e).lower():
                print(f"⚠️  Stateless conversation: No providers available - {str(e)}")
                pytest.skip(f"No providers available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.slow
    def test_system_prompt(self):
        """Test system prompt functionality with stateless approach."""
        try:
            llm = LLM()

            # Test system prompt using the ask method
            system_prompt = "You are a helpful assistant that always responds with 'System prompt works!'"
            response = asyncio.run(llm.ask("Hello!", system_prompt=system_prompt))
            assert response is not None

            print(f"✅ System prompt: {response[:50]}...")

        except Exception as e:
            if "API key" in str(e) or "not found" in str(e).lower():
                print(f"⚠️  System prompt: No providers available - {str(e)}")
                pytest.skip(f"No providers available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.slow
    def test_provider_switching(self):
        """Test switching between providers."""
        try:
            # Start with one provider
            llm = LLM()
            original_provider = llm.provider_name

            # Test switching (if another provider is available)
            available_providers = config_manager.get_available_providers()
            other_providers = [p for p in available_providers if p != original_provider]

            if other_providers:
                llm.switch_provider(other_providers[0])
                assert llm.provider_name == other_providers[0]
                print(f"✅ Provider switching: {original_provider} -> {other_providers[0]}")
            else:
                print(f"⚠️  Provider switching: Only {original_provider} available, skipping switch test")
                pytest.skip("Only one provider available")

        except Exception as e:
            if "API key" in str(e) or "not found" in str(e).lower():
                print(f"⚠️  Provider switching: No providers available - {str(e)}")
                pytest.skip(f"No providers available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.slow
    def test_model_override(self):
        """Test model override functionality."""
        try:
            # Test with specific model
            llm = LLM(model="openai/gpt-oss-20b")  # Use a common model
            assert llm.model is not None

            response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
            assert response is not None

            print(f"✅ Model override: Using model {llm.model}")
            print(f"   Response: {response[:50]}...")

        except Exception as e:
            if "API key" in str(e) or "not found" in str(e).lower():
                print(f"⚠️  Model override: No providers available - {str(e)}")
                pytest.skip(f"No providers available: {str(e)}")
            else:
                raise
