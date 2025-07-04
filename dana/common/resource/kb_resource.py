"""Knowledge Base Resource Module for DXA.

A Knowledge Base in DXA is a structured repository of information that can be stored,
retrieved, and queried. It serves as a foundation for building intelligent systems
by providing persistent storage and efficient access to domain knowledge.

Key Concepts:
    - Knowledge Entry: A single piece of information stored in the knowledge base,
      consisting of a key, value, and optional metadata
    - Metadata: Additional information about knowledge entries that can be used for
      organization, filtering, and context
    - Querying: The ability to retrieve knowledge based on specific criteria or patterns
    - Persistence: Long-term storage of knowledge that survives system restarts

This module implements the knowledge base resource functionality for the DXA system.
It provides the core infrastructure for storing, retrieving, and managing knowledge
in a persistent and queryable manner.

The module contains:
    - KBResource: The main resource class for knowledge base operations
    - Integration with KnowledgeStorage for persistence
    - Support for knowledge metadata and querying

This module is part of the base resource layer and provides the foundation for
knowledge management features in the DXA system.
"""

from typing import Any

from dana.common.db.storage import KnowledgeDBStorage
from dana.common.resource.base_resource import BaseResource
from dana.common.types import BaseResponse


class KBResource(BaseResource):
    """Implementation of the knowledge base resource for DXA.

    This class provides the concrete implementation of knowledge base operations,
    acting as a facade over the underlying storage system. It handles the storage,
    retrieval, and management of knowledge entries while providing a consistent
    API for these operations.

    The resource supports:
    - Storing knowledge with associated metadata
    - Retrieving knowledge by key or query
    - Deleting knowledge entries
    - Resource lifecycle management (initialization and cleanup)

    Attributes:
        name (str): The name of the resource
        description (Optional[str]): Optional description of the resource
        config (Optional[Dict[str, Any]]): Optional configuration parameters
        _storage (KnowledgeStorage): The underlying storage implementation
        _knowledge_base (Dict[str, Dict[str, Any]]): Internal storage for knowledge

    Example:
        >>> storage = KnowledgeStorage()
        >>> kb_resource = KBResource("my_kb", storage)
        >>> await kb_resource.initialize()
        >>>
        >>> # Store knowledge
        >>> response = await kb_resource.store(
        ...     key="fact1",
        ...     value="The sky is blue",
        ...     metadata={"source": "observation"}
        ... )
        >>>
        >>> # Retrieve knowledge
        >>> response = await kb_resource.retrieve(key="fact1")
        >>>
        >>> # Delete knowledge
        >>> response = await kb_resource.delete(key="fact1")
        >>>
        >>> await kb_resource.cleanup()
    """

    def __init__(self, name: str, description: str | None = None, config: dict[str, Any] | None = None):
        """Initialize the knowledge base resource.

        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration
        """
        super().__init__(name, description, config)
        config = config or {}
        connection_string = config.get("connection_string")
        if connection_string is None:
            connection_string = "sqlite:///knowledge.db"  # Default connection string
        self._storage = KnowledgeDBStorage(connection_string=connection_string)
        self._knowledge_base: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize the knowledge base resource."""
        await super().initialize()
        self._storage.initialize()
        self.info(f"Knowledge base resource [{self.name}] initialized")

    async def cleanup(self) -> None:
        """Clean up the knowledge base resource."""
        await super().cleanup()
        self._storage.cleanup()
        self.info(f"Knowledge base resource [{self.name}] cleaned up")

    async def store(self, key: str, value: Any, metadata: dict | None = None) -> BaseResponse:
        """Store knowledge in the knowledge base.

        Args:
            key: The key to store the knowledge under
            value: The value to store
            metadata: Optional metadata about the knowledge

        Returns:
            BaseResponse indicating success or failure
        """
        try:
            self._knowledge_base[key] = {"value": value, "metadata": metadata or {}}
            return BaseResponse(success=True, content={"key": key})
        except Exception as e:
            return BaseResponse(success=False, error=f"Failed to store knowledge: {str(e)}")

    async def retrieve(self, key: str | None = None, query: str | None = None) -> BaseResponse:
        """Retrieve knowledge from the knowledge base.

        Args:
            key: Optional key to retrieve
            query: Optional query string to search for

        Returns:
            BaseResponse containing the retrieved knowledge
        """
        try:
            if key:
                result = self._knowledge_base.get(key)
            else:
                # Simple query implementation - can be enhanced
                result = {k: v for k, v in self._knowledge_base.items() if query and query.lower() in str(v).lower()}
            return BaseResponse(success=True, content=result)
        except Exception as e:
            return BaseResponse(success=False, error=f"Failed to retrieve knowledge: {str(e)}")

    async def delete(self, key: str) -> BaseResponse:
        """Delete knowledge from the knowledge base.

        Args:
            key: The key to delete

        Returns:
            BaseResponse indicating success or failure
        """
        try:
            if key in self._knowledge_base:
                del self._knowledge_base[key]
            return BaseResponse(success=True, content={"key": key})
        except Exception as e:
            return BaseResponse(success=False, error=f"Failed to delete knowledge: {str(e)}")

    def can_handle(self, request: dict[str, Any]) -> bool:
        """Check if the resource can handle the request.

        Args:
            request: The request to check

        Returns:
            True if the resource can handle the request, False otherwise
        """
        return request.get("type") == "knowledge"
