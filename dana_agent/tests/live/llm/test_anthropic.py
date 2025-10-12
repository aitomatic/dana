"""
Live tests for Anthropic provider
"""

import asyncio

import pytest

from dana.common.llm.llm import LLM


class TestAnthropicLive:
    """Live tests for Anthropic provider."""

    @pytest.mark.live
    @pytest.mark.provider("anthropic")
    def test_anthropic_basic_chat(self):
        """Test basic Anthropic chat functionality."""
        try:
            llm = LLM(provider="anthropic")
            response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
            assert response is not None
            assert len(response) > 0
            print(f"✅ Anthropic basic chat: {response[:50]}...")
        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"Anthropic API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.provider("anthropic")
    def test_anthropic_models(self):
        """Test different Anthropic models."""
        models = ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"]

        for model in models:
            try:
                llm = LLM(provider="anthropic", model=model)
                response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
                assert response is not None
                print(f"✅ Anthropic {model}: {response[:30]}...")
            except Exception as e:
                if "API key" in str(e):
                    pytest.skip(f"Anthropic API key not available: {str(e)}")
                elif "not available" in str(e).lower():
                    print(f"⚠️  Anthropic {model}: Model not available - {str(e)}")
                    continue
                else:
                    raise

    @pytest.mark.live
    @pytest.mark.provider("anthropic")
    def test_anthropic_system_prompt(self):
        """Test Anthropic with system prompt."""
        try:
            llm = LLM(provider="anthropic")
            system_prompt = "You are a helpful assistant that always responds with 'System prompt works!'"

            response = asyncio.run(llm.ask("Hello!", system_prompt=system_prompt))
            assert response is not None

            print(f"✅ Anthropic system prompt: {response[:50]}...")
        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"Anthropic API key not available: {str(e)}")
            else:
                raise
