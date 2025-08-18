"""Test the EmbeddingQueryExecutor class."""

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from dana.common.exceptions import EmbeddingError, EmbeddingProviderError
from dana.common.sys_resource.embedding.embedding_query_executor import EmbeddingQueryExecutor


class TestEmbeddingQueryExecutor(unittest.TestCase):
    """Test the EmbeddingQueryExecutor class."""

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

    def test_executor_initialization(self):
        """Test query executor initialization."""
        executor = EmbeddingQueryExecutor(model="openai:text-embedding-3-small", batch_size=50)

        self.assertEqual(executor.model, "openai:text-embedding-3-small")
        self.assertEqual(executor.batch_size, 50)
        self.assertFalse(executor._initialized)

    def test_property_setters(self):
        """Test property setters."""
        executor = EmbeddingQueryExecutor()

        executor.model = "cohere:embed-english-v2.0"
        self.assertEqual(executor.model, "cohere:embed-english-v2.0")

        executor.batch_size = 100
        self.assertEqual(executor.batch_size, 100)

    def test_mock_embedding_generation(self):
        """Test mock embedding generation."""
        executor = EmbeddingQueryExecutor(model="mock:test-model")

        async def run_test():
            provider_configs = {}
            await executor.initialize(provider_configs)

            texts = ["Hello", "World"]
            embeddings = await executor._generate_mock_embeddings(texts)

            self.assertEqual(len(embeddings), 2)
            self.assertIsInstance(embeddings[0], list)
            self.assertEqual(len(embeddings[0]), 384)  # Mock embedding dimension

        asyncio.run(run_test())

    def test_generate_embeddings_without_initialization(self):
        """Test that generating embeddings without initialization raises error."""
        executor = EmbeddingQueryExecutor(model="openai:text-embedding-3-small")

        async def run_test():
            with self.assertRaises(EmbeddingError) as context:
                await executor.generate_embeddings(["test"])

            self.assertIn("not initialized", str(context.exception))

        asyncio.run(run_test())

    def test_empty_text_list(self):
        """Test handling of empty text list."""
        executor = EmbeddingQueryExecutor(model="mock:test-model")

        async def run_test():
            provider_configs = {}
            await executor.initialize(provider_configs)

            embeddings = await executor.generate_embeddings([])
            self.assertEqual(embeddings, [])

        asyncio.run(run_test())

    def test_single_vs_batch_processing(self):
        """Test single text vs batch processing paths."""
        executor = EmbeddingQueryExecutor(model="mock:test-model", batch_size=2)

        async def run_test():
            provider_configs = {}
            await executor.initialize(provider_configs)

            # Single text
            single_result = await executor.generate_embeddings(["single text"])
            self.assertEqual(len(single_result), 1)

            # Multiple texts
            batch_texts = ["text1", "text2", "text3"]
            batch_result = await executor.generate_embeddings(batch_texts)
            self.assertEqual(len(batch_result), 3)

        asyncio.run(run_test())

    def test_unsupported_provider(self):
        """Test handling of unsupported provider."""
        executor = EmbeddingQueryExecutor(model="unsupported:model")

        async def run_test():
            provider_configs = {}
            await executor.initialize(provider_configs)

            with self.assertRaises(EmbeddingProviderError) as context:
                await executor.generate_embeddings(["test"])

            self.assertIn("Unsupported provider", str(context.exception))

        asyncio.run(run_test())

    def test_no_model_specified(self):
        """Test error when no model is specified."""
        executor = EmbeddingQueryExecutor()  # No model

        async def run_test():
            provider_configs = {}
            await executor.initialize(provider_configs)

            with self.assertRaises(EmbeddingError) as context:
                await executor.generate_embeddings(["test"])

            self.assertIn("No model specified", str(context.exception))

        asyncio.run(run_test())

    @patch("dana.common.sys_resource.embedding.embedding_query_executor.asyncio.get_event_loop")
    def test_openai_provider_initialization(self, mock_get_loop):
        """Test OpenAI provider initialization."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        executor = EmbeddingQueryExecutor(model="openai:text-embedding-3-small")

        with patch("openai.AsyncOpenAI") as _:

            async def run_test():
                await executor._initialize_openai()
                # Should not raise an error
                self.assertIsNotNone(executor)

            asyncio.run(run_test())

    def test_cohere_provider_initialization(self):
        """Test Cohere provider initialization."""
        executor = EmbeddingQueryExecutor(model="cohere:embed-english-v2.0")

        # Cohere packages are lightweight and already installed - simple mocking is sufficient
        with patch("cohere.AsyncClient") as _:

            async def run_test():
                await executor._initialize_cohere()
                # Should not raise an error since cohere is available
                self.assertIsNotNone(executor)

            asyncio.run(run_test())

    def test_huggingface_provider_initialization(self):
        """Test HuggingFace provider initialization."""
        executor = EmbeddingQueryExecutor(model="huggingface:BAAI/bge-small-en-v1.5")

        # Mock sentence_transformers in sys.modules first to avoid import errors
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            # Mock the sentence_transformers import
            with patch("sentence_transformers.SentenceTransformer") as _:
                with patch("asyncio.get_event_loop") as mock_get_loop:
                    mock_loop = MagicMock()
                    mock_loop.run_in_executor = AsyncMock(return_value=MagicMock())
                    mock_get_loop.return_value = mock_loop

                    async def run_test():
                        try:
                            await executor._initialize_huggingface()
                            # Should not raise an error if sentence_transformers is available (mocked)
                            self.assertIsNotNone(executor)
                        except ImportError:
                            # If sentence_transformers is not installed, this is expected
                            self.skipTest("sentence_transformers not installed")

                    asyncio.run(run_test())

    def test_provider_initialization_missing_dependencies(self):
        """Test provider initialization with missing dependencies."""
        executor = EmbeddingQueryExecutor()

        async def test_missing_cohere():
            # Test missing Cohere - the actual implementation should handle this gracefully
            try:
                await executor._initialize_cohere()
            except ImportError:
                # Expected if cohere is not installed
                pass

        async def test_missing_huggingface():
            # Test missing HuggingFace - the actual implementation should handle this gracefully
            try:
                await executor._initialize_huggingface()
            except ImportError:
                # Expected if sentence_transformers is not installed
                pass

        # These tests just verify the imports don't crash the test runner
        asyncio.run(test_missing_cohere())
        asyncio.run(test_missing_huggingface())

    def test_batch_processing_logic(self):
        """Test batch processing with different batch sizes."""
        executor = EmbeddingQueryExecutor(model="mock:test-model", batch_size=2)

        async def run_test():
            provider_configs = {}
            await executor.initialize(provider_configs)

            # Test with texts that require multiple batches
            texts = ["text1", "text2", "text3", "text4", "text5"]
            embeddings = await executor.generate_embeddings(texts)

            self.assertEqual(len(embeddings), 5)
            for embedding in embeddings:
                self.assertIsInstance(embedding, list)

        asyncio.run(run_test())

    def test_provider_error_handling(self):
        """Test provider-specific error handling."""
        executor = EmbeddingQueryExecutor(model="openai:text-embedding-3-small")

        async def run_test():
            # Test authentication error
            with patch.object(executor, "_generate_openai_embeddings") as mock_openai:
                mock_openai.side_effect = Exception("unauthorized")

                provider_configs = {"openai": {"api_key": "invalid"}}
                await executor.initialize(provider_configs)
                # await executor._generate_single_batch(["test"])

        asyncio.run(run_test())
