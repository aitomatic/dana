"""Embedding Query Execution Engine for Dana.

This module provides the EmbeddingQueryExecutor class, which handles the core
embedding generation logic including batch processing and provider integration.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
from typing import Any

from dana.common.exceptions import (
    EmbeddingError,
    EmbeddingProviderError,
    EmbeddingAuthenticationError,
)
from dana.common.mixins.loggable import Loggable


class EmbeddingQueryExecutor(Loggable):
    """Handles embedding generation and batch processing.

    This class is responsible for:
    - Generating embeddings using different providers (OpenAI, HuggingFace, Cohere)
    - Managing batch processing for efficiency
    - Handling provider-specific configurations
    - Error classification and handling
    """

    def __init__(
        self,
        model: str | None = None,
        batch_size: int = 100,
    ):
        """Initialize the embedding query executor.

        Args:
            model: Optional model name for embeddings
            batch_size: Batch size for processing multiple texts
        """
        super().__init__()
        self._model = model
        self._batch_size = batch_size
        self._provider_configs = {}
        self._initialized = False

        # Provider clients (initialized lazily)
        self._openai_client = None
        self._huggingface_model = None
        self._cohere_client = None

    @property
    def model(self) -> str | None:
        """Get the current model."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set the current model."""
        self._model = value

    @property
    def batch_size(self) -> int:
        """Get the batch size."""
        return self._batch_size

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        """Set the batch size."""
        self._batch_size = value

    async def initialize(self, provider_configs: dict[str, Any]) -> None:
        """Initialize the executor with provider configurations.

        Args:
            provider_configs: Provider-specific configurations
        """
        if self._initialized:
            return

        self._provider_configs = provider_configs
        self.debug(f"Initializing EmbeddingQueryExecutor with configs: {list(provider_configs.keys())}")

        # Initialize providers based on available configurations
        await self._initialize_providers()

        self._initialized = True
        self.debug("EmbeddingQueryExecutor initialized successfully")

    async def _initialize_providers(self) -> None:
        """Initialize provider clients based on available configurations."""
        if "openai" in self._provider_configs:
            await self._initialize_openai()

        if "huggingface" in self._provider_configs:
            await self._initialize_huggingface()

        if "cohere" in self._provider_configs:
            await self._initialize_cohere()

    async def _initialize_openai(self) -> None:
        """Initialize OpenAI client."""
        try:
            import openai

            config = self._provider_configs["openai"]
            api_key = config.get("api_key")

            if not api_key:
                self.warning("OpenAI API key not found in configuration")
                return

            self._openai_client = openai.AsyncOpenAI(api_key=api_key)
            self.debug("OpenAI client initialized successfully")

        except ImportError:
            self.warning("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            self.error(f"Failed to initialize OpenAI client: {e}")

    async def _initialize_huggingface(self) -> None:
        """Initialize HuggingFace model."""
        try:
            from sentence_transformers import SentenceTransformer

            if not self._model or ":" not in self._model:
                self.warning("Invalid HuggingFace model format")
                return

            model_name = self._model.split(":", 1)[1]

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self._huggingface_model = await loop.run_in_executor(None, lambda: SentenceTransformer(model_name))

            self.debug(f"HuggingFace model {model_name} initialized successfully")

        except ImportError:
            self.warning("sentence-transformers library not installed. Install with: pip install sentence-transformers")
        except Exception as e:
            self.error(f"Failed to initialize HuggingFace model: {e}")

    async def _initialize_cohere(self) -> None:
        """Initialize Cohere client."""
        try:
            import cohere

            config = self._provider_configs["cohere"]
            api_key = config.get("api_key")

            if not api_key:
                self.warning("Cohere API key not found in configuration")
                return

            self._cohere_client = cohere.AsyncClient(api_key=api_key)
            self.debug("Cohere client initialized successfully")

        except ImportError:
            self.warning("Cohere library not installed. Install with: pip install cohere")
        except Exception as e:
            self.error(f"Failed to initialize Cohere client: {e}")

    async def generate_embeddings(self, texts: list[str], provider_configs: dict[str, Any] | None = None) -> list[list[float]]:
        """Generate embeddings for input texts.

        Args:
            texts: List of texts to embed
            provider_configs: Optional provider configurations (for runtime override)

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not self._initialized:
            if provider_configs:
                await self.initialize(provider_configs)
            else:
                raise EmbeddingError("Executor not initialized")

        if not texts:
            return []

        if len(texts) == 1:
            # Single text - no batching needed
            return await self._generate_single_batch(texts)
        else:
            # Multiple texts - use batching
            return await self._generate_batched(texts)

    async def _generate_batched(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings with batching for efficiency.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            batch_embeddings = await self._generate_single_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def _generate_single_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a single batch of texts.

        Args:
            texts: Batch of texts to embed

        Returns:
            List of embedding vectors for the batch

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not self._model:
            raise EmbeddingError("No model specified for embedding generation")

        provider = self._model.split(":", 1)[0]

        if provider == "openai":
            return await self._generate_openai_embeddings(texts)
        elif provider == "huggingface":
            return await self._generate_huggingface_embeddings(texts)
        elif provider == "cohere":
            return await self._generate_cohere_embeddings(texts)
        elif provider == "mock":
            return await self._generate_mock_embeddings(texts)
        else:
            raise EmbeddingProviderError(f"Unsupported provider: {provider}")

    async def _generate_openai_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API.

        Args:
            texts: Texts to embed

        Returns:
            List of embedding vectors
        """
        if not self._openai_client:
            raise EmbeddingProviderError("OpenAI client not initialized")

        try:
            model_name = self._model.split(":", 1)[1] if ":" in self._model else "text-embedding-3-small"

            response = await self._openai_client.embeddings.create(model=model_name, input=texts, encoding_format="float")

            return [embedding.embedding for embedding in response.data]

        except Exception as e:
            if "unauthorized" in str(e).lower() or "authentication" in str(e).lower():
                raise EmbeddingAuthenticationError(f"OpenAI authentication failed: {e}")
            else:
                raise EmbeddingProviderError(f"OpenAI embedding generation failed: {e}")

    async def _generate_huggingface_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using HuggingFace model.

        Args:
            texts: Texts to embed

        Returns:
            List of embedding vectors
        """
        if not self._huggingface_model:
            raise EmbeddingProviderError("HuggingFace model not initialized")

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, lambda: self._huggingface_model.encode(texts, convert_to_tensor=False))

            # Convert numpy arrays to lists
            return [embedding.tolist() for embedding in embeddings]

        except Exception as e:
            raise EmbeddingProviderError(f"HuggingFace embedding generation failed: {e}")

    async def _generate_cohere_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Cohere API.

        Args:
            texts: Texts to embed

        Returns:
            List of embedding vectors
        """
        if not self._cohere_client:
            raise EmbeddingProviderError("Cohere client not initialized")

        try:
            model_name = self._model.split(":", 1)[1] if ":" in self._model else "embed-english-v2.0"

            response = await self._cohere_client.embed(texts=texts, model=model_name, input_type="search_document")

            return response.embeddings

        except Exception as e:
            if "unauthorized" in str(e).lower() or "authentication" in str(e).lower():
                raise EmbeddingAuthenticationError(f"Cohere authentication failed: {e}")
            else:
                raise EmbeddingProviderError(f"Cohere embedding generation failed: {e}")

    async def _generate_mock_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings for testing.

        Args:
            texts: Texts to embed

        Returns:
            List of mock embedding vectors
        """
        # Generate deterministic mock embeddings based on text hash
        embeddings = []
        for text in texts:
            # Simple hash-based mock embedding (384 dimensions)
            text_hash = hash(text)
            embedding = [(text_hash + i) % 1000 / 1000.0 for i in range(384)]
            embeddings.append(embedding)

        self.debug(f"Generated mock embeddings for {len(texts)} texts")
        return embeddings

    async def cleanup(self) -> None:
        """Cleanup embedding executor resources."""
        # Close any open connections
        if self._openai_client:
            await self._openai_client.close()

        if self._cohere_client:
            await self._cohere_client.close()

        # Clear model references
        self._huggingface_model = None
        self._initialized = False

        self.debug("EmbeddingQueryExecutor cleaned up")

    def get_supported_models(self) -> dict[str, list[str]]:
        """Get supported models by provider.

        Returns:
            Dictionary mapping providers to their supported models
        """
        return {
            "openai": ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
            "huggingface": ["BAAI/bge-small-en-v1.5", "sentence-transformers/all-MiniLM-L6-v2", "sentence-transformers/all-mpnet-base-v2"],
            "cohere": ["embed-english-v2.0", "embed-multilingual-v2.0"],
        }
