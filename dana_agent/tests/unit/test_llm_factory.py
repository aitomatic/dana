"""
Unit tests for LLM provider factory
"""

from unittest.mock import Mock, patch

import pytest

from dana.common.llm.providers.factory import create_provider
from dana.common.llm.types import ConfigurationError


class TestCreateProvider:
    """Unit tests for the create_provider function"""

    def test_create_openai_provider(self):
        """Test creating OpenAI provider"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {"api_key_env": "OPENAI_API_KEY", "default_model": "gpt-3.5-turbo"}

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("openai", model="gpt-4")

                mock_openai.assert_called_once_with(model="gpt-4")
                assert provider == mock_provider

    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {"api_key_env": "ANTHROPIC_API_KEY", "default_model": "claude-3-sonnet"}

            with patch("dana.common.llm.providers.anthropic.AnthropicProvider") as mock_anthropic:
                mock_provider = Mock()
                mock_anthropic.return_value = mock_provider

                provider = create_provider("anthropic", model="claude-3-opus")

                mock_anthropic.assert_called_once_with(model="claude-3-opus")
                assert provider == mock_provider

    def test_create_ollama_provider(self):
        """Test creating Ollama provider via OpenAI-compatible fallback"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {
                "api_key_env": "OLLAMA_API_KEY",
                "default_model": "llama2",
                "base_url": "http://localhost:11434/v1",
            }
            mock_config.get_provider_api_key.return_value = "ollama-key"

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("ollama", model="llama2:7b")

                mock_openai.assert_called_once_with(api_key="ollama-key", model="llama2:7b", base_url="http://localhost:11434/v1")
                assert provider == mock_provider

    def test_create_azure_provider(self):
        """Test creating Azure provider"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {"api_key_env": "AZURE_API_KEY", "default_model": "gpt-35-turbo"}

            with patch("dana.common.llm.providers.azure.AzureProvider") as mock_azure:
                mock_provider = Mock()
                mock_azure.return_value = mock_provider

                provider = create_provider("azure", model="gpt-4")

                mock_azure.assert_called_once_with(model="gpt-4")
                assert provider == mock_provider

    def test_create_groq_provider(self):
        """Test creating Groq provider via OpenAI-compatible fallback"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {
                "api_key_env": "GROQ_API_KEY",
                "default_model": "llama3-8b-8192",
                "base_url": "https://api.groq.com/openai/v1",
            }
            mock_config.get_provider_api_key.return_value = "groq-key"

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("groq", model="llama3-70b-8192")

                mock_openai.assert_called_once_with(api_key="groq-key", model="llama3-70b-8192", base_url="https://api.groq.com/openai/v1")
                assert provider == mock_provider

    def test_create_moonshot_provider(self):
        """Test creating Moonshot provider via OpenAI-compatible fallback"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {
                "api_key_env": "MOONSHOT_API_KEY",
                "default_model": "moonshot-v1-8k",
                "base_url": "https://api.moonshot.cn/v1",
            }
            mock_config.get_provider_api_key.return_value = "moonshot-key"

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("moonshot", model="moonshot-v1-32k")

                mock_openai.assert_called_once_with(api_key="moonshot-key", model="moonshot-v1-32k", base_url="https://api.moonshot.cn/v1")
                assert provider == mock_provider

    def test_create_huggingface_provider(self):
        """Test creating HuggingFace provider via OpenAI-compatible fallback"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {
                "api_key_env": "HUGGINGFACE_API_KEY",
                "default_model": "microsoft/DialoGPT-medium",
                "base_url": "https://api-inference.huggingface.co/v1",
            }
            mock_config.get_provider_api_key.return_value = "hf-key"

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("huggingface", model="microsoft/DialoGPT-large")

                mock_openai.assert_called_once_with(
                    api_key="hf-key", model="microsoft/DialoGPT-large", base_url="https://api-inference.huggingface.co/v1"
                )
                assert provider == mock_provider

    def test_create_qwen_provider(self):
        """Test creating Qwen provider via OpenAI-compatible fallback"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {
                "api_key_env": "QWEN_API_KEY",
                "default_model": "qwen-turbo",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            }
            mock_config.get_provider_api_key.return_value = "qwen-key"

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("qwen", model="qwen-plus")

                mock_openai.assert_called_once_with(
                    api_key="qwen-key", model="qwen-plus", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                assert provider == mock_provider

    def test_create_deepseek_provider(self):
        """Test creating DeepSeek provider via OpenAI-compatible fallback"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {
                "api_key_env": "DEEPSEEK_API_KEY",
                "default_model": "deepseek-chat",
                "base_url": "https://api.deepseek.com/v1",
            }
            mock_config.get_provider_api_key.return_value = "deepseek-key"

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("deepseek", model="deepseek-coder")

                mock_openai.assert_called_once_with(api_key="deepseek-key", model="deepseek-coder", base_url="https://api.deepseek.com/v1")
                assert provider == mock_provider

    def test_create_openrouter_provider(self):
        """Test creating OpenRouter provider via OpenAI-compatible fallback"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {
                "api_key_env": "OPENROUTER_API_KEY",
                "default_model": "openai/gpt-3.5-turbo",
                "base_url": "https://openrouter.ai/api/v1",
            }
            mock_config.get_provider_api_key.return_value = "openrouter-key"

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("openrouter", model="anthropic/claude-3-sonnet")

                mock_openai.assert_called_once_with(
                    api_key="openrouter-key", model="anthropic/claude-3-sonnet", base_url="https://openrouter.ai/api/v1"
                )
                assert provider == mock_provider

    def test_create_provider_with_env_model(self):
        """Test creating provider with model from environment variable"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {"api_key_env": "OPENAI_API_KEY", "default_model": "gpt-3.5-turbo"}

            with patch("os.getenv") as mock_getenv:
                mock_getenv.return_value = "gpt-4-turbo"

                with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                    mock_provider = Mock()
                    mock_openai.return_value = mock_provider

                    _provider = create_provider("openai")

                    mock_openai.assert_called_once_with(model="gpt-4-turbo")

    def test_create_provider_with_default_model(self):
        """Test creating provider with default model from config"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {"api_key_env": "OPENAI_API_KEY", "default_model": "gpt-3.5-turbo"}

            with patch("os.getenv") as mock_getenv:
                mock_getenv.return_value = None

                with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                    mock_provider = Mock()
                    mock_openai.return_value = mock_provider

                    _provider = create_provider("openai")

                    mock_openai.assert_called_once_with(model="gpt-3.5-turbo")

    def test_create_provider_fallback_model(self):
        """Test creating provider with fallback model when no default is set"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {"api_key_env": "OPENAI_API_KEY"}

            with patch("os.getenv") as mock_getenv:
                mock_getenv.return_value = None

                with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                    mock_provider = Mock()
                    mock_openai.return_value = mock_provider

                    _provider = create_provider("openai")

                    mock_openai.assert_called_once_with(model="gpt-3.5-turbo")

    def test_create_provider_not_found(self):
        """Test creating provider that doesn't exist"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = None
            mock_config.get_available_providers.return_value = ["openai", "anthropic"]

            with pytest.raises(ValueError, match="Provider 'unknown' not found"):
                create_provider("unknown")

    def test_create_openai_compatible_provider(self):
        """Test creating OpenAI-compatible provider for unknown providers"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {"api_key_env": "CUSTOM_API_KEY", "base_url": "https://api.custom.com/v1"}
            mock_config.get_provider_api_key.return_value = "custom-key"

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("custom", model="custom-model")

                mock_openai.assert_called_once_with(api_key="custom-key", model="custom-model", base_url="https://api.custom.com/v1")
                assert provider == mock_provider

    def test_create_openai_compatible_provider_missing_api_key(self):
        """Test creating OpenAI-compatible provider with missing API key"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {"api_key_env": "CUSTOM_API_KEY", "base_url": "https://api.custom.com/v1"}
            mock_config.get_provider_api_key.return_value = None

            with pytest.raises(ConfigurationError, match="API key not found for custom"):
                create_provider("custom")

    def test_create_provider_with_kwargs(self):
        """Test creating provider with additional kwargs"""
        with patch("dana.common.llm.providers.factory.config_manager") as mock_config:
            mock_config.get_provider_config.return_value = {"api_key_env": "OPENAI_API_KEY", "default_model": "gpt-3.5-turbo"}

            with patch("dana.common.llm.providers.factory.OpenAIProvider") as mock_openai:
                mock_provider = Mock()
                mock_openai.return_value = mock_provider

                provider = create_provider("openai", model="gpt-4", temperature=0.7, max_tokens=100)

                mock_openai.assert_called_once_with(model="gpt-4", temperature=0.7, max_tokens=100)
                assert provider == mock_provider
