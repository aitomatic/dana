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

from typing import Dict, Any, Optional
from opendxa.base.resource.base_resource import BaseResource, ResourceResponse
from opendxa.base.db.storage import KnowledgeDBStorage
from opendxa.base.db import KnowledgeDBModel

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
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the knowledge base resource.
        
        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration
        """
        super().__init__(name, description, config)
        self._storage = KnowledgeDBStorage(connection_string=config.get("connection_string"))
    
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
    
    async def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> ResourceResponse:
        """Store knowledge in the knowledge base.
        
        Args:
            key: Unique identifier for the knowledge
            value: The knowledge content to store
            metadata: Optional metadata about the knowledge
            
        Returns:
            ResourceResponse indicating success or failure
        """
        try:
            knowledge = KnowledgeDBModel(
                key=key,
                value=value,
                metadata=metadata
            )
            self._storage.store(knowledge)
            return ResourceResponse(success=True, content={"key": key})
        except Exception as e:
            return ResourceResponse.error_response(f"Failed to store knowledge: {str(e)}")
    
    async def retrieve(self, key: Optional[str] = None, query: Optional[str] = None) -> ResourceResponse:
        """Retrieve knowledge from the knowledge base.
        
        Args:
            key: Optional specific key to retrieve
            query: Optional query to filter results
            
        Returns:
            ResourceResponse containing the retrieved knowledge
        """
        try:
            if key:
                result = self._storage.retrieve(key)
            else:
                result = self._storage.retrieve(query=query)
            return ResourceResponse(success=True, content=result)
        except Exception as e:
            return ResourceResponse.error_response(f"Failed to retrieve knowledge: {str(e)}")
    
    async def delete(self, key: str) -> ResourceResponse:
        """Delete knowledge from the knowledge base.
        
        Args:
            key: The key of the knowledge to delete
            
        Returns:
            ResourceResponse indicating success or failure
        """
        try:
            self._storage.delete(key)
            return ResourceResponse(success=True, content={"key": key})
        except Exception as e:
            return ResourceResponse.error_response(f"Failed to delete knowledge: {str(e)}")
    
    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if the resource can handle the request.
        
        Args:
            request: The request to check
            
        Returns:
            True if the resource can handle the request, False otherwise
        """
        return request.get("type") == "knowledge" 