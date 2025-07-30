"""Test the LlamaIndex embedding integration."""

import os
import unittest
from unittest.mock import patch, MagicMock

from dana.common.exceptions import EmbeddingError
from dana.common.resource.embedding.embedding_integrations import (
    LlamaIndexEmbeddingResource,
    get_embedding_model,
    get_default_embedding_model,
    setup_llamaindex,
)


class TestLlamaIndexEmbeddingResource(unittest.TestCase):
    """Test the LlamaIndex embedding integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = {key: os.environ.get(key) for key in ["OPENAI_API_KEY", "COHERE_API_KEY"]}
        # Set a dummy API key to satisfy checks that assume it's available
        os.environ["OPENAI_API_KEY"] = "test-key"

    def tearDown(self):
        """Clean up after tests."""
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    @patch("dana.common.resource.embedding.embedding_integrations.LlamaIndexEmbeddingResource._create_llamaindex_embedding")
    def test_get_embedding_model_simple(self, mock_create_embedding):
        """Test get_embedding_model calls the internal creation method."""
        mock_embedding_instance = MagicMock()
        mock_create_embedding.return_value = mock_embedding_instance

        result = get_embedding_model("openai:text-embedding-3-small")

        self.assertEqual(result, mock_embedding_instance)
        mock_create_embedding.assert_called_once_with("openai:text-embedding-3-small")

    @patch("dana.common.resource.embedding.embedding_integrations.LlamaIndexEmbeddingResource._create_default_llamaindex_embedding")
    def test_get_default_embedding_model_simple(self, mock_create_default):
        """Test get_default_embedding_model calls the internal default creation method."""
        mock_embedding_instance = MagicMock()
        mock_create_default.return_value = mock_embedding_instance

        result = get_default_embedding_model()

        self.assertEqual(result, mock_embedding_instance)
        mock_create_default.assert_called_once()

    @patch("llama_index.core.Settings")
    @patch("dana.common.resource.embedding.embedding_integrations.LlamaIndexEmbeddingResource._create_llamaindex_embedding")
    def test_setup_llamaindex_simple(self, mock_create_embedding, mock_settings):
        """Test setup_llamaindex configures global settings correctly."""
        mock_embedding_instance = MagicMock()
        mock_create_embedding.return_value = mock_embedding_instance

        setup_llamaindex("openai:text-embedding-3-small", chunk_size=512)

        mock_create_embedding.assert_called_once_with("openai:text-embedding-3-small")
        self.assertEqual(mock_settings.embed_model, mock_embedding_instance)
        self.assertEqual(mock_settings.chunk_size, 512)

    @patch("dana.common.resource.embedding.embedding_integrations.ConfigLoader")
    def test_resource_config_override_simple(self, mock_loader):
        """Test that resource methods use config overrides correctly."""
        base_config = {"embedding": {"provider_configs": {"openai": {"api_key": "env:OPENAI_API_KEY", "batch_size": 100}}}}
        mock_loader.return_value.get_default_config.return_value = base_config

        override_config = {"embedding": {"provider_configs": {"openai": {"batch_size": 50}}}}
        resource = LlamaIndexEmbeddingResource(config_override=override_config)

        with patch("llama_index.embeddings.openai.OpenAIEmbedding") as mock_openai:
            resource.get_embedding_model("openai:text-embedding-3-small")

            mock_openai.assert_called_once()
            _, kwargs = mock_openai.call_args
            self.assertEqual(kwargs.get("embed_batch_size"), 50)
            self.assertEqual(kwargs.get("api_key"), "test-key")

    def test_invalid_model_format_error(self):
        """Test that an invalid model format raises an EmbeddingError."""
        with self.assertRaises(EmbeddingError) as context:
            get_embedding_model("invalid-format")
        self.assertIn("Invalid model format", str(context.exception))


if __name__ == "__main__":
    unittest.main()
