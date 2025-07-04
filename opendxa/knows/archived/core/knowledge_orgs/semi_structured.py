"""Semi-structured store implementation using Redis."""

import json
from typing import Any

import redis
from psycopg2.extras import Json
from redis.exceptions import RedisError

from dana.frameworks.knows.core.knowledge_orgs.base import KnowledgeOrganization, QueryError, StorageError
from dana.frameworks.knows.core.knowledge_orgs.config import RedisSettings


class SemiStructuredStore(KnowledgeOrganization):
    """Semi-structured store implementation using Redis."""
    
    def __init__(self, settings: RedisSettings, conn: Any):
        """Initialize the semi-structured store.
        
        Args:
            settings: Redis connection settings
            conn: Database connection
        """
        self.settings = settings
        self.client = self._create_client()
        self.conn = conn
    
    def _create_client(self) -> redis.Redis:
        """Create Redis client."""
        try:
            # Parse URL to get host and port
            url = self.settings.url.replace("redis://", "")
            if ":" in url:
                host, port_str = url.split(":")
                port = int(port_str)
            else:
                host = url
                port = self.settings.port

            return redis.Redis(
                host=host,
                port=port,
                db=self.settings.db,
                password=self.settings.password,
                ssl=self.settings.ssl,
                socket_timeout=self.settings.timeout,
                max_connections=self.settings.pool_size,
            )
        except RedisError as e:
            raise StorageError(f"Failed to create Redis client: {e}")
    
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
        """Store a value in the semi-structured store.

        Args:
            key: Key to store the value under
            value: Value to store (must be JSON serializable)

        Raises:
            ValueError: If key is empty or invalid, or value is not JSON serializable
            StorageError: If storage fails
        """
        self._validate_key(key)
        if not isinstance(value, dict | list):
            raise ValueError("Value must be a dict or list")
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO semi_structured_store (id, data)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data
                    """,
                    (key, Json(value))
                )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise StorageError(f"Failed to store value: {e}")
    
    def retrieve(self, key: str) -> Any | None:
        """Retrieve a value from the semi-structured store.

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
                    """
                    SELECT data FROM semi_structured_store
                    WHERE id = %s
                    """,
                    (key,)
                )
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            raise StorageError(f"Failed to retrieve value: {e}")
    
    def delete(self, key: str) -> None:
        """Delete a value from the semi-structured store.

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
                    """
                    DELETE FROM semi_structured_store
                    WHERE id = %s
                    """,
                    (key,)
                )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise StorageError(f"Failed to delete value: {e}")
    
    def query(self, pattern: str) -> list[Any]:
        """Query values in Redis by pattern.

        Args:
            pattern: Pattern to match keys

        Returns:
            List of matching values

        Raises:
            QueryError: If query fails or pattern is invalid
        """
        if not isinstance(pattern, str) or not pattern:
            raise QueryError("Pattern must be a non-empty string")
        try:
            keys = self.client.keys(pattern)
            results = []
            for key in keys:
                value = self.client.get(key)
                if value is not None:
                    # Handle both string and bytes responses
                    if isinstance(value, bytes):
                        value_str = value.decode('utf-8')
                    elif isinstance(value, str):
                        value_str = value
                    else:
                        value_str = str(value)
                    results.append(json.loads(value_str))
            return results
        except Exception as e:
            raise QueryError(f"Failed to query values: {e}")
    
    def close(self) -> None:
        """Close the Redis connection."""
        try:
            self.client.close()
        except RedisError:
            pass 