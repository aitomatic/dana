"""
Live tests for Groq provider
"""

import asyncio

import pytest

from dana_agent.common.llm.llm import LLM


class TestGroqLive:
    """Live tests for Groq provider."""

    @pytest.mark.live
    @pytest.mark.provider("groq")
    def test_groq_basic_chat(self):
        """Test basic Groq chat functionality."""
        try:
            llm = LLM(provider="groq")
            response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
            assert response is not None
            assert len(response) > 0
            print(f"✅ Groq basic chat: {response[:50]}...")
        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"Groq API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.provider("groq")
    def test_groq_models(self):
        """Test different Groq models."""
        models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "gemma2-9b-it"]

        for model in models:
            try:
                llm = LLM(provider="groq", model=model)
                response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
                assert response is not None
                print(f"✅ Groq {model}: {response[:30]}...")
            except Exception as e:
                if "API key" in str(e):
                    pytest.skip(f"Groq API key not available: {str(e)}")
                elif "not available" in str(e).lower():
                    print(f"⚠️  Groq {model}: Model not available - {str(e)}")
                    continue
                else:
                    raise

    @pytest.mark.live
    @pytest.mark.provider("groq")
    def test_groq_conversation(self):
        """Test Groq conversation with stateless approach."""
        try:
            from dana_agent.common.llm.types import LLMMessage

            llm = LLM(provider="groq")

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

            print("✅ Groq conversation: Stateless approach working")
            print(f"   First response: {response1[:50]}...")
            print(f"   Second response: {response2[:50]}...")
        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"Groq API key not available: {str(e)}")
            else:
                raise
