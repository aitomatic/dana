"""Knowledge base resource implementation."""

from typing import Dict, Any, Optional, List
from opendxa.base.resource import ResourceResponse
from opendxa.base.resource.storage_backed_resource import StorageBackedResource, KnowledgeStorageEntry
from datetime import datetime
import uuid
from dataclasses import dataclass, field

@dataclass
class KnowledgeEntry(KnowledgeStorageEntry):
    """A single knowledge entry.
    
    This extends KnowledgeStorageEntry with knowledge-specific fields.
    """
    validated_at: float = field(default_factory=lambda: datetime.now().timestamp())

class KnowledgeBaseResource(StorageBackedResource):
    """Resource for structured knowledge storage and retrieval."""
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize knowledge base resource.
        
        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration including:
                - categories: List of knowledge categories
                - tags: List of available tags
                - confidence_threshold: Minimum confidence for retrieval (default: 0.7)
        """
        super().__init__(name, description, config)
        self.categories = config.get("categories", []) if config else []
        self.tags = config.get("tags", []) if config else []
        self.confidence_threshold = config.get("confidence_threshold", 0.7) if config else 0.7
        
    async def store(
        self,
        content: Any,
        metadata: Optional[Dict] = None
    ) -> ResourceResponse:
        """Store knowledge with validation.
        
        Args:
            content: The knowledge content to store
            metadata: Optional metadata including category, tags, and confidence
            
        Returns:
            ResourceResponse with success status and stored entry details
        """
        try:
            # Extract knowledge-specific fields from metadata
            category = metadata.pop("category") if metadata and "category" in metadata else None
            tags = metadata.pop("tags") if metadata and "tags" in metadata else []
            confidence = metadata.pop("confidence", 1.0) if metadata else 1.0
            
            # Validate category and tags
            if category and category not in self.categories:
                return ResourceResponse(
                    success=False,
                    error=f"Invalid category: {category}"
                )
                
            invalid_tags = [tag for tag in tags if tag not in self.tags]
            if invalid_tags:
                return ResourceResponse(
                    success=False,
                    error=f"Invalid tags: {invalid_tags}"
                )
                
            # Create knowledge entry
            entry = KnowledgeEntry(
                content=content,
                category=category,
                tags=tags,
                confidence=confidence,
                metadata=metadata or {}
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
        limit: Optional[int] = None,
        confidence_threshold: Optional[float] = None
    ) -> ResourceResponse:
        """Retrieve knowledge with confidence scoring.
        
        Args:
            entry_id: Optional specific entry ID to retrieve
            query: Optional query parameters for filtering
            limit: Optional maximum number of results
            confidence_threshold: Optional minimum confidence score
            
        Returns:
            ResourceResponse with success status and matching knowledge entries
        """
        try:
            # If entry_id is provided, use parent's retrieve
            if entry_id:
                return await super().retrieve(entry_id)
                
            # Otherwise use knowledge-specific retrieval
            threshold = confidence_threshold or self.confidence_threshold
            matches = self._filter_knowledge(query or {})
            
            # Score matches based on relevance
            scored_matches = []
            for knowledge in matches:
                score = self._calculate_relevance_score(knowledge, query or {})
                if score >= threshold:
                    scored_matches.append((knowledge, score))
                    
            # Sort by score
            scored_matches.sort(key=lambda x: x[1], reverse=True)
            
            # Apply limit
            if limit:
                scored_matches = scored_matches[:limit]
                
            return ResourceResponse(
                success=True,
                content={
                    "knowledge": [
                        {
                            "content": know.content,
                            "category": know.category,
                            "tags": know.tags,
                            "confidence": know.confidence,
                            "metadata": know.metadata
                        }
                        for know, score in scored_matches
                    ]
                }
            )
        except Exception as e:
            return ResourceResponse(success=False, error=str(e))
            
    def _filter_knowledge(self, query: Dict) -> List[KnowledgeEntry]:
        """Filter knowledge entries based on query conditions."""
        matches = []
        for entry in self._storage.values():
            if isinstance(entry, KnowledgeEntry) and self._matches_query(entry, query):
                matches.append(entry)
        return matches
            
    def _matches_query(self, knowledge: KnowledgeEntry, query: Dict) -> bool:
        """Check if knowledge matches query conditions."""
        if "category" in query and knowledge.category != query["category"]:
            return False
        if "tags" in query and not all(tag in knowledge.tags for tag in query["tags"]):
            return False
        return True
            
    def _calculate_relevance_score(self, knowledge: KnowledgeEntry, query: Dict) -> float:
        """Calculate relevance score for knowledge based on query."""
        score = 0.0
        
        # Category match
        if "category" in query and knowledge.category == query["category"]:
            score += 0.3
            
        # Tag matches
        if "tags" in query:
            matching_tags = set(query["tags"]) & set(knowledge.tags)
            score += 0.2 * len(matching_tags) / len(query["tags"])
            
        # Content relevance (simplified)
        if "content" in query:
            # This is a simplified version - in practice you'd want more sophisticated matching
            if isinstance(knowledge.content, str) and isinstance(query["content"], str):
                if query["content"].lower() in knowledge.content.lower():
                    score += 0.5
                    
        return min(1.0, score)
        
    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Handle resource queries.
        
        Args:
            request: Query request including operation and parameters
            
        Returns:
            ResourceResponse with success status and query results
        """
        operation = request.get("operation", "retrieve")
        
        if operation == "store":
            return await self.store(
                request.get("content"),
                request.get("metadata")
            )
        if operation == "retrieve":
            return await self.retrieve(
                request.get("entry_id"),
                request.get("query"),
                request.get("limit"),
                request.get("confidence_threshold")
            )
        return ResourceResponse(
            success=False,
            error=f"Unknown operation: {operation}"
        ) 