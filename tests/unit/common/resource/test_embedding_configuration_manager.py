"""Test the EmbeddingConfigurationManager class."""

import os
import unittest
from unittest.mock import patch

from dana.common.resource.embedding.embedding_configuration_manager import EmbeddingConfigurationManager


class TestEmbeddingConfigurationManager(unittest.TestCase):
    """Test the EmbeddingConfigurationManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing environment variables for clean tests
        self.original_env = {}
        for key in ["OPENAI_API_KEY", "COHERE_API_KEY", "DANA_MOCK_EMBEDDING"]:
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

    def test_explicit_model_initialization(self):
        """Test configuration manager with explicit model."""
        config_manager = EmbeddingConfigurationManager(explicit_model="openai:text-embedding-3-small", config={"batch_size": 200})

        self.assertEqual(config_manager.explicit_model, "openai:text-embedding-3-small")
        self.assertEqual(config_manager.config["batch_size"], 200)

    def test_model_validation_with_api_keys(self):
        """Test model validation with various API key scenarios."""
        config_manager = EmbeddingConfigurationManager()

        # Test with no API keys - should still work for validation
        self.assertIsInstance(config_manager._validate_model("openai:text-embedding-3-small"), bool)
        self.assertIsInstance(config_manager._validate_model("cohere:embed-english-v2.0"), bool)

        # Test with OpenAI API key
        os.environ["OPENAI_API_KEY"] = "test-key"
        self.assertTrue(config_manager._validate_model("openai:text-embedding-3-small"))
        self.assertTrue(config_manager._validate_model("openai:text-embedding-3-large"))

        # Test with Cohere API key
        os.environ["COHERE_API_KEY"] = "test-key"
        self.assertTrue(config_manager._validate_model("cohere:embed-english-v2.0"))

    def test_invalid_model_formats(self):
        """Test validation of invalid model formats."""
        config_manager = EmbeddingConfigurationManager()

        # Test invalid formats
        self.assertFalse(config_manager._validate_model(""))
        self.assertFalse(config_manager._validate_model("invalid-format"))
        self.assertFalse(config_manager._validate_model("provider-without-colon"))

    def test_mock_mode_activation(self):
        """Test mock mode activation."""
        os.environ["DANA_MOCK_EMBEDDING"] = "true"
        config_manager = EmbeddingConfigurationManager()

        selected_model = config_manager._determine_model()
        self.assertEqual(selected_model, "mock:test-embeddings")

    def test_explicit_model_override(self):
        """Test that explicit model overrides auto-selection."""
        config_manager = EmbeddingConfigurationManager(explicit_model="openai:text-embedding-3-large")

        selected_model = config_manager._determine_model()
        self.assertEqual(selected_model, "openai:text-embedding-3-large")

    def test_auto_selection_with_available_models(self):
        """Test auto-selection when models are available."""
        with patch.object(EmbeddingConfigurationManager, "_find_first_available_model") as mock_find:
            mock_find.return_value = "openai:text-embedding-3-small"

            config_manager = EmbeddingConfigurationManager()
            selected_model = config_manager._determine_model()

            self.assertEqual(selected_model, "openai:text-embedding-3-small")

    def test_auto_selection_no_models_available(self):
        """Test auto-selection when no models are available."""
        with patch.object(EmbeddingConfigurationManager, "_find_first_available_model") as mock_find:
            mock_find.return_value = None

            config_manager = EmbeddingConfigurationManager()
            selected_model = config_manager._determine_model()

            self.assertIsNone(selected_model)

    def test_model_availability_check(self):
        """Test model availability checking."""
        config_manager = EmbeddingConfigurationManager()

        # Test OpenAI availability
        self.assertFalse(config_manager._is_model_actually_available("openai:text-embedding-3-small"))

        os.environ["OPENAI_API_KEY"] = "test-key"
        self.assertTrue(config_manager._is_model_actually_available("openai:text-embedding-3-small"))

        # Test Cohere availability
        del os.environ["OPENAI_API_KEY"]
        self.assertFalse(config_manager._is_model_actually_available("cohere:embed-english-v2.0"))

        os.environ["COHERE_API_KEY"] = "test-key"
        self.assertTrue(config_manager._is_model_actually_available("cohere:embed-english-v2.0"))

        # Test HuggingFace availability (always true)
        self.assertTrue(config_manager._is_model_actually_available("huggingface:BAAI/bge-small-en-v1.5"))

    def test_find_first_available_model_with_config(self):
        """Test finding first available model from configuration."""
        mock_config = {
            "embedding": {
                "preferred_models": ["openai:text-embedding-3-small", "cohere:embed-english-v2.0", "huggingface:BAAI/bge-small-en-v1.5"]
            }
        }

        with patch("dana.common.resource.embedding.embedding_configuration_manager.ConfigLoader") as mock_config_loader_class:
            mock_config_loader_instance = mock_config_loader_class.return_value
            mock_config_loader_instance.get_default_config.return_value = mock_config

            config_manager = EmbeddingConfigurationManager()

            # No API keys - should find HuggingFace (always available)
            result = config_manager._find_first_available_model()
            self.assertEqual(result, "huggingface:BAAI/bge-small-en-v1.5")

            # With OpenAI key - should find OpenAI first
            os.environ["OPENAI_API_KEY"] = "test-key"
            result = config_manager._find_first_available_model()
            self.assertEqual(result, "openai:text-embedding-3-small")

    def test_get_model_config(self):
        """Test getting model-specific configuration."""
        mock_config = {
            "embedding": {
                "provider_configs": {
                    "openai": {"api_key": "env:OPENAI_API_KEY", "batch_size": 100, "dimension": 1024},
                    "cohere": {"api_key": "env:COHERE_API_KEY", "batch_size": 50},
                }
            }
        }

        with patch("dana.common.resource.embedding.embedding_configuration_manager.ConfigLoader") as mock_config_loader_class:
            mock_config_loader_instance = mock_config_loader_class.return_value
            mock_config_loader_instance.get_default_config.return_value = mock_config

            config_manager = EmbeddingConfigurationManager()

            # Test OpenAI config
            openai_config = config_manager.get_model_config("openai:text-embedding-3-small")
            expected_openai = {"api_key": "env:OPENAI_API_KEY", "batch_size": 100, "dimension": 1024}
            self.assertEqual(openai_config, expected_openai)

            # Test Cohere config
            cohere_config = config_manager.get_model_config("cohere:embed-english-v2.0")
            expected_cohere = {"api_key": "env:COHERE_API_KEY", "batch_size": 50}
            self.assertEqual(cohere_config, expected_cohere)

            # Test invalid model format
            invalid_config = config_manager.get_model_config("invalid-format")
            self.assertEqual(invalid_config, {})

    def test_supported_providers(self):
        """Test supported providers functionality."""
        config_manager = EmbeddingConfigurationManager()

        supported = config_manager.get_supported_providers()
        expected = ["openai", "huggingface", "cohere"]
        self.assertEqual(supported, expected)

        # Test provider support checking
        self.assertTrue(config_manager.is_provider_supported("openai"))
        self.assertTrue(config_manager.is_provider_supported("huggingface"))
        self.assertTrue(config_manager.is_provider_supported("cohere"))
        self.assertFalse(config_manager.is_provider_supported("unsupported"))

    def test_selected_model_property(self):
        """Test selected_model property and setter."""
        config_manager = EmbeddingConfigurationManager()

        # Test initial selection (lazy loading)
        with patch.object(config_manager, "_determine_model") as mock_determine:
            mock_determine.return_value = "openai:text-embedding-3-small"

            model = config_manager.selected_model
            self.assertEqual(model, "openai:text-embedding-3-small")
            mock_determine.assert_called_once()

        # Test setter
        config_manager.selected_model = "cohere:embed-english-v2.0"
        self.assertEqual(config_manager.selected_model, "cohere:embed-english-v2.0")
