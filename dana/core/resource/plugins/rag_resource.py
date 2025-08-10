"""
RAG (Retrieval Augmented Generation) Resource

Provides document retrieval and analysis capabilities for Dana.
Migrated from core to stdlib as a plugin.
Now uses the system resource bridge for production-ready RAG functionality.
"""

import os
from dataclasses import dataclass, field
from typing import Any

from dana.common.types import BaseRequest, BaseResponse
from dana.core.resource import BaseResource, ResourceState
from dana.core.resource.system_bridge import RAGResourceBridge


@dataclass
class RAGResource(BaseResource):
    """RAG (Retrieval Augmented Generation) resource."""

    kind: str = "rag"
    sources: list[str] = field(default_factory=list)
    reranking: bool = False
    chunk_size: int = 1024
    chunk_overlap: int = 256
    embedding_model: str = "default"
    cache_dir: str = ".cache/rag"

    # Bridge to system resource
    _bridge: RAGResourceBridge | None = field(default=None, init=False)

    # Internal state (for fallback mode)
    _chunks: list[str] = field(default_factory=list, init=False)
    _embeddings: list[list[float]] = field(default_factory=list, init=False)

    def initialize(self) -> bool:
        """Initialize RAG system."""
        if not self.sources:
            print(f"Warning: No sources provided for RAG resource '{self.name}'")
            return False

        print(f"Initializing RAG resource '{self.name}' with {len(self.sources)} sources")

        # Try to use system resource bridge first
        try:
            self._bridge = RAGResourceBridge(
                name=f"{self.name}_bridge",
                sources=self.sources,
                cache_dir=self.cache_dir,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
            if self._bridge.initialize():
                self.state = ResourceState.RUNNING
                self.capabilities = self._bridge.capabilities
                print("RAG resource initialized with system bridge")
                return True
            else:
                print("Failed to initialize RAG bridge, falling back to basic implementation")
        except Exception as e:
            print(f"Failed to create RAG bridge: {e}, falling back to basic implementation")

        # Fallback to basic implementation
        for source in self.sources:
            if os.path.exists(source):
                self._process_document(source)
            else:
                print(f"Warning: Source not found: {source}")

        if not self._chunks:
            print("No documents were successfully processed")
            return False

        self.state = ResourceState.RUNNING
        self.capabilities = ["query", "search", "summarize"]
        print(f"RAG resource initialized with {len(self._chunks)} chunks (fallback mode)")
        return True

    def _process_document(self, filepath: str):
        """Process a document into chunks."""
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            # Simple chunking
            for i in range(0, len(content), self.chunk_size - self.chunk_overlap):
                chunk = content[i : i + self.chunk_size]
                if chunk:
                    self._chunks.append(chunk)
                    # Mock embedding
                    self._embeddings.append([0.1] * 384)
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    def cleanup(self) -> bool:
        """Clean up RAG resources."""
        # Clean up bridge if it exists
        if self._bridge:
            self._bridge.cleanup()
            self._bridge = None

        # Clean up fallback state
        self._chunks.clear()
        self._embeddings.clear()
        self.state = ResourceState.TERMINATED
        return True

    def query(self, request: Any) -> Any:
        """Query RAG system."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"RAG resource {self.name} not running")

        # Use bridge if available
        if self._bridge:
            return self._bridge.query(request)

        # Fallback to basic implementation
        if isinstance(request, str):
            query_text = request
        elif isinstance(request, dict):
            query_text = request.get("query", "")
        elif isinstance(request, BaseRequest):
            query_text = request.arguments.get("query", "")
        else:
            return BaseResponse(success=False, error="Invalid request format")

        if not query_text:
            return BaseResponse(success=False, error="No query provided")

        # Simple search - return top chunks containing query terms
        results = []
        query_lower = query_text.lower()

        for i, chunk in enumerate(self._chunks[:10]):  # Limit to first 10 for demo
            if any(term in chunk.lower() for term in query_lower.split()):
                results.append(
                    {
                        "chunk_id": i,
                        "text": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                        "relevance": 0.8,  # Mock relevance score
                    }
                )

        if not results:
            # Return some chunks anyway
            results = [{"chunk_id": 0, "text": self._chunks[0][:200] if self._chunks else "No content", "relevance": 0.5}]

        response = {
            "query": query_text,
            "results": results[:3],  # Top 3 results
            "total_chunks": len(self._chunks),
            "sources": len(self.sources),
        }

        if isinstance(request, BaseRequest):
            return BaseResponse(success=True, content=response)
        return {"success": True, **response}

    def get_stats(self) -> dict[str, Any]:
        """Get RAG statistics."""
        return {
            "name": self.name,
            "kind": self.kind,
            "state": self.state.value,
            "sources": len(self.sources),
            "chunks": len(self._chunks),
            "chunk_size": self.chunk_size,
            "embedding_model": self.embedding_model,
            "capabilities": self.capabilities,
        }
