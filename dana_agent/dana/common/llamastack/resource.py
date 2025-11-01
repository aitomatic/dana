"""
LlamaStack VectorIO Resource

A Dana Resource that wraps LlamaStack's VectorIO API for vector database access.
This module USES LlamaStack's VectorIO API and converts to Dana Resource format.
"""

from typing import Any

import structlog

from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource

from .client import LlamaStackClientManager


logger = structlog.get_logger()


class VectorIOResource(BaseResource):
    """
    Dana Resource that wraps LlamaStack's VectorIO API.

    Provides access to vector databases via LlamaStack's VectorIO API.
    This resource converts LlamaStack VectorIO chunks to Dana Resource format.
    """

    def __init__(self, vector_db_id: str, **kwargs):
        """
        Initialize VectorIO Resource.

        Args:
            vector_db_id: Vector database identifier
            **kwargs: Additional arguments for BaseResource
        """
        super().__init__(
            resource_type="vectorio",
            resource_id=vector_db_id,
            **kwargs,
        )
        self.vector_db_id = vector_db_id
        self.client = LlamaStackClientManager.get_client()

        logger.info(
            "VectorIOResource initialized",
            vector_db_id=vector_db_id,
        )

    def _convert_chunk_to_resource_data(self, chunk: dict[str, Any]) -> dict[str, Any]:
        """
        Convert a LlamaStack VectorIO chunk to Dana Resource-compatible format.

        Args:
            chunk: Chunk data from LlamaStack VectorIO API

        Returns:
            Resource data in Dana format
        """
        # Extract chunk content
        content = chunk.get("content", chunk.get("text", chunk.get("chunk", "")))
        if isinstance(content, dict):
            content = content.get("text", content.get("content", str(content)))

        # Extract metadata
        metadata = chunk.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        # Extract similarity score if available
        similarity = chunk.get("similarity", chunk.get("score", None))

        # Build resource data
        resource_data = {
            "content": str(content),
            "metadata": {
                **metadata,
                "chunk_id": chunk.get("chunk_id", chunk.get("id")),
                "similarity": similarity,
                "llamastack_chunk": chunk,  # Preserve original for debugging
            },
        }

        return resource_data

    async def _query_vector_io(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Internal method to call LlamaStack VectorIO API.

        Args:
            query: Search query string
            params: Additional query parameters

        Returns:
            List of chunks from VectorIO API
        """
        params = params or {}

        if self.client and hasattr(self.client, "vector_io"):
            result = await self.client.vector_io.query_chunks(
                vector_db_id=self.vector_db_id,
                query=query,
                params=params,
            )
            chunks = result.get("chunks", result.get("results", [])) if isinstance(result, dict) else []
        else:
            # Fallback: return empty if API not available
            logger.warning("LlamaStack VectorIO API not available, returning empty results")
            chunks = []

        return chunks

    @tool_use
    async def query(self, query: str, top_k: int = 5, **kwargs) -> list[dict[str, Any]]:
        """
        Query the vector database for relevant chunks.

        This method searches the vector database for chunks similar to the query
        and returns them in Dana Resource format.

        Args:
            query: Search query string
            top_k: Number of results to return (default: 5)
            **kwargs: Additional query parameters (e.g., similarity_threshold)

        Returns:
            List of chunk data in Dana Resource-compatible format, each with:
            - content: Chunk text content
            - metadata: Chunk metadata including chunk_id, similarity, etc.
        """
        try:
            params = {"top_k": top_k, **kwargs}

            # Call LlamaStack VectorIO API
            chunks = await self._query_vector_io(query, params=params)

            # Convert chunks to Dana Resource format
            resource_chunks = [self._convert_chunk_to_resource_data(chunk) for chunk in chunks]

            logger.info(
                "Queried vector database",
                vector_db_id=self.vector_db_id,
                query_length=len(query),
                chunk_count=len(resource_chunks),
            )
            return resource_chunks
        except Exception as e:
            logger.error("Failed to query vector database", vector_db_id=self.vector_db_id, error=str(e))
            raise
