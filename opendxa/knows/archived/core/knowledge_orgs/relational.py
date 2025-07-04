"""Relational store implementation using PostgreSQL."""

from typing import Any

import psycopg2
from psycopg2.extras import Json

from dana.frameworks.knows.core.knowledge_orgs.base import KnowledgeOrganization, StorageError
from dana.frameworks.knows.core.knowledge_orgs.config import RelationalSettings


class RelationalStore(KnowledgeOrganization):
    """Relational store implementation using PostgreSQL."""
    
    def __init__(self, settings: RelationalSettings):
        """Initialize the relational store.
        
        Args:
            settings: Relational store connection settings
        """
        self.settings = settings
        self.conn = self._create_connection()
        self._ensure_default_tables()
    
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
    
    def _ensure_default_tables(self) -> None:
        """Ensure default tables exist.
        
        Raises:
            StorageError: If table creation fails
        """
        default_tables = [
            'process_configs',
            'test_configs'
        ]
        
        try:
            with self.conn.cursor() as cur:
                for table in default_tables:
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS {table} (
                            id TEXT PRIMARY KEY,
                            data JSONB NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
            self.conn.commit()
        except psycopg2.Error as e:
            raise StorageError(f"Failed to ensure default tables: {e}")
    
    def _ensure_table(self, table_name: str) -> None:
        """Ensure a specific table exists.
        
        Args:
            table_name: Name of the table to create
            
        Raises:
            StorageError: If table creation fails
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id TEXT PRIMARY KEY,
                        data JSONB NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            self.conn.commit()
        except psycopg2.Error as e:
            raise StorageError(f"Failed to ensure table {table_name}: {e}")
    
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
        if not (key.startswith("test:") or key.isalnum()):
            raise ValueError("Key must start with 'test:' or be alphanumeric")
        if key.startswith("test:"):
            if ":" in key[5:]:  # Check for additional colons
                raise ValueError("Key cannot contain additional colons")
            if any(c in key for c in " \t\n\r\f\v"):
                raise ValueError("Key cannot contain whitespace")
            if any(c in key for c in "/\\*?\"<>|"):
                raise ValueError("Key cannot contain special characters")

    def store(self, key: str, value: Any) -> None:
        """Store a value in the relational store.

        Args:
            key: Key to store the value under
            value: Value to store (must be a dict with 'table' and 'data' fields)

        Raises:
            ValueError: If key is empty or invalid, or value is invalid
            StorageError: If storage fails
        """
        self._validate_key(key)
        if not isinstance(value, dict):
            raise ValueError("Value must be a dictionary")
        if 'table' not in value:
            raise ValueError("Value must contain a 'table' field")
        if 'data' not in value:
            raise ValueError("Value must contain a 'data' field")
        if not isinstance(value['data'], dict):
            raise ValueError("Data field must be a dictionary")
        
        # Ensure the table exists
        self._ensure_table(value['table'])
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {value['table']} (id, data)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data, updated_at = CURRENT_TIMESTAMP
                    """,
                    (key, Json(value['data']))
                )
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to store value: {e}")
    
    def retrieve(self, key: str) -> dict[str, Any] | None:
        """Retrieve a value from the relational store.

        Args:
            key: Key to retrieve

        Returns:
            Retrieved value or None if not found

        Raises:
            ValueError: If key is invalid
            StorageError: If retrieval fails
        """
        self._validate_key(key)
        
        # Try to find the key in all known tables
        tables_to_search = ['process_configs', 'test_configs']
        
        try:
            with self.conn.cursor() as cur:
                for table in tables_to_search:
                    cur.execute(
                        f"""
                        SELECT data FROM {table}
                        WHERE id = %s
                        """,
                        (key,)
                    )
                    result = cur.fetchone()
                    if result:
                        return result[0]
                return None
        except psycopg2.Error as e:
            raise StorageError(f"Failed to retrieve value: {e}")
    
    def delete(self, key: str) -> None:
        """Delete a value from the relational store.

        Args:
            key: Key to delete

        Raises:
            ValueError: If key is invalid
            StorageError: If deletion fails
        """
        self._validate_key(key)
        
        # Try to delete from all known tables
        tables_to_search = ['process_configs', 'test_configs']
        
        try:
            with self.conn.cursor() as cur:
                for table in tables_to_search:
                    cur.execute(
                        f"""
                        DELETE FROM {table}
                        WHERE id = %s
                        """,
                        (key,)
                    )
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to delete value: {e}")
    
    def query(self, table: str, condition: str | None = None, order_by: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        """Query values from the relational store.

        Args:
            table: Table to query
            condition: Optional SQL WHERE condition
            order_by: Optional SQL ORDER BY clause
            limit: Optional maximum number of results

        Returns:
            List of retrieved values

        Raises:
            ValueError: If parameters are invalid
            StorageError: If query fails
        """
        if not isinstance(table, str) or not table:
            raise ValueError("Table must be a non-empty string")
        if condition is not None and not isinstance(condition, str):
            raise ValueError("Condition must be a string")
        if order_by is not None and not isinstance(order_by, str):
            raise ValueError("Order by must be a string")
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        
        query = f"SELECT id, data FROM {table}"
        params = []
        
        if condition:
            query += f" WHERE {condition}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                return [{'id': row[0], 'data': row[1]} for row in results]
        except psycopg2.Error as e:
            raise StorageError(f"Failed to query values: {e}")
    
    def close(self) -> None:
        """Close the PostgreSQL connection."""
        try:
            self.conn.close()
        except psycopg2.Error:
            pass 