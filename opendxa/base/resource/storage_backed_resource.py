"""Base storage-backed resource implementation."""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from opendxa.base.resource import BaseResource, ResourceResponse

@dataclass
class StorageEntry:
    """Base class for all storage entries.
    
    This is the minimal interface that all storage entries must implement.
    Subclasses should extend this with domain-specific fields.
    """
    content: Any
    metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())

@dataclass
class KnowledgeStorageEntry(StorageEntry):
    """Base class for knowledge-related storage entries.
    
    This extends StorageEntry with fields common to all knowledge entries.
    """
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    confidence: float = 1.0

@dataclass
class MemoryStorageEntry(StorageEntry):
    """Base class for memory-related storage entries.
    
    This extends StorageEntry with fields common to all memory entries.
    """
    importance: float = 1.0
    context: Dict = field(default_factory=dict)
    last_accessed: float = field(default_factory=lambda: datetime.now().timestamp())

class StorageBackedResource(BaseResource):
    """Base class for all storage-backed resources.
    
    This provides the core storage and retrieval functionality.
    Subclasses should implement domain-specific storage and retrieval logic.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize storage-backed resource.
        
        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration
        """
        super().__init__(name, description, config)
        self._storage: Dict[str, StorageEntry] = {}
        
    async def store(
        self,
        content: Any,
        metadata: Optional[Dict] = None
    ) -> ResourceResponse:
        """Store content with optional metadata.
        
        Args:
            content: The content to store
            metadata: Optional metadata to associate with the content
            
        Returns:
            ResourceResponse with success status and stored entry details
        """
        try:
            entry_id = str(uuid.uuid4())
            entry = StorageEntry(
                content=content,
                metadata=metadata or {}
            )
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
        entry_id: str
    ) -> ResourceResponse:
        """Retrieve content by ID.
        
        Args:
            entry_id: The ID of the entry to retrieve
            
        Returns:
            ResourceResponse with success status and retrieved content
        """
        try:
            if entry_id not in self._storage:
                return ResourceResponse(success=False, error="Entry not found")
            entry = self._storage[entry_id]
            return ResourceResponse(
                success=True,
                content={
                    "content": entry.content,
                    "metadata": entry.metadata,
                    "created_at": entry.created_at
                }
            )
        except Exception as e:
            return ResourceResponse(success=False, error=str(e))
            
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
                request.get("metadata")
            )
        if operation == "retrieve":
            return await self.retrieve(request.get("entry_id"))
            
        return ResourceResponse(
            success=False,
            error=f"Unknown operation: {operation}"
        ) 