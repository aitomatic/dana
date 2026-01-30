"""Semantic memory store using LanceDB.

A persistent, queryable memory store for agents. Supports:
- Storing memories with metadata (source, identity, timestamps)
- Semantic search using vector embeddings
- Metadata filtering (by identity, source, date)
- Indexing markdown directories

Usage:
    from dana.lib.memory import MemoryStore

    store = MemoryStore()
    store.store("VAV damper at 100% but zone warm -> check AHU first", identity="hvac")
    results = store.query("debugging VAV temperature issues", limit=3)
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import lancedb
from lancedb.table import Table


# Default embedding model (lazy loaded)
_EMBEDDING_MODEL = None
_EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 dimension


def _get_embedding_model():
    """Get embedding model, lazy loaded."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        # Check for OpenAI first (faster, better quality)
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI

                client = OpenAI()

                class OpenAIEmbedder:
                    dim = 1536

                    def encode(self, texts: list[str] | str) -> list[list[float]]:
                        if isinstance(texts, str):
                            texts = [texts]
                        response = client.embeddings.create(
                            model="text-embedding-3-small",
                            input=texts,
                        )
                        return [e.embedding for e in response.data]

                _EMBEDDING_MODEL = OpenAIEmbedder()
                global _EMBEDDING_DIM
                _EMBEDDING_DIM = 1536
                return _EMBEDDING_MODEL
            except Exception:
                pass  # Fall through to local model

        # Fallback to local sentence-transformers
        from sentence_transformers import SentenceTransformer

        _EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

    return _EMBEDDING_MODEL


def _embed(text: str) -> list[float]:
    """Embed a single text string.

    Truncates text to ~6000 chars to stay within embedding model token limits.
    """
    # Truncate to avoid token limits (~6000 chars ≈ ~1500-2000 tokens)
    text = text[:6000]

    model = _get_embedding_model()
    if hasattr(model, "encode"):
        result = model.encode(text)
        # Handle both numpy arrays and lists
        if hasattr(result, "tolist"):
            return result.tolist()
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], list):
                return result[0]  # OpenAI returns list of lists
            return result
        return list(result)
    raise ValueError(f"Unknown embedding model type: {type(model)}")


def _text_to_id(text: str) -> str:
    """Generate stable ID from text hash."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


@dataclass
class Memory:
    """A single memory record."""

    id: str
    text: str
    source: str
    identity: str
    created: datetime
    score: float = 0.0  # Populated on query results

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "identity": self.identity,
            "created": self.created.isoformat(),
            "score": self.score,
        }


@dataclass
class MemoryStore:
    """Persistent semantic memory store using LanceDB.

    Attributes:
        store_path: Path to the LanceDB database directory.
        table_name: Name of the memories table.
    """

    store_path: Path = field(default_factory=lambda: Path.home() / ".dana" / "memory")
    table_name: str = "memories"

    _db: lancedb.DBConnection = field(default=None, init=False, repr=False)
    _table: Table | None = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Initialize the LanceDB connection."""
        self.store_path = Path(self.store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(str(self.store_path))
        self._ensure_table()

    def _get_table_names(self) -> list[str]:
        """Get list of table names in the database."""
        tables = self._db.list_tables()
        return tables.tables if hasattr(tables, "tables") else list(tables)

    def _ensure_table(self) -> None:
        """Ensure the memories table exists."""
        if self.table_name in self._get_table_names():
            self._table = self._db.open_table(self.table_name)
        else:
            self._table = None

    def _create_table_if_needed(self, vector: list[float]) -> Table:
        """Create table with first record to establish schema."""
        if self._table is None:
            # Check if table exists (may have been created by another process)
            if self.table_name in self._get_table_names():
                self._table = self._db.open_table(self.table_name)
            else:
                # Create with schema inferred from first record
                self._table = self._db.create_table(
                    self.table_name,
                    data=[
                        {
                            "id": "__schema__",
                            "text": "",
                            "source": "",
                            "identity": "",
                            "created": datetime.now().isoformat(),
                            "vector": vector,
                        }
                    ],
                )
                # Delete the schema placeholder
                self._table.delete('id = "__schema__"')
        return self._table

    def store(
        self,
        text: str,
        source: str = "agent",
        identity: str = "general",
        created: datetime | None = None,
    ) -> Memory:
        """Store a new memory.

        Args:
            text: The memory content.
            source: Where this memory came from (e.g., "session", "user", "ontology").
            identity: Domain category (e.g., "hvac", "general", "coding").
            created: Timestamp (defaults to now).

        Returns:
            The stored Memory object.
        """
        memory_id = _text_to_id(text)
        created = created or datetime.now()
        vector = _embed(text)

        # Ensure table exists
        table = self._create_table_if_needed(vector)

        # Check for duplicate
        try:
            existing = table.search().where(f'id = "{memory_id}"').limit(1).to_list()
            if existing:
                # Already exists, return existing
                row = existing[0]
                return Memory(
                    id=row["id"],
                    text=row["text"],
                    source=row["source"],
                    identity=row["identity"],
                    created=datetime.fromisoformat(row["created"]),
                )
        except Exception:
            pass  # Table might be empty, continue with insert

        # Insert new memory
        table.add(
            [
                {
                    "id": memory_id,
                    "text": text,
                    "source": source,
                    "identity": identity,
                    "created": created.isoformat(),
                    "vector": vector,
                }
            ]
        )

        return Memory(
            id=memory_id,
            text=text,
            source=source,
            identity=identity,
            created=created,
        )

    def query(
        self,
        text: str,
        limit: int = 5,
        min_score: float = 0.0,
        identity: str | None = None,
        source: str | None = None,
    ) -> list[Memory]:
        """Query for relevant memories.

        Args:
            text: The query text.
            limit: Maximum number of results.
            min_score: Minimum similarity score (0-1, higher is more similar).
            identity: Filter by identity (optional).
            source: Filter by source (optional).

        Returns:
            List of Memory objects sorted by relevance.
        """
        if self._table is None:
            return []

        vector = _embed(text)

        # Build query
        query = self._table.search(vector).limit(limit * 2)  # Fetch extra for filtering

        # Add filters
        filters = []
        if identity:
            filters.append(f'identity = "{identity}"')
        if source:
            filters.append(f'source = "{source}"')
        if filters:
            query = query.where(" AND ".join(filters))

        # Execute
        try:
            results = query.to_list()
        except Exception:
            return []

        # Convert to Memory objects
        memories = []
        for row in results:
            # LanceDB returns distance, convert to similarity score
            # For cosine distance: similarity = 1 - distance
            distance = row.get("_distance", 0)
            score = max(0, 1 - distance)

            if score < min_score:
                continue

            memories.append(
                Memory(
                    id=row["id"],
                    text=row["text"],
                    source=row["source"],
                    identity=row["identity"],
                    created=datetime.fromisoformat(row["created"]),
                    score=score,
                )
            )

            if len(memories) >= limit:
                break

        return memories

    def index_directory(
        self,
        path: Path | str,
        identity: str = "docs",
        source: str = "indexed",
        glob_pattern: str = "**/*.md",
    ) -> int:
        """Index markdown files from a directory.

        Args:
            path: Directory path to index.
            identity: Domain to assign to indexed memories.
            source: Source to assign to indexed memories.
            glob_pattern: Glob pattern for files to index.

        Returns:
            Number of memories indexed.
        """
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

        count = 0
        for file_path in path.glob(glob_pattern):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    # Use relative path as part of the memory
                    rel_path = file_path.relative_to(path)
                    text = f"[{rel_path}]\n{content}"

                    # Chunk if too long (rough chunking at ~1000 chars)
                    if len(text) > 1500:
                        chunks = self._chunk_text(text, chunk_size=1000, overlap=100)
                        for i, chunk in enumerate(chunks):
                            self.store(
                                text=f"[{rel_path} chunk {i + 1}]\n{chunk}",
                                source=source,
                                identity=identity,
                            )
                            count += 1
                    else:
                        self.store(text=text, source=source, identity=identity)
                        count += 1
                except Exception as e:
                    # Skip files that can't be read
                    print(f"Warning: Could not index {file_path}: {e}")

        return count

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID.

        Args:
            memory_id: The memory ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        if self._table is None:
            return False

        try:
            self._table.delete(f'id = "{memory_id}"')
            return True
        except Exception:
            return False

    def clear(self, identity: str | None = None) -> int:
        """Clear memories.

        Args:
            identity: If specified, only clear memories in this identity.
                   If None, clear all memories.

        Returns:
            Number of memories cleared (approximate).
        """
        if self._table is None:
            return 0

        try:
            if identity:
                # Count before delete (approximate)
                count = len(self._table.search().where(f'identity = "{identity}"').limit(10000).to_list())
                self._table.delete(f'identity = "{identity}"')
            else:
                count = self._table.count_rows()
                self._db.drop_table(self.table_name)
                self._table = None
            return count
        except Exception:
            return 0

    def list_identitys(self) -> list[str]:
        """List all identitys in the store.

        Returns:
            List of unique identity names.
        """
        if self._table is None:
            return []

        try:
            # Fetch all and extract unique identitys
            results = self._table.search().limit(10000).to_list()
            return list(set(r["identity"] for r in results))
        except Exception:
            return []

    def count(self, identity: str | None = None) -> int:
        """Count memories.

        Args:
            identity: If specified, count only memories in this identity.

        Returns:
            Number of memories.
        """
        if self._table is None:
            return 0

        try:
            if identity:
                return len(self._table.search().where(f'identity = "{identity}"').limit(100000).to_list())
            return self._table.count_rows()
        except Exception:
            return 0

    def status(self) -> dict[str, Any]:
        """Get store status.

        Returns:
            Dictionary with status information.
        """
        identitys = self.list_identitys()
        return {
            "store_path": str(self.store_path),
            "total_memories": self.count(),
            "identitys": {d: self.count(identity=d) for d in identitys},
            "embedding_model": (
                "openai/text-embedding-3-small"
                if os.getenv("OPENAI_API_KEY")
                else "sentence-transformers/all-MiniLM-L6-v2"
            ),
        }
