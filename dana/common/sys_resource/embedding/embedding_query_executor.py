"""Embedding Query Execution Engine for Dana.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
import os
from typing import Any

from dana.common.exceptions import (
    EmbeddingError,
    EmbeddingProviderError,
    EmbeddingAuthenticationError,
)
from dana.common.mixins.loggable import Loggable


class EmbeddingQueryExecutor(Loggable):
    """Handles embedding generation for different providers."""

    def __init__(self, model: str | None = None, batch_size: int = 100):
        """Initialize the embedding query executor."""
        super().__init__()
        self._model = model
        self._batch_size = batch_size
        self._provider_configs = {}
        self._initialized = False

        # Provider clients (lazy initialization)
        self._openai_client = None
        self._huggingface_model = None
        self._cohere_client = None
        self._ollama_client = None

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
        """Initialize the executor with provider configurations."""
        if self._initialized:
            return

        self._provider_configs = provider_configs

        # Initialize relevant provider clients
        if self._model and ":" in self._model:
            provider = self._model.split(":", 1)[0]

            if provider == "openai" and "openai" in provider_configs:
                await self._initialize_openai()
            elif provider in {"ollama", "local"}:
                provider_key = provider if provider in provider_configs else "ollama"
                if provider_key in provider_configs:
                    await self._initialize_ollama(provider_key)
            elif provider == "huggingface" and "huggingface" in provider_configs:
                await self._initialize_huggingface()
            elif provider == "cohere" and "cohere" in provider_configs:
                await self._initialize_cohere()

        self._initialized = True

    async def _initialize_ollama(self, provider_key: str = "ollama") -> None:
        """Initialize Ollama client."""
        try:
            import httpx

            config = self._provider_configs.get(provider_key, {})
            fallback_base_url = (
                config.get("base_url")
                or self._provider_configs.get("ollama", {}).get("base_url")
                or os.getenv("LOCAL_EMBEDDING_BASE_URL")
                or os.getenv("LOCAL_BASE_URL")
                or "http://localhost:11434"
            )
            base_url = fallback_base_url
            
            # Remove trailing slash and ensure proper format
            if base_url.endswith("/"):
                base_url = base_url[:-1]
            
            self._ollama_client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
            self.debug("Ollama client initialized successfully")

        except ImportError:
            self.warning("httpx library not installed. Install with: pip install httpx")
        except Exception as e:
            self.error(f"Failed to initialize Ollama client: {e}")

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
            from sentence_transformers import SentenceTransformer  # type: ignore

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
        """Generate embeddings for input texts."""
        if not self._initialized:
            if provider_configs:
                await self.initialize(provider_configs)
            else:
                raise EmbeddingError("Executor not initialized")

        if not texts:
            return []

        if not self._model:
            raise EmbeddingError("No model specified")

        provider = self._model.split(":", 1)[0]

        # Route to appropriate provider
        if provider == "openai":
            return await self._generate_openai_embeddings(texts)
        elif provider in {"ollama", "local"}:
            return await self._generate_ollama_embeddings(texts)
        elif provider == "huggingface":
            return await self._generate_huggingface_embeddings(texts)
        elif provider == "cohere":
            return await self._generate_cohere_embeddings(texts)
        elif provider == "mock":
            return await self._generate_mock_embeddings(texts)
        else:
            raise EmbeddingProviderError(f"Unsupported provider: {provider}")

    async def _generate_ollama_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Ollama API."""
        if not self._ollama_client:
            raise EmbeddingProviderError("Ollama client not initialized")

        try:
            model_name = self._model.split(":", 1)[1] if self._model and ":" in self._model else "bge-m3:latest"
            
            # Ollama embedding API endpoint
            response = await self._ollama_client.post(
                "/api/embed",
                json={
                    "model": model_name,
                    "input": texts,
                },
            )
            response.raise_for_status()
            result = response.json()

            if isinstance(result, dict):
                if "data" in result and isinstance(result["data"], list):
                    return [item.get("embedding", []) for item in result["data"]]
                if "embedding" in result:
                    embedding_value = result["embedding"]
                    if isinstance(embedding_value, list) and embedding_value and isinstance(embedding_value[0], list):
                        return embedding_value
                    return [embedding_value]

            raise EmbeddingProviderError("Unexpected response format from Ollama embed endpoint")

        except Exception as e:
            if "unauthorized" in str(e).lower() or "authentication" in str(e).lower():
                raise EmbeddingAuthenticationError(f"Ollama authentication failed: {e}")
            else:
                raise EmbeddingProviderError(f"Ollama embedding failed: {e}")

    async def _generate_openai_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API."""
        if not self._openai_client:
            raise EmbeddingProviderError("OpenAI client not initialized")

        try:
            model_name = self._model.split(":", 1)[1] if self._model and ":" in self._model else "text-embedding-3-small"
            response = await self._openai_client.embeddings.create(model=model_name, input=texts, encoding_format="float")
            return [embedding.embedding for embedding in response.data]

        except Exception as e:
            if "unauthorized" in str(e).lower() or "authentication" in str(e).lower():
                raise EmbeddingAuthenticationError(f"OpenAI authentication failed: {e}")
            else:
                raise EmbeddingProviderError(f"OpenAI embedding failed: {e}")

    async def _generate_huggingface_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using HuggingFace model."""
        if not self._huggingface_model:
            raise EmbeddingProviderError("HuggingFace model not initialized")

        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self._huggingface_model.encode(texts, convert_to_tensor=False),  # type: ignore
            )
            return [embedding.tolist() for embedding in embeddings]

        except Exception as e:
            raise EmbeddingProviderError(f"HuggingFace embedding failed: {e}")

    async def _generate_cohere_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Cohere API."""
        if not self._cohere_client:
            raise EmbeddingProviderError("Cohere client not initialized")

        try:
            model_name = self._model.split(":", 1)[1] if self._model and ":" in self._model else "embed-english-v2.0"
            response = await self._cohere_client.embed(texts=texts, model=model_name, input_type="search_document")
            return list(response.embeddings)  # type: ignore

        except Exception as e:
            if "unauthorized" in str(e).lower() or "authentication" in str(e).lower():
                raise EmbeddingAuthenticationError(f"Cohere authentication failed: {e}")
            else:
                raise EmbeddingProviderError(f"Cohere embedding failed: {e}")

    async def _generate_mock_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings for testing."""
        embeddings = []
        for text in texts:
            text_hash = hash(text)
            embedding = [(text_hash + i) % 1000 / 1000.0 for i in range(384)]
            embeddings.append(embedding)
        return embeddings
