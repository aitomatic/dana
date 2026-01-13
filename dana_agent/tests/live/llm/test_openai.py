"""
Live tests for OpenAI provider
"""

import asyncio

import pytest

from dana.common.llm.llm import LLM


class TestOpenAILive:
    """Live tests for OpenAI provider."""

    @pytest.mark.live
    @pytest.mark.provider("openai")
    def test_openai_basic_chat(self):
        """Test basic OpenAI chat functionality."""
        try:
            llm = LLM(provider="openai")
            response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
            assert response is not None
            assert len(response) > 0
            print(f"✅ OpenAI basic chat: {response[:50]}...")
        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"OpenAI API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.provider("openai")
    def test_openai_models(self):
        """Test different OpenAI models."""
        models = ["gpt-3.5-turbo", "gpt-4"]

        for model in models:
            try:
                llm = LLM(provider="openai", model=model)
                response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
                assert response is not None
                print(f"✅ OpenAI {model}: {response[:30]}...")
            except Exception as e:
                if "API key" in str(e):
                    pytest.skip(f"OpenAI API key not available: {str(e)}")
                elif "not available" in str(e).lower():
                    print(f"⚠️  OpenAI {model}: Model not available - {str(e)}")
                    continue
                else:
                    raise

    @pytest.mark.live
    @pytest.mark.provider("openai")
    def test_openai_conversation(self):
        """Test OpenAI conversation with stateless approach."""
        try:
            from dana.common.llm.types import LLMMessage

            llm = LLM(provider="openai")

            # First message
            messages1 = [LLMMessage(role="user", content="My name is TestUser.")]
            response1 = asyncio.run(llm.chat(messages1))
            assert response1 is not None

            # Second message with full context
            messages2 = [
                LLMMessage(role="user", content="My name is TestUser."),
                LLMMessage(role="assistant", content=response1),
                LLMMessage(role="user", content="What's my name?"),
            ]
            response2 = asyncio.run(llm.chat(messages2))
            assert response2 is not None

            print("✅ OpenAI conversation: Stateless approach working")
            print(f"   First response: {response1[:50]}...")
            print(f"   Second response: {response2[:50]}...")
        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"OpenAI API key not available: {str(e)}")
            else:
                raise
