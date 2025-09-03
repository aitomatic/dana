"""Embedding resource module for Dana.

This module provides a unified interface for embedding generation across
different providers (OpenAI, HuggingFace, Cohere) with flexible configuration
and automatic model selection. It also includes simple LlamaIndex integration.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .embedding_resource import EmbeddingResource
from .embedding_query_executor import EmbeddingQueryExecutor

# Simple LlamaIndex integration
from .embedding_integrations import (
    get_embedding_model,
    RAGEmbeddingResource,  # Backward compatibility alias
    EmbeddingFactory,
    get_default_embedding_model
)

__all__ = [
    # Core embedding system
    "EmbeddingResource",
    "EmbeddingQueryExecutor",
    "get_embedding_model",
    "get_default_embedding_model",
    "RAGEmbeddingResource",
    "EmbeddingFactory",
]
