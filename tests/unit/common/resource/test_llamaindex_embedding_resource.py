"""Test the LlamaIndex embedding integration."""

import os
import sys
import unittest
import types
from unittest.mock import MagicMock, patch

from dana.common.exceptions import EmbeddingError
from dana.common.sys_resource.embedding.embedding_integrations import (
    LlamaIndexEmbeddingResource,
    RAGEmbeddingResource,
    get_default_embedding_model,
    get_embedding_model,
)


class TestLlamaIndexEmbeddingResource(unittest.TestCase):
    """Test the LlamaIndex embedding integration."""

    def setUp(self):
        """Set up test fixtures."""
        tracked_env_keys = [
            "OPENAI_API_KEY",
            "COHERE_API_KEY",
            "LOCAL_EMBEDDING_BASE_URL",
            "LOCAL_BASE_URL",
            "EMBEDDING_BATCH_SIZE",
        ]
        self.original_env = {key: os.environ.get(key) for key in tracked_env_keys}
        # Set a dummy API key to satisfy checks that assume it's available
        os.environ["OPENAI_API_KEY"] = "test-key"

    def tearDown(self):
        """Clean up after tests."""
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    @patch("dana.common.sys_resource.embedding.embedding_integrations.LlamaIndexEmbeddingResource._create_embedding")
    def test_get_embedding_model_simple(self, mock_create_embedding):
        """Test get_embedding_model calls the internal creation method."""
        mock_embedding_instance = MagicMock()
        mock_create_embedding.return_value = mock_embedding_instance

        result = get_embedding_model("openai:text-embedding-3-small")

        self.assertEqual(result, mock_embedding_instance)
        mock_create_embedding.assert_called_once_with("openai:text-embedding-3-small", None)

    @patch("dana.common.sys_resource.embedding.embedding_integrations.LlamaIndexEmbeddingResource._create_embedding")
    @patch("dana.common.sys_resource.embedding.embedding_integrations.LlamaIndexEmbeddingResource._is_model_available")
    def test_get_default_embedding_model_simple(self, mock_is_available, mock_create_embedding):
        """Test get_default_embedding_model calls the internal creation method."""
        mock_embedding_instance = MagicMock()
        mock_create_embedding.return_value = mock_embedding_instance
        mock_is_available.return_value = True

        result = get_default_embedding_model()

        self.assertEqual(result, mock_embedding_instance)
        self.assertTrue(mock_create_embedding.called)

    @patch("llama_index.core.Settings")
    @patch("dana.common.sys_resource.embedding.embedding_integrations.LlamaIndexEmbeddingResource._create_embedding")
    def test_setup_llamaindex_simple(self, mock_create_embedding, mock_settings):
        """Test setup_llamaindex configures global settings correctly."""
        mock_embedding_instance = MagicMock()
        mock_create_embedding.return_value = mock_embedding_instance

        RAGEmbeddingResource().setup_llamaindex("openai:text-embedding-3-small", chunk_size=512)

        mock_create_embedding.assert_called_once_with("openai:text-embedding-3-small", None)
        self.assertEqual(mock_settings.embed_model, mock_embedding_instance)
        self.assertEqual(mock_settings.chunk_size, 512)

    @patch("dana.common.sys_resource.embedding.embedding_integrations.ConfigLoader")
    def test_resource_config_override_simple(self, mock_loader):
        """Test that resource methods use config overrides correctly."""
        base_config = {"embedding": {"provider_configs": {"openai": {"api_key": "env:OPENAI_API_KEY", "batch_size": 100}}}}
        mock_loader.return_value.get_default_config.return_value = base_config

        override_config = {"embedding": {"provider_configs": {"openai": {"batch_size": 50}}}}
        resource = LlamaIndexEmbeddingResource(config_override=override_config)

        with patch("llama_index.embeddings.openai.OpenAIEmbedding") as mock_openai:
            # Mock the embedding instance
            mock_openai.return_value = MagicMock()

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

    @patch("dana.common.sys_resource.embedding.embedding_integrations.ConfigLoader")
    def test_ollama_env_defaults_used_when_config_missing(self, mock_loader):
        """Ensure Ollama embedding creation uses environment fallbacks when config is empty."""
        mock_loader.return_value.get_default_config.return_value = {
            "embedding": {
                "provider_configs": {"ollama": {}},
                "preferred_models": ["ollama:nomic-embed-text"],
            }
        }

        os.environ["LOCAL_EMBEDDING_BASE_URL"] = "http://localhost:11434"
        os.environ["LOCAL_BASE_URL"] = "http://localhost:11434"
        os.environ["EMBEDDING_BATCH_SIZE"] = "32"

        fake_llama_index = types.ModuleType("llama_index")
        fake_llama_index.__path__ = []  # mark as package
        fake_embeddings_pkg = types.ModuleType("llama_index.embeddings")
        fake_embeddings_pkg.__path__ = []
        fake_ollama_pkg = types.ModuleType("llama_index.embeddings.ollama")
        mock_embedding_cls = MagicMock(return_value="embedding-instance")
        fake_ollama_pkg.OllamaEmbedding = mock_embedding_cls

        with patch.dict(
            sys.modules,
            {
                "llama_index": fake_llama_index,
                "llama_index.embeddings": fake_embeddings_pkg,
                "llama_index.embeddings.ollama": fake_ollama_pkg,
            },
        ):
            resource = LlamaIndexEmbeddingResource()
            embedding = resource._create_ollama_embedding("nomic-embed-text", {}, None)

        self.assertEqual(embedding, "embedding-instance")
        self.assertTrue(mock_embedding_cls.called)
        _, kwargs = mock_embedding_cls.call_args
        self.assertEqual(kwargs.get("model_name"), "nomic-embed-text")
        self.assertEqual(kwargs.get("base_url"), "http://localhost:11434")
        self.assertEqual(kwargs.get("embed_batch_size"), 32)


if __name__ == "__main__":
    unittest.main()
