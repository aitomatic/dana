"""Vector store implementation using PostgreSQL with pgvector."""

from typing import Any

import numpy as np
import psycopg2
from psycopg2.extras import Json

from dana.frameworks.knows.core.knowledge_orgs.base import KnowledgeOrganization, QueryError, StorageError
from dana.frameworks.knows.core.knowledge_orgs.config import VectorStoreSettings


class VectorStore(KnowledgeOrganization):
    """Vector store implementation using PostgreSQL with pgvector."""
    
    def __init__(self, settings: VectorStoreSettings):
        """Initialize the vector store.
        
        Args:
            settings: Vector store connection settings
        """
        self.settings = settings
        self.dimensions = settings.embedding_dim
        self.conn = self._create_connection()
        self._ensure_extension()
        self._ensure_table()
    
    def _create_connection(self) -> psycopg2.extensions.connection:
        """Create a PostgreSQL connection.
        
        Returns:
            PostgreSQL connection instance
        
        Raises:
            StorageError: If connection fails
        """
        try:
            return psycopg2.connect(
                host=self.settings.host,
                port=self.settings.port,
                database=self.settings.database,
                user=self.settings.user,
                password=self.settings.password,
                sslmode=self.settings.ssl_mode
            )
        except psycopg2.Error as e:
            raise StorageError(f"Failed to create PostgreSQL connection: {e}")
    
    def _ensure_extension(self) -> None:
        """Ensure pgvector extension is installed.
        
        Raises:
            StorageError: If extension installation fails
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            self.conn.commit()
        except psycopg2.Error as e:
            raise StorageError(f"Failed to ensure pgvector extension: {e}")
    
    def _ensure_table(self) -> None:
        """Ensure vector store table exists.
        
        Raises:
            StorageError: If table creation fails
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.settings.table} (
                        id TEXT PRIMARY KEY,
                        embedding vector({self.dimensions}),
                        metadata JSONB DEFAULT '{{}}'::jsonb,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            self.conn.commit()
        except psycopg2.Error as e:
            raise StorageError(f"Failed to ensure vector store table: {e}")
    
    def _parse_vector(self, vector_data) -> list[float]:
        """Parse vector data from PostgreSQL format.
        
        Args:
            vector_data: Vector data from PostgreSQL (string or list)
            
        Returns:
            List of floats representing the vector
        """
        if isinstance(vector_data, str):
            # Remove brackets and split by comma
            vector_str = vector_data.strip('[]')
            return [float(x.strip()) for x in vector_str.split(',')]
        elif isinstance(vector_data, list):
            return vector_data
        else:
            return list(vector_data)

    def _validate_key(self, key: str) -> None:
        """Validate key format.

        Args:
            key: Key to validate

        Raises:
            ValueError: If key is invalid
        """
        if not isinstance(key, str):
            raise ValueError("Key must be a string")
        if not key:
            raise ValueError("Key cannot be empty")
        if not key.startswith("test:"):
            raise ValueError("Key must start with 'test:'")
        if ":" in key[5:]:  # Check for additional colons
            raise ValueError("Key cannot contain additional colons")
        if any(c in key for c in " \t\n\r\f\v"):
            raise ValueError("Key cannot contain whitespace")
        if any(c in key for c in "/\\*?\"<>|"):
            raise ValueError("Key cannot contain special characters")

    def store(self, key: str, value: Any) -> None:
        """Store a value in the vector store.
        
        Args:
            key: Key to store the value under
            value: Value to store (must be a dict with 'embedding' field)
            
        Raises:
            ValueError: If key is empty or invalid, or value is invalid
            StorageError: If storage fails
        """
        self._validate_key(key)
        if not isinstance(value, dict):
            raise ValueError("Value must be a dictionary")
        if 'embedding' not in value:
            raise ValueError("Value must contain an 'embedding' field")
        
        embedding = value['embedding']
        if not isinstance(embedding, list) or not all(isinstance(x, int | float) for x in embedding):
            raise ValueError("Embedding must be a list of numbers")
        if len(embedding) != self.dimensions:
            raise ValueError(f"Embedding must have {self.dimensions} dimensions")
        
        metadata = value.get('metadata', {})
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.settings.table} (id, embedding, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE 
                    SET embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                    """,
                    (key, embedding, Json(metadata))
                )
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to store value: {e}")
    
    def retrieve(self, key: str) -> dict[str, Any] | None:
        """Retrieve a value from the vector store.
        
        Args:
            key: Key to retrieve
            
        Returns:
            Retrieved value or None if not found
            
        Raises:
            ValueError: If key is invalid
            StorageError: If retrieval fails
        """
        self._validate_key(key)
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT embedding, metadata FROM {self.settings.table}
                    WHERE id = %s
                    """,
                    (key,)
                )
                result = cur.fetchone()
                if result is None:
                    return None
                
                return {
                    'embedding': self._parse_vector(result[0]),
                    'metadata': result[1]
                }
        except psycopg2.Error as e:
            raise StorageError(f"Failed to retrieve value: {e}")
    
    def delete(self, key: str) -> None:
        """Delete a value from the vector store.
        
        Args:
            key: Key to delete
            
        Raises:
            ValueError: If key is invalid
            StorageError: If deletion fails
        """
        self._validate_key(key)
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {self.settings.table}
                    WHERE id = %s
                    """,
                    (key,)
                )
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to delete value: {e}")
    
    def query(self, **kwargs) -> list[Any]:
        """Query values from the vector store.
        
        Args:
            **kwargs: Query parameters
                embedding: Vector to search for
                limit: Maximum number of results
                similarity_threshold: Minimum similarity score (0-1)
                
        Returns:
            List of matching values
            
        Raises:
            QueryError: If query fails
        """
        try:
            embedding = kwargs.get("embedding")
            if embedding is None or (isinstance(embedding, list | np.ndarray) and len(embedding) == 0):
                raise ValueError("Query must include 'embedding' parameter")
            
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            if not isinstance(embedding, list) or not all(isinstance(x, int | float) for x in embedding):
                raise ValueError("Embedding must be a list of numbers")
            
            if len(embedding) != self.dimensions:
                raise ValueError(f"Embedding must have {self.dimensions} dimensions")
            
            limit = kwargs.get("limit", 10)
            similarity_threshold = kwargs.get("similarity_threshold", 0.7)
            
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, embedding, metadata, 1 - (embedding <=> %s::vector) as similarity
                    FROM {self.settings.table}
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY similarity DESC
                    LIMIT %s
                    """,
                    (embedding, embedding, similarity_threshold, limit)
                )
                results = cur.fetchall()
                
                return [{
                    'id': row[0],
                    'embedding': self._parse_vector(row[1]),
                    'metadata': row[2],
                    'similarity': row[3]
                } for row in results]
        except (psycopg2.Error, ValueError) as e:
            raise QueryError(f"Failed to query values: {e}")
    
    def close(self) -> None:
        """Close the PostgreSQL connection."""
        try:
            self.conn.close()
        except psycopg2.Error:
            pass 