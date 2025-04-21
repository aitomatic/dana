"""Long-term memory resource implementation."""

from typing import Dict, Any, Optional, List
import uuid
from dataclasses import dataclass

from opendxa.base.resource import ResourceResponse
from opendxa.base.resource.storage_backed_resource import StorageBackedResource, MemoryStorageEntry

@dataclass
class LongTermMemoryEntry(MemoryStorageEntry):
    """A single long-term memory entry.
    
    This extends MemoryStorageEntry with long-term memory specific fields.
    """
    decay_rate: float = 0.01  # Slower decay for long-term memories

class LongTermMemoryResource(StorageBackedResource):
    """Resource for long-term memory storage and retrieval."""
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize long-term memory resource.
        
        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration
        """
        super().__init__(name, description, config)
        self.decay_rate = config.get("decay_rate", 0.01) if config else 0.01  # Slower decay for long-term
        
    async def store(
        self,
        content: Any,
        metadata: Optional[Dict] = None,
        importance: float = 1.0,
        context: Optional[Dict] = None
    ) -> ResourceResponse:
        """Store a long-term memory entry.
        
        Args:
            content: The memory content to store
            metadata: Optional metadata to associate with the memory
            importance: Importance score of the memory (default: 1.0)
            context: Optional context information
            
        Returns:
            ResourceResponse with success status and stored entry details
        """
        try:
            entry = LongTermMemoryEntry(
                content=content,
                metadata=metadata or {},
                importance=importance,
                context=context or {}
            )
            entry_id = str(uuid.uuid4())
            self._storage[entry_id] = entry
            return ResourceResponse(
                success=True,
                content={
                    "id": entry_id,
                    "stored_at": entry.created_at
                }
            )
        except Exception as e:
            return ResourceResponse(success=False, error=str(e))
            
    async def retrieve(
        self,
        entry_id: Optional[str] = None,
        query: Optional[Dict] = None,
        limit: Optional[int] = None
    ) -> ResourceResponse:
        """Retrieve long-term memory entries matching query.
        
        Args:
            entry_id: Optional specific entry ID to retrieve
            query: Optional query parameters for filtering
            limit: Optional maximum number of results
            
        Returns:
            ResourceResponse with success status and matching memory entries
        """
        try:
            # If entry_id is provided, use parent's retrieve
            if entry_id:
                return await super().retrieve(entry_id)
                
            # Otherwise use memory-specific retrieval
            matches = self._filter_memories(query or {})
            if limit:
                matches = matches[:limit]
            return ResourceResponse(
                success=True,
                content={
                    "memories": [
                        {
                            "content": mem.content,
                            "timestamp": mem.created_at,
                            "importance": mem.importance,
                            "metadata": mem.metadata,
                            "context": mem.context
                        }
                        for mem in matches
                    ]
                }
            )
        except Exception as e:
            return ResourceResponse(success=False, error=str(e))
            
    def _filter_memories(self, query: Dict) -> List[LongTermMemoryEntry]:
        """Filter memories based on query conditions."""
        matches = []
        for entry in self._storage.values():
            if isinstance(entry, LongTermMemoryEntry) and self._matches_query(entry, query):
                matches.append(entry)
        return matches
        
    def _matches_query(self, memory: LongTermMemoryEntry, query: Dict) -> bool:
        """Check if memory matches query conditions."""
        for key, value in query.items():
            if key in memory.metadata:
                if memory.metadata[key] != value:
                    return False
            elif key in memory.context:
                if memory.context[key] != value:
                    return False
            else:
                return False
        return True
        
    async def query(self, request: Optional[Dict[str, Any]] = None) -> ResourceResponse:
        """Handle resource queries.
        
        Args:
            request: Query request including operation and parameters
            
        Returns:
            ResourceResponse with success status and query results
        """
        request = request or {}
        operation = request.get("operation", "retrieve")
        
        if operation == "store":
            return await self.store(
                request.get("content"),
                request.get("metadata"),
                request.get("importance", 1.0),
                request.get("context")
            )
        if operation == "retrieve":
            return await self.retrieve(
                request.get("entry_id"),
                request.get("query"),
                request.get("limit")
            )
        return ResourceResponse(
            success=False,
            error=f"Unknown operation: {operation}"
        ) 