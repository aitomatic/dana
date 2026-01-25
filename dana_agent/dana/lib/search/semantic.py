"""Semantic search engine using LlamaIndex embeddings."""

import hashlib
import os
from pathlib import Path
from typing import Any

from llama_index.core import (
    Document,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.settings import Settings


def get_embedding_model() -> Any:
    """Get embedding model based on available API keys.

    Priority:
    1. OpenAI (if OPENAI_API_KEY is set)
    2. HuggingFace (local, no API key required)
    """
    if os.getenv("OPENAI_API_KEY"):
        from llama_index.embeddings.openai import OpenAIEmbedding

        return OpenAIEmbedding(model="text-embedding-3-small")

    # Fallback to HuggingFace (local)
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")


class SemanticSearchEngine:
    """Vector similarity search using LlamaIndex.

    Caches index to disk for fast startup. Cache is keyed by:
    - cache_name (e.g., "asset_types")
    - embedding model name (to invalidate when model changes)
    """

    DEFAULT_CACHE_DIR = Path.home() / ".cache" / "semantic_search"

    def __init__(
        self,
        corpus: list[str],
        cache_dir: Path | str | None = None,
        cache_name: str = "default",
    ):
        self._corpus = corpus
        self._cache_dir = Path(cache_dir) if cache_dir else self.DEFAULT_CACHE_DIR
        self._index: VectorStoreIndex | None = None

        # Get embedding model and its name for cache key
        self._embed_model = get_embedding_model()
        self._model_name = self._get_model_name()

        # Cache dir includes model name to invalidate on model change
        model_safe = self._model_name.replace(":", "_").replace("/", "_")
        self._persist_dir = self._cache_dir / f"{cache_name}_{model_safe}"

        # Configure LlamaIndex
        Settings.embed_model = self._embed_model

        # Build text-to-index mapping (strip for consistent matching)
        self._text_to_idx = {text.strip(): i for i, text in enumerate(corpus)}

    def _get_model_name(self) -> str:
        """Extract model name from embedding model."""
        if hasattr(self._embed_model, "model_name"):
            return self._embed_model.model_name
        if hasattr(self._embed_model, "model"):
            return self._embed_model.model
        return "unknown"

    @staticmethod
    def _text_to_doc_id(text: str) -> str:
        """Generate stable document ID from text hash."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _load_or_build_index(self, force_rebuild: bool = False) -> VectorStoreIndex:
        """Load index from cache or build new one."""
        if not force_rebuild and self._persist_dir.exists():
            try:
                storage_context = StorageContext.from_defaults(persist_dir=str(self._persist_dir))
                return load_index_from_storage(storage_context)
            except Exception:
                pass  # Fall through to rebuild

        # Build new index with hash-based doc IDs
        documents = [Document(text=text, doc_id=self._text_to_doc_id(text)) for text in self._corpus]
        index = VectorStoreIndex.from_documents(documents)

        # Persist to disk
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        index.storage_context.persist(persist_dir=str(self._persist_dir))

        return index

    def search(
        self,
        query: str,
        n: int = 10,
        force_rebuild: bool = False,
    ) -> list[tuple[int, float, str]]:
        """Search for similar items.

        Args:
            query: Search query text.
            n: Number of results to return.
            force_rebuild: If True, rebuild the index from scratch.

        Returns:
            List of (corpus_index, score, text) tuples sorted by relevance.
        """
        if self._index is None or force_rebuild:
            self._index = self._load_or_build_index(force_rebuild)

        retriever = self._index.as_retriever(similarity_top_k=n)
        results = retriever.retrieve(query)

        output = []
        for node in results:
            text = node.node.text
            # Map text back to corpus index (strip for consistent matching)
            idx = self._text_to_idx.get(text.strip(), -1)
            output.append((idx, node.score, text))

        return output
