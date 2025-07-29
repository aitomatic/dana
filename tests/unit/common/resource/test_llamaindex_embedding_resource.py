"""Test the LlamaIndex embedding integration."""

import os
import unittest
from unittest.mock import patch, MagicMock

from dana.common.exceptions import EmbeddingError
from dana.common.resource.embedding.llamaindex_embedding_resource import (
    LlamaIndexEmbeddingResource,
    create_llamaindex_embedding,
    setup_llamaindex,
    get_embedding_model,
)


class TestLlamaIndexEmbeddingResource(unittest.TestCase):
    """Test the LlamaIndex embedding integration."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_env = {}

    def setUp(self):
        """Set up test fixtures."""
        # Clear environment variables for clean tests
        self.original_env = {}
        for key in ["OPENAI_API_KEY", "COHERE_API_KEY"]:
            self.original_env[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    @staticmethod
    def mock_heavy_dependencies():
        """Context manager to mock heavy ML dependencies for testing.

        This prevents tests from requiring sentence-transformers, torch, etc.
        to be installed while still testing the integration logic.
        """
        return patch.dict(
            "sys.modules",
            {
                "sentence_transformers": MagicMock(),
                "torch": MagicMock(),
                "transformers": MagicMock(),
            },
        )

    def test_resource_initialization(self):
        """Test LlamaIndexEmbeddingResource initialization."""
        resource = LlamaIndexEmbeddingResource()
        self.assertIsNone(resource.config_override)

        # Test with config override
        config_override = {"embedding": {"provider_configs": {"openai": {"batch_size": 200}}}}
        resource_with_config = LlamaIndexEmbeddingResource(config_override=config_override)
        self.assertEqual(resource_with_config.config_override, config_override)

    @patch("dana.common.resource.embedding.llamaindex_embedding_resource.ConfigLoader")
    def test_create_llamaindex_embedding_function(self, mock_loader):
        """Test create_llamaindex_embedding function."""
        # Mock configuration
        mock_config = {"embedding": {"provider_configs": {"openai": {"api_key": "test-key", "batch_size": 100, "dimension": 1024}}}}
        mock_loader.return_value.get_default_config.return_value = mock_config

        with patch("llama_index.embeddings.openai.OpenAIEmbedding") as mock_openai_embedding:
            mock_embedding_instance = MagicMock()
            mock_openai_embedding.return_value = mock_embedding_instance

            result = create_llamaindex_embedding("openai:text-embedding-3-small")

            self.assertEqual(result, mock_embedding_instance)
            mock_openai_embedding.assert_called_once_with(
                api_key="test-key",
                model="text-embedding-3-small",
                embed_batch_size=100,
                dimensions=1024,
            )

    def test_invalid_model_format(self):
        """Test error handling for invalid model format."""
        with self.assertRaises(EmbeddingError) as context:
            create_llamaindex_embedding("invalid-format")

        self.assertIn("Invalid model format", str(context.exception))
        self.assertIn("Expected 'provider:model_name'", str(context.exception))

    @patch("dana.common.resource.embedding.llamaindex_embedding_resource.ConfigLoader")
    def test_unsupported_provider(self, mock_loader):
        """Test error handling for unsupported provider."""
        mock_config = {"embedding": {"provider_configs": {}}}
        mock_loader.return_value.get_default_config.return_value = mock_config

        with self.assertRaises(EmbeddingError) as context:
            create_llamaindex_embedding("unsupported:model")

        self.assertIn("Unsupported provider", str(context.exception))

    @patch("dana.common.resource.embedding.llamaindex_embedding_resource.ConfigLoader")
    def test_openai_embedding_creation(self, mock_loader):
        """Test OpenAI embedding creation."""
        os.environ["OPENAI_API_KEY"] = "test-openai-key"

        mock_config = {"embedding": {"provider_configs": {"openai": {"api_key": "env:OPENAI_API_KEY", "batch_size": 50, "dimension": 512}}}}
        mock_loader.return_value.get_default_config.return_value = mock_config

        with patch("llama_index.embeddings.openai.OpenAIEmbedding") as mock_openai:
            create_llamaindex_embedding("openai:text-embedding-3-small")

            mock_openai.assert_called_once_with(
                api_key="test-openai-key",
                model="text-embedding-3-small",
                embed_batch_size=50,
                dimensions=512,
            )

    @patch("dana.common.resource.embedding.llamaindex_embedding_resource.ConfigLoader")
    def test_cohere_embedding_creation(self, mock_loader):
        """Test Cohere embedding creation."""
        os.environ["COHERE_API_KEY"] = "test-cohere-key"

        mock_config = {"embedding": {"provider_configs": {"cohere": {"api_key": "env:COHERE_API_KEY", "batch_size": 25}}}}
        mock_loader.return_value.get_default_config.return_value = mock_config

        # Cohere packages are lightweight and already installed - simple mocking is sufficient
        try:
            # Try to import first to ensure the module is available

            with patch("llama_index.embeddings.cohere.CohereEmbedding") as mock_cohere:
                create_llamaindex_embedding("cohere:embed-english-v2.0")

                mock_cohere.assert_called_once_with(
                    api_key="test-cohere-key",
                    model_name="embed-english-v2.0",
                    embed_batch_size=25,
                )
        except ImportError:
            self.skipTest("llama-index-embeddings-cohere not installed")

    @patch("dana.common.resource.embedding.llamaindex_embedding_resource.ConfigLoader")
    def test_huggingface_embedding_creation(self, mock_loader):
        """Test HuggingFace embedding creation."""
        mock_config = {"embedding": {"provider_configs": {"huggingface": {"cache_dir": "/custom/cache"}}}}
        mock_loader.return_value.get_default_config.return_value = mock_config

        # Mock heavy ML dependencies to avoid requiring them for tests
        with self.mock_heavy_dependencies():
            try:
                # Try to import and patch the HuggingFace embedding class

                with patch("llama_index.embeddings.huggingface.HuggingFaceEmbedding") as mock_hf:
                    create_llamaindex_embedding("huggingface:BAAI/bge-small-en-v1.5")

                    mock_hf.assert_called_once_with(
                        model_name="BAAI/bge-small-en-v1.5",
                        cache_folder="/custom/cache",
                    )
            except ImportError:
                self.skipTest("llama-index-embeddings-huggingface not installed")

    def test_missing_api_key_error(self):
        """Test error when API key is missing."""
        with patch("dana.common.resource.embedding.llamaindex_embedding_resource.ConfigLoader") as mock_loader:
            mock_config = {"embedding": {"provider_configs": {"openai": {"api_key": "env:MISSING_KEY", "batch_size": 100}}}}
            mock_loader.return_value.get_default_config.return_value = mock_config

            with self.assertRaises(EmbeddingError) as context:
                create_llamaindex_embedding("openai:text-embedding-3-small")

            self.assertIn("API key not found", str(context.exception))

    def test_missing_import_error_handling(self):
        """Test handling of missing LlamaIndex imports."""
        with patch("dana.common.resource.embedding.llamaindex_embedding_resource.ConfigLoader") as mock_loader:
            mock_config = {"embedding": {"provider_configs": {"openai": {"api_key": "test-key"}}}}
            mock_loader.return_value.get_default_config.return_value = mock_config

            # Test with missing OpenAI package
            original_import = __builtins__["__import__"]

            def mock_import(name, *args, **kwargs):
                if name == "llama_index.embeddings.openai":
                    raise ImportError("No module named 'llama_index.embeddings.openai'")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                with self.assertRaises(EmbeddingError) as context:
                    create_llamaindex_embedding("openai:text-embedding-3-small")

                self.assertIn("Install:", str(context.exception))

    def test_setup_llamaindex_function(self):
        """Test setup_llamaindex function."""
        with patch("dana.common.resource.embedding.llamaindex_embedding_resource.create_llamaindex_embedding") as mock_create:
            with patch("llama_index.core.Settings") as mock_settings:
                mock_embedding = MagicMock()
                mock_create.return_value = mock_embedding

                setup_llamaindex("openai:text-embedding-3-small", chunk_size=1024)

                mock_create.assert_called_once_with("openai:text-embedding-3-small")
                self.assertEqual(mock_settings.embed_model, mock_embedding)
                self.assertEqual(mock_settings.chunk_size, 1024)

    def test_setup_llamaindex_missing_core(self):
        """Test setup_llamaindex with missing llama-index-core."""
        with patch("builtins.__import__", side_effect=ImportError("No module named 'llama_index.core'")):
            with self.assertRaises(EmbeddingError) as context:
                setup_llamaindex("openai:text-embedding-3-small")

            self.assertIn("Install: pip install llama-index-core", str(context.exception))

    def test_resource_get_embedding_model(self):
        """Test LlamaIndexEmbeddingResource.get_embedding_model."""
        resource = LlamaIndexEmbeddingResource()

        with patch("dana.common.resource.embedding.llamaindex_embedding_resource.create_llamaindex_embedding") as mock_create:
            mock_embedding = MagicMock()
            mock_create.return_value = mock_embedding

            result = resource.get_embedding_model("openai:text-embedding-3-small")

            self.assertEqual(result, mock_embedding)
            mock_create.assert_called_once_with("openai:text-embedding-3-small", None)

    def test_resource_get_embedding_model_error(self):
        """Test LlamaIndexEmbeddingResource.get_embedding_model error handling."""
        resource = LlamaIndexEmbeddingResource()

        with patch("dana.common.resource.embedding.llamaindex_embedding_resource.create_llamaindex_embedding") as mock_create:
            mock_create.side_effect = EmbeddingError("Test error")

            with self.assertRaises(EmbeddingError):
                resource.get_embedding_model("openai:text-embedding-3-small")

    def test_resource_setup_globals(self):
        """Test LlamaIndexEmbeddingResource.setup_globals."""
        resource = LlamaIndexEmbeddingResource()

        with patch("dana.common.resource.embedding.llamaindex_embedding_resource.setup_llamaindex") as mock_setup:
            resource.setup_globals("openai:text-embedding-3-small", chunk_size=2048)

            mock_setup.assert_called_once_with("openai:text-embedding-3-small", 2048)

    def test_resource_setup_globals_error(self):
        """Test LlamaIndexEmbeddingResource.setup_globals error handling."""
        resource = LlamaIndexEmbeddingResource()

        with patch("dana.common.resource.embedding.llamaindex_embedding_resource.setup_llamaindex") as mock_setup:
            mock_setup.side_effect = EmbeddingError("Test error")

            with self.assertRaises(EmbeddingError):
                resource.setup_globals("openai:text-embedding-3-small")

    def test_get_embedding_model_alias(self):
        """Test get_embedding_model alias function."""
        with patch("dana.common.resource.embedding.llamaindex_embedding_resource.ConfigLoader") as mock_loader:
            mock_config = {"embedding": {"provider_configs": {"openai": {"api_key": "test-api-key"}}}}
            mock_loader.return_value.get_default_config.return_value = mock_config

            with patch("llama_index.embeddings.openai.OpenAIEmbedding") as mock_openai:
                mock_embedding = MagicMock()
                mock_openai.return_value = mock_embedding

                result = get_embedding_model("openai:text-embedding-3-small")

                self.assertEqual(result, mock_embedding)
                mock_openai.assert_called_once()

    def test_config_override_functionality(self):
        """Test configuration override functionality."""
        config_override = {"embedding": {"provider_configs": {"openai": {"api_key": "override-key", "batch_size": 999}}}}

        with patch("dana.common.resource.embedding.llamaindex_embedding_resource.ConfigLoader") as mock_loader:
            base_config = {"embedding": {"provider_configs": {"openai": {"api_key": "base-key", "batch_size": 100, "dimension": 1024}}}}
            mock_loader.return_value.get_default_config.return_value = base_config

            with patch("llama_index.embeddings.openai.OpenAIEmbedding") as mock_openai:
                create_llamaindex_embedding("openai:text-embedding-3-small", config_override)

                # Should use override values where available, base values otherwise
                mock_openai.assert_called_once_with(
                    api_key="override-key",
                    model="text-embedding-3-small",
                    embed_batch_size=999,  # Override value
                    dimensions=1024,  # Base value (not overridden)
                )
