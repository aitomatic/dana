"""
Live tests for LlamaStack provider

⚠️  PREREQUISITE: LlamaStack server must be running before running these tests.

1. Start the Ollama server: source ./bin/ollama/start.sh
2. Start the LlamaStack server: OLLAMA_URL=${LOCAL_LLM_URL} uv run --with llama-stack llama stack run starter
"""

import asyncio

import pytest

from dana.common.llamastack.client import LlamaStackClientManager
from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage


def get_available_llm_models():
    """
    Get available LLM models from LlamaStack.

    Returns:
        List of model identifiers (strings) that are LLM type (not embeddings)
    """
    try:
        client = LlamaStackClientManager.get_client()
        registered_models = client.models.list()

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
            # The model_type might be on the model object or we default to assuming it's LLM
            model_type = getattr(model, "model_type", None)
            model_id = getattr(model, "identifier", None)

            # If identifier is None, try other possible attributes
            if model_id is None:
                # Try 'id' or 'name' as fallback
                model_id = getattr(model, "id", None) or getattr(model, "name", None)

            if model_type is None or model_type == "llm":
                if model_id:
                    llm_models.append(model_id)
        print(f"✅ Found {len(llm_models)} LLM models: {llm_models}")
        return llm_models
    except Exception as e:
        # Log the error but don't raise - let tests handle it
        print(f"⚠️  Could not list models from LlamaStack: {e}")
        return []


def get_test_model():
    """
    Get a model to use for testing.
    Prefers models with 'llama' in the name, otherwise returns first available.

    Returns:
        Model identifier string or None if no models available
    """
    models = get_available_llm_models()
    if not models:
        return None

    # Prefer llama models, but use any available model
    for model in models:
        if "llama" in model.lower():
            return model
        print(f"🔍 Model: {model}")

    # Return first available model
    print(f"🔍 Returning first available model: {models[0]}")
    return models[0]


class TestLlamaStackLive:
    """Live tests for LlamaStack provider."""

    @pytest.fixture(scope="class")
    def test_model(self):
        """Get a test model that's available in LlamaStack."""
        model = get_test_model()
        if not model:
            # Try to use default model from config as fallback
            try:
                from dana.common.config import config_manager

                config = config_manager.get_provider_config("llamastack")
                if config:
                    default_model = config.get("default_model")
                    if default_model:
                        print(f"⚠️  No models listed, using default from config: {default_model}")
                        return default_model
            except Exception as e:
                print(f"⚠️  Could not get default model from config: {e}")
            pytest.skip("No LLM models available in LlamaStack")
        return model

    @pytest.mark.live
    @pytest.mark.provider("llamastack")
    def test_llamastack_basic_chat(self, test_model):
        """Test basic LlamaStack chat functionality."""
        try:
            llm = LLM(provider="llamastack", model=test_model)
            response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
            assert response is not None
            assert len(response) > 0
            print(f"✅ LlamaStack basic chat ({test_model}): {response[:50]}...")
        except Exception as e:
            if "Connection" in str(e) or "API key" in str(e):
                pytest.skip(f"LlamaStack server not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.provider("llamastack")
    def test_llamastack_models(self):
        """Test different models through LlamaStack."""
        models = get_available_llm_models()
        if not models:
            pytest.skip("No LLM models available in LlamaStack")

        tested_count = 0
        for model in models[:5]:  # Test up to 5 models
            try:
                llm = LLM(provider="llamastack", model=model)
                response = asyncio.run(llm.ask("Hello! Please respond with just 'Hi there!'"))
                assert response is not None
                print(f"✅ LlamaStack {model}: {response[:30]}...")
                tested_count += 1
            except Exception as e:
                error_str = str(e).lower()
                if "connection" in error_str:
                    pytest.skip(f"LlamaStack server not available: {str(e)}")
                elif "not found" in error_str or "not available" in error_str:
                    print(f"⚠️  LlamaStack {model}: Model not available - {str(e)}")
                    continue
                elif "not implemented" in error_str or "not supported" in error_str:
                    # Some providers don't support OpenAI chat completion API
                    print(f"⚠️  LlamaStack {model}: API not supported by provider - {str(e)}")
                    continue
                else:
                    raise

        if tested_count == 0:
            pytest.skip("No models were successfully tested")

    @pytest.mark.live
    @pytest.mark.provider("llamastack")
    def test_llamastack_conversation(self, test_model):
        """Test LlamaStack conversation with stateless approach."""
        try:
            llm = LLM(provider="llamastack", model=test_model)

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

            print(f"✅ LlamaStack conversation ({test_model}): Stateless approach working")
            print(f"   First response: {response1[:50]}...")
            print(f"   Second response: {response2[:50]}...")
        except Exception as e:
            if "Connection" in str(e) or "API key" in str(e):
                pytest.skip(f"LlamaStack server not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    @pytest.mark.provider("llamastack")
    def test_llamastack_full_response(self, test_model):
        """Test LlamaStack chat_response for full metadata."""
        try:
            llm = LLM(provider="llamastack", model=test_model)
            messages = [LLMMessage(role="system", content="You are a helpful assistant."), LLMMessage(role="user", content="What is 2+2?")]
            response_obj = asyncio.run(llm.chat_response(messages))
            assert response_obj is not None
            assert response_obj.content is not None
            assert response_obj.model is not None
            print(f"✅ LlamaStack full response ({test_model}): model={response_obj.model}, content={response_obj.content[:50]}...")
            if response_obj.usage:
                print(f"   Token usage: {response_obj.usage}")
        except Exception as e:
            if "Connection" in str(e) or "API key" in str(e):
                pytest.skip(f"LlamaStack server not available: {str(e)}")
            else:
                raise
