"""Tests for Azure provider streaming inheritance."""

from unittest.mock import patch, MagicMock

from dana.common.llm.providers.openai_compatible_base import OpenAICompatibleProvider


class TestAzureStreamInheritsBase:
    """Verify AzureProvider inherits streaming from base."""

    def _make_provider(self, use_responses_api=None):
        """Create AzureProvider with mocked config_manager."""
        config_mock = MagicMock()
        config_mock.get_provider_api_key.return_value = "fake-key"
        config_mock.get_provider_base_url.return_value = "https://test.openai.azure.com"
        config_mock.get_provider_api_version.return_value = "2024-02-15-preview"
        config_mock.get_provider_config.return_value = {"use_responses_api": use_responses_api} if use_responses_api is not None else {}

        with patch("dana.common.llm.providers.azure.config_manager", config_mock):
            from dana.common.llm.providers.azure import AzureProvider

            return AzureProvider(api_key="fake-key", base_url="https://test.openai.azure.com")

    def test_inherits_from_openai_compatible(self):
        provider = self._make_provider()
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_has_stream_method(self):
        provider = self._make_provider()
        assert hasattr(provider, "stream")
        assert callable(provider.stream)

    def test_has_chat_completions_stream(self):
        provider = self._make_provider()
        assert hasattr(provider, "_stream_chat_completions")

    def test_has_responses_stream(self):
        provider = self._make_provider()
        assert hasattr(provider, "_stream_responses")

    def test_config_flag_set(self):
        provider = self._make_provider(use_responses_api=True)
        assert provider._use_responses_api is True

    def test_config_flag_none_by_default(self):
        provider = self._make_provider()
        assert provider._use_responses_api is None
