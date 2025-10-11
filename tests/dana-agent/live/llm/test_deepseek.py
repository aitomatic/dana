"""
Live tests for DeepSeek provider
"""

import asyncio

import pytest

from dana_agent.common.llm.llm import LLM


class TestDeepSeekLive:
    """Live tests for DeepSeek provider."""

    @pytest.mark.live
    @pytest.mark.provider("deepseek")
    def test_deepseek_basic_chat(self):
        """Test basic DeepSeek chat functionality."""
        try:
            llm = LLM(provider="deepseek")
            response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
            assert response is not None
            assert len(response) > 0
            print(f"✅ DeepSeek basic chat: {response[:50]}...")
        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"DeepSeek API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.provider("deepseek")
    def test_deepseek_models(self):
        """Test different DeepSeek models."""
        models = ["deepseek-chat", "deepseek-reasoner"]

        for model in models:
            try:
                llm = LLM(provider="deepseek", model=model)
                response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
                assert response is not None
                print(f"✅ DeepSeek {model}: {response[:30]}...")
            except Exception as e:
                if "API key" in str(e):
                    pytest.skip(f"DeepSeek API key not available: {str(e)}")
                elif "not available" in str(e).lower():
                    print(f"⚠️  DeepSeek {model}: Model not available - {str(e)}")
                    continue
                else:
                    raise

    @pytest.mark.live
    @pytest.mark.provider("deepseek")
    def test_deepseek_coding_task(self):
        """Test DeepSeek with a coding task."""
        try:
            llm = LLM(provider="deepseek", model="deepseek-chat")
            response = asyncio.run(llm.ask("Write a simple Python function that adds two numbers."))
            assert response is not None
            assert len(response) > 0
            print(f"✅ DeepSeek coding task: {response[:50]}...")
        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"DeepSeek API key not available: {str(e)}")
            else:
                raise
