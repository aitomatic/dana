"""Memory and state management capability for DXA.

This module provides memory management functionality for DXA agents, including:
- Long-term memory storage with importance-based retention
- Working memory for temporary state
- Memory decay over time
- Importance-based memory filtering
- Context-aware memory retrieval

Classes:
    MemoryEntry: A single memory entry with content, metadata, and importance
    MemoryCapability: Main memory management capability implementation

Example:
    >>> memory = MemoryCapability(max_size=1000, decay_rate=0.1)
    >>> await memory.use({
    ...     "operation": "store",
    ...     "content": "Important observation",
    ...     "importance": 0.8
    ... })
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from ...base.capability.base_capability import BaseCapability
from ...common.exceptions import OpenDXAError, DXAMemoryError

class MemoryEntry(BaseModel):
    """A single memory entry."""
    content: Any = Field(..., description="The content of the memory")
    timestamp: float = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="When the memory was created"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the memory"
    )
    importance: float = Field(
        default=1.0,
        description="Importance of the memory (higher = more important)"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual information for the memory"
    )

class MemoryCapability(BaseCapability):
    """Capability to manage agent's memory and state."""
    
    def __init__(
        self,
        max_size: Optional[int] = None,
        decay_rate: float = 0.1,
        importance_threshold: float = 0.5
    ):
        """Initialize memory capability.
        
        Args:
            max_size: Maximum number of memories to store (None = unlimited)
            decay_rate: Rate at which memory importance decays over time
            importance_threshold: Minimum importance to keep a memory
        """
        super().__init__(
            name="memory",
            description="Memory and state management capability"
        )
        self.max_size = max_size
        self.decay_rate = decay_rate
        self.importance_threshold = importance_threshold
        self._memories: List[MemoryEntry] = []
        self._working_memory: Dict[str, Any] = {}

    async def apply(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Use memory capability.
        
        Args:
            context: Current context including operation details
            **kwargs: Additional arguments including:
                - operation: Type of memory operation
                - content: Content to store (for store operations)
                - query: Query for retrieval operations
                
        Returns:
            Dict containing operation results
        """
        operation = kwargs.get('operation', 'retrieve')
        
        if operation == 'store':
            return await self._store_memory(
                kwargs.get('content'),
                kwargs.get('metadata', {}),
                kwargs.get('importance', 1.0),
                context
            )
        if operation == 'retrieve':
            return await self._retrieve_memories(
                kwargs.get('query', {}),
                kwargs.get('limit')
            )
        if operation == 'update_working':
            return await self._update_working_memory(
                kwargs.get('updates', {})
            )
        if operation == 'clear':
            return await self._clear_memories(
                kwargs.get('filter', {})
            )
        return {
            "success": False,
            "error": f"Unknown operation: {operation}"
        }

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if memory capability can handle the request."""
        return True  # Memory capability can always be used

    async def _store_memory(
        self,
        content: Any,
        metadata: Dict,
        importance: float,
        context: Dict
    ) -> Dict[str, Any]:
        """Store a new memory."""
        try:
            # Create new memory entry
            entry = MemoryEntry(
                content=content,
                metadata=metadata,
                importance=importance,
                context=context
            )
            
            # Add to memories
            self._memories.append(entry)
            
            # Maintain max size if needed
            if self.max_size and len(self._memories) > self.max_size:
                self._cleanup_memories()
            
            return {
                "success": True,
                "stored_at": entry.timestamp
            }
            
        except OpenDXAError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            raise DXAMemoryError(f"Failed to store memory: {str(e)}") from e

    async def _retrieve_memories(
        self,
        query: Dict,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retrieve memories matching query."""
        try:
            # Apply importance decay
            self._apply_decay()
            
            # Filter memories
            matches = [
                mem for mem in self._memories
                if self._matches_query(mem, query)
            ]
            
            # Sort by importance
            matches.sort(key=lambda x: x.importance, reverse=True)
            
            # Apply limit
            if limit:
                matches = matches[:limit]
            
            return {
                "success": True,
                "memories": [
                    {
                        "content": mem.content,
                        "timestamp": mem.timestamp,
                        "importance": mem.importance,
                        "metadata": mem.metadata
                    }
                    for mem in matches
                ]
            }
            
        except OpenDXAError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            raise DXAMemoryError(f"Failed to retrieve memories: {str(e)}") from e

    async def _update_working_memory(
        self,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update working memory."""
        try:
            self._working_memory.update(updates)
            return {
                "success": True,
                "working_memory": self._working_memory
            }
        except OpenDXAError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            raise DXAMemoryError(f"Failed to update working memory: {str(e)}") from e

    async def _clear_memories(
        self,
        filter_dict: Dict
    ) -> Dict[str, Any]:
        """Clear memories matching filter."""
        try:
            initial_count = len(self._memories)
            self._memories = [
                mem for mem in self._memories
                if not self._matches_query(mem, filter_dict)
            ]
            return {
                "success": True,
                "cleared_count": initial_count - len(self._memories)
            }
        except OpenDXAError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            raise DXAMemoryError(f"Failed to clear memories: {str(e)}") from e

    def _cleanup_memories(self):
        """Clean up memories based on importance and size limits."""
        # Remove low importance memories
        self._memories = [
            mem for mem in self._memories
            if mem.importance >= self.importance_threshold
        ]
        
        # If still over max size, remove oldest
        if self.max_size and len(self._memories) > self.max_size:
            # Sort by timestamp and keep only the newest max_size memories
            self._memories.sort(key=lambda x: x.timestamp if x.timestamp is not None else 0)
            self._memories = self._memories[max(0, len(self._memories) - self.max_size):]

    def _apply_decay(self):
        """Apply importance decay to memories."""
        current_time = datetime.now().timestamp()
        for memory in self._memories:
            time_diff = current_time - memory.timestamp
            memory.importance *= (1 - self.decay_rate) ** time_diff

    def _matches_query(self, memory: MemoryEntry, query: Dict) -> bool:
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