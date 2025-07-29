"""Embedding resource module for Dana.

This module provides a unified interface for embedding generation across
different providers (OpenAI, HuggingFace, Cohere) with flexible configuration
and automatic model selection. It also includes simple LlamaIndex integration.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .embedding_resource import EmbeddingResource
from .embedding_configuration_manager import EmbeddingConfigurationManager
from .embedding_query_executor import EmbeddingQueryExecutor

# Simple LlamaIndex integration
from .llamaindex_embedding_resource import (
    create_llamaindex_embedding,
    setup_llamaindex,
    LlamaIndexEmbeddingResource,
    get_embedding_model,
    RAGEmbeddingResource,  # Backward compatibility alias
)

__all__ = [
    # Core embedding system
    "EmbeddingResource",
    "EmbeddingConfigurationManager",
    "EmbeddingQueryExecutor",
    # Simple LlamaIndex integration
    "create_llamaindex_embedding",
    "setup_llamaindex",
    "LlamaIndexEmbeddingResource",
    "get_embedding_model",
    "RAGEmbeddingResource",
]
