"""
Storage Types for KNOWS Knowledge Organizations

Defines the different storage systems for different data types.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class StorageType(Enum):
    """Storage organization types."""

    RELATIONAL = "Relational"
    SEMI_STRUCTURED = "Semi-structured"
    VECTOR = "Vector"
    TIME_SERIES = "Time Series"


class StorageInterface(ABC):
    """Abstract interface for storage systems."""

    @abstractmethod
    def store(self, key: str, data: Any) -> bool:
        """Store data with given key."""
        pass

    @abstractmethod
    def retrieve(self, key: str) -> Any | None:
        """Retrieve data with given key."""
        pass

    @abstractmethod
    def query(self, query_params: dict[str, Any]) -> list[Any]:
        """Query data based on parameters."""
        pass


class RelationalStore(StorageInterface):
    """Relational store for facts, rules, reference data."""

    def __init__(self):
        self.data = {}
        self.indexes = {}

    def store(self, key: str, data: Any) -> bool:
        """Store structured data."""
        self.data[key] = data
        # Update indexes for fast lookup
        if isinstance(data, dict):
            for field, value in data.items():
                if field not in self.indexes:
                    self.indexes[field] = {}
                if value not in self.indexes[field]:
                    self.indexes[field][value] = []
                self.indexes[field][value].append(key)
        return True

    def retrieve(self, key: str) -> Any | None:
        """Retrieve data by key."""
        return self.data.get(key)

    def query(self, query_params: dict[str, Any]) -> list[Any]:
        """Query using field-value pairs."""
        results = []
        for key, data in self.data.items():
            if isinstance(data, dict):
                match = True
                for field, value in query_params.items():
                    if data.get(field) != value:
                        match = False
                        break
                if match:
                    results.append(data)
        return results


class SemiStructuredStore(StorageInterface):
    """Semi-structured store for workflows, procedures, decision trees."""

    def __init__(self):
        self.documents = {}
        self.tags = {}

    def store(self, key: str, data: Any) -> bool:
        """Store document with tags."""
        self.documents[key] = data
        if isinstance(data, dict) and "tags" in data:
            for tag in data["tags"]:
                if tag not in self.tags:
                    self.tags[tag] = []
                self.tags[tag].append(key)
        return True

    def retrieve(self, key: str) -> Any | None:
        """Retrieve document by key."""
        return self.documents.get(key)

    def query(self, query_params: dict[str, Any]) -> list[Any]:
        """Query by tags or content."""
        results = []
        for key, doc in self.documents.items():
            if "tags" in query_params:
                if isinstance(doc, dict) and "tags" in doc:
                    if any(tag in doc["tags"] for tag in query_params["tags"]):
                        results.append(doc)
            elif "content" in query_params:
                if isinstance(doc, dict) and "content" in doc:
                    if query_params["content"].lower() in doc["content"].lower():
                        results.append(doc)
        return results


class VectorStore(StorageInterface):
    """Vector store for similarity search, pattern recognition."""

    def __init__(self):
        self.vectors = {}
        self.embeddings = {}

    def store(self, key: str, data: Any) -> bool:
        """Store vector with metadata."""
        self.vectors[key] = data
        # Simulate vector embedding (in real implementation, use actual embeddings)
        if isinstance(data, dict) and "content" in data:
            # Simple hash-based embedding for simulation
            embedding = hash(data["content"]) % 1000
            self.embeddings[key] = embedding
        return True

    def retrieve(self, key: str) -> Any | None:
        """Retrieve vector by key."""
        return self.vectors.get(key)

    def query(self, query_params: dict[str, Any]) -> list[Any]:
        """Query by similarity."""
        results = []
        if "similarity" in query_params:
            query_embedding = hash(query_params["similarity"]) % 1000
            for key, embedding in self.embeddings.items():
                # Simple similarity calculation (in real implementation, use cosine similarity)
                similarity = 1 - abs(query_embedding - embedding) / 1000
                if similarity > 0.7:  # Threshold for similarity
                    results.append(self.vectors[key])
        return results


class TimeSeriesStore(StorageInterface):
    """Time series store for temporal patterns, trends, sequences."""

    def __init__(self):
        self.series = {}
        self.timestamps = {}

    def store(self, key: str, data: Any) -> bool:
        """Store time series data."""
        from datetime import datetime

        timestamp = datetime.now()
        self.series[key] = data
        self.timestamps[key] = timestamp
        return True

    def retrieve(self, key: str) -> Any | None:
        """Retrieve time series by key."""
        return self.series.get(key)

    def query(self, query_params: dict[str, Any]) -> list[Any]:
        """Query by time range or patterns."""
        results = []
        from datetime import datetime, timedelta

        if "time_range" in query_params:
            hours = query_params["time_range"]
            cutoff_time = datetime.now() - timedelta(hours=hours)
            for key, timestamp in self.timestamps.items():
                if timestamp > cutoff_time:
                    results.append(self.series[key])
        elif "pattern" in query_params:
            # Simple pattern matching for simulation
            pattern = query_params["pattern"]
            for key, data in self.series.items():
                if isinstance(data, dict) and "content" in data:
                    if pattern.lower() in data["content"].lower():
                        results.append(data)
        return results


class KnowledgeStorage:
    """Main storage manager for KNOWS."""

    def __init__(self):
        self.stores = {
            StorageType.RELATIONAL: RelationalStore(),
            StorageType.SEMI_STRUCTURED: SemiStructuredStore(),
            StorageType.VECTOR: VectorStore(),
            StorageType.TIME_SERIES: TimeSeriesStore(),
        }

    def store_knowledge(self, storage_type: StorageType, key: str, data: Any) -> bool:
        """Store knowledge in appropriate storage system."""
        store = self.stores.get(storage_type)
        if store:
            return store.store(key, data)
        return False

    def retrieve_knowledge(self, storage_type: StorageType, key: str) -> Any | None:
        """Retrieve knowledge from storage system."""
        store = self.stores.get(storage_type)
        if store:
            return store.retrieve(key)
        return None

    def query_knowledge(self, storage_type: StorageType, query_params: dict[str, Any]) -> list[Any]:
        """Query knowledge from storage system."""
        store = self.stores.get(storage_type)
        if store:
            return store.query(query_params)
        return []

    def get_all_stores(self) -> dict[StorageType, StorageInterface]:
        """Get all storage systems."""
        return self.stores
