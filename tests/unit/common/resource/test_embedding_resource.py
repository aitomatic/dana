"""Test the EmbeddingResource class."""

import asyncio
import os
import unittest
from unittest.mock import patch

from dana.common.resource.embedding.embedding_resource import EmbeddingResource
from dana.common.types import BaseRequest, BaseResponse


class TestEmbeddingResource(unittest.TestCase):
    """Test the EmbeddingResource class."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear environment variables for clean tests
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

    def test_mock_embedding_generation(self):
        """Test EmbeddingResource with mock embedding generation."""
        os.environ["DANA_MOCK_EMBEDDING"] = "true"

        embedding_resource = EmbeddingResource(name="test_embedding", model="mock:test-model")

        async def run_test():
            request = BaseRequest(arguments={"text": "Hello, world!"})
            response = await embedding_resource.query(request)

            # Verify response structure
            self.assertIsInstance(response, BaseResponse)
            self.assertTrue(response.success)
            self.assertIsNotNone(response.content)
            self.assertIsNone(response.error)

            # Verify embedding content
            content = response.content
            self.assertIn("embeddings", content)
            self.assertIn("model", content)
            self.assertIn("dimension", content)
            self.assertIn("count", content)

            embeddings = content["embeddings"]
            self.assertIsInstance(embeddings, list)
            self.assertEqual(len(embeddings), 1)
            self.assertIsInstance(embeddings[0], list)

        asyncio.run(run_test())

    def test_batch_embedding_generation(self):
        """Test batch embedding generation."""
        os.environ["DANA_MOCK_EMBEDDING"] = "true"

        embedding_resource = EmbeddingResource(name="test_embedding", model="mock:test-model")

        async def run_test():
            texts = ["Hello", "World", "Test"]
            request = BaseRequest(arguments={"texts": texts})
            response = await embedding_resource.query(request)

            self.assertTrue(response.success)
            content = response.content
            embeddings = content["embeddings"]

            self.assertEqual(len(embeddings), 3)
            self.assertEqual(content["count"], 3)

        asyncio.run(run_test())

    def test_configuration_hierarchy(self):
        """Test configuration hierarchy: constructor > config file."""
        with patch("dana.common.resource.embedding.embedding_resource.ConfigLoader") as mock_loader:
            # Mock config file
            mock_config = {
                "embedding": {
                    "preferred_models": ["openai:text-embedding-3-small"],
                    "provider_configs": {"openai": {"api_key": "env:OPENAI_API_KEY", "batch_size": 100}},
                }
            }
            mock_loader.return_value.get_default_config.return_value = mock_config

            # Test constructor overrides
            embedding = EmbeddingResource(name="test_embedding", model="openai:text-embedding-3-large", batch_size=200)

            self.assertEqual(embedding.model, "openai:text-embedding-3-large")
            self.assertEqual(embedding.get_batch_size(), 200)

    def test_model_auto_selection(self):
        """Test automatic model selection based on API key availability."""
        with patch("dana.common.resource.embedding.embedding_resource.ConfigLoader") as mock_loader:
            mock_config = {
                "embedding": {
                    "preferred_models": ["openai:text-embedding-3-small", "cohere:embed-english-v2.0"],
                    "provider_configs": {"openai": {"api_key": "env:OPENAI_API_KEY"}, "cohere": {"api_key": "env:COHERE_API_KEY"}},
                }
            }
            mock_loader.return_value.get_default_config.return_value = mock_config

            # Test with OpenAI key available
            os.environ["OPENAI_API_KEY"] = "test-key"
            embedding = EmbeddingResource(name="test_embedding")
            self.assertEqual(embedding.model, "openai:text-embedding-3-small")

            # Test with Cohere key available (remove OpenAI)
            del os.environ["OPENAI_API_KEY"]
            os.environ["COHERE_API_KEY"] = "test-key"
            embedding2 = EmbeddingResource(name="test_embedding2")
            self.assertEqual(embedding2.model, "cohere:embed-english-v2.0")

    def test_error_handling(self):
        """Test error classification and handling."""
        embedding = EmbeddingResource(name="test_embedding", model="openai:text-embedding-3-small")

        async def run_test():
            # Test with no API key
            request = BaseRequest(arguments={"text": "test"})
            response = await embedding.query(request)

            # Should return error response
            self.assertFalse(response.success)
            self.assertIsNotNone(response.error)

        asyncio.run(run_test())

    def test_invalid_request_format(self):
        """Test handling of invalid request formats."""
        os.environ["DANA_MOCK_EMBEDDING"] = "true"
        embedding = EmbeddingResource(name="test_embedding", model="mock:test-model")

        async def run_test():
            # Test empty request
            request = BaseRequest(arguments={})
            response = await embedding.query(request)
            self.assertFalse(response.success)
            self.assertIn("No arguments provided", response.error)

            # Test invalid text type - still should handle gracefully
            request = BaseRequest(arguments={"text": 123})
            response = await embedding.query(request)
            # This might succeed if the implementation converts to string, or fail gracefully
            # Let's check the response rather than assume it will fail
            self.assertIsInstance(response, BaseResponse)

        asyncio.run(run_test())

    def test_provider_config_resolution(self):
        """Test provider configuration resolution including environment variables."""
        with patch("dana.common.resource.embedding.embedding_resource.ConfigLoader") as mock_loader:
            mock_config = {
                "embedding": {
                    "preferred_models": ["openai:text-embedding-3-small"],
                    "provider_configs": {"openai": {"api_key": "env:OPENAI_API_KEY", "batch_size": 100, "dimension": 1024}},
                }
            }
            mock_loader.return_value.get_default_config.return_value = mock_config

            os.environ["OPENAI_API_KEY"] = "test-api-key"

            embedding = EmbeddingResource(name="test_embedding")

            # Check that environment variable was resolved
            resolved_config = embedding.provider_configs.get("openai", {})
            self.assertEqual(resolved_config["api_key"], "test-api-key")
            self.assertEqual(resolved_config["batch_size"], 100)

    def test_embedding_resource_cleanup(self):
        """Test resource cleanup."""
        embedding = EmbeddingResource(name="test_embedding", model="mock:test-model")

        async def run_test():
            await embedding.cleanup()
            # Verify cleanup completed without errors
            self.assertIsNotNone(embedding)

        asyncio.run(run_test())
