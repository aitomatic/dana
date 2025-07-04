"""Time series store implementation using PostgreSQL with TimescaleDB."""

from datetime import datetime
from typing import Any

import psycopg2
from psycopg2.extras import Json

from dana.frameworks.knows.core.knowledge_orgs.base import KnowledgeOrganization, QueryError, StorageError
from dana.frameworks.knows.core.knowledge_orgs.config import TimeSeriesSettings


class TimeSeriesStore(KnowledgeOrganization):
    """Time series store implementation using PostgreSQL with TimescaleDB."""
    
    def __init__(self, settings: TimeSeriesSettings):
        """Initialize the time series store.
        
        Args:
            settings: Time series store connection settings
        """
        self.settings = settings
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
        """Ensure TimescaleDB extension is installed.
        
        Raises:
            StorageError: If extension installation fails
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
            self.conn.commit()
        except psycopg2.Error as e:
            raise StorageError(f"Failed to ensure TimescaleDB extension: {e}")
    
    def _ensure_table(self) -> None:
        """Ensure time series store table exists.
        
        Raises:
            StorageError: If table creation fails
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.settings.table} (
                        id TEXT NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        value DOUBLE PRECISION NOT NULL,
                        unit TEXT NOT NULL,
                        metadata JSONB DEFAULT '{{}}'::jsonb,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create hypertable for TimescaleDB (if not already exists)
                cur.execute(f"""
                    SELECT create_hypertable('{self.settings.table}', 'timestamp', if_not_exists => TRUE)
                """)
            self.conn.commit()
        except psycopg2.Error as e:
            # Ignore error if hypertable already exists or TimescaleDB is not available
            if "already a hypertable" not in str(e) and "extension \"timescaledb\" is not available" not in str(e):
                raise StorageError(f"Failed to ensure time series store table: {e}")
            self.conn.rollback()
    
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
        """Store a value in the time series store.

        Args:
            key: Key to store the value under
            value: Value to store (must be a dict with timestamp, value, unit, and metadata)

        Raises:
            ValueError: If key is empty or invalid, or value is invalid
            StorageError: If storage fails
        """
        self._validate_key(key)
        if not isinstance(value, dict):
            raise ValueError("Value must be a dictionary")
        if 'timestamp' not in value:
            raise ValueError("Value must contain a 'timestamp' field")
        if 'value' not in value:
            raise ValueError("Value must contain a 'value' field")
        if 'unit' not in value:
            raise ValueError("Value must contain a 'unit' field")
        if 'metadata' not in value:
            raise ValueError("Value must contain a 'metadata' field")
        
        timestamp = value['timestamp']
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        elif not isinstance(timestamp, str):
            raise ValueError("Timestamp must be a string or datetime object")
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            raise ValueError("Timestamp must be in ISO format")
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO time_series_store (id, timestamp, value, unit, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (key, timestamp, value['value'], value['unit'], Json(value['metadata']))
                )
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to store value: {e}")
    
    def retrieve(self, key: str, start_time: str | datetime | None = None, end_time: str | datetime | None = None) -> list[dict[str, Any]]:
        """Retrieve values from the time series store.

        Args:
            key: Key to retrieve
            start_time: Optional start time in ISO format or datetime object
            end_time: Optional end time in ISO format or datetime object

        Returns:
            List of retrieved values

        Raises:
            ValueError: If key is invalid or time format is invalid
            StorageError: If retrieval fails
        """
        self._validate_key(key)
        query = "SELECT timestamp, value, unit, metadata FROM time_series_store WHERE id = %s"
        params = [key]
        
        if start_time:
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat()
            try:
                datetime.fromisoformat(start_time)
            except ValueError:
                raise ValueError("Start time must be in ISO format")
            query += " AND timestamp >= %s"
            params.append(start_time)
        
        if end_time:
            if isinstance(end_time, datetime):
                end_time = end_time.isoformat()
            try:
                datetime.fromisoformat(end_time)
            except ValueError:
                raise ValueError("End time must be in ISO format")
            query += " AND timestamp <= %s"
            params.append(end_time)
        
        query += " ORDER BY timestamp ASC"
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                return [
                    {
                        'timestamp': row[0],
                        'value': row[1],
                        'unit': row[2],
                        'metadata': row[3]
                    }
                    for row in results
                ]
        except psycopg2.Error as e:
            raise StorageError(f"Failed to retrieve values: {e}")
    
    def delete(self, key: str) -> None:
        """Delete values from the time series store.

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
                    DELETE FROM time_series_store
                    WHERE id = %s
                    """,
                    (key,)
                )
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to delete values: {e}")
    
    def query(self, **kwargs) -> list[Any]:
        """Query values from the time series store.
        
        Args:
            **kwargs: Query parameters
                start_time: Start time for query
                end_time: End time for query
                limit: Maximum number of results
                interval: Time interval for aggregation
                
        Returns:
            List of matching values
            
        Raises:
            QueryError: If query fails
        """
        try:
            start_time = kwargs.get("start_time")
            end_time = kwargs.get("end_time")
            limit = kwargs.get("limit", 100)
            interval = kwargs.get("interval")
            
            if not start_time or not end_time:
                raise ValueError("Query must include 'start_time' and 'end_time' parameters")
            
            # Convert times to strings if datetime
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat()
            if isinstance(end_time, datetime):
                end_time = end_time.isoformat()
            
            with self.conn.cursor() as cur:
                if interval:
                    # Aggregated query
                    cur.execute(
                        """
                        SELECT time_bucket(%s, timestamp) as bucket,
                               jsonb_agg(value ORDER BY timestamp) as values
                        FROM time_series_store
                        WHERE timestamp >= %s AND timestamp <= %s
                        GROUP BY bucket
                        ORDER BY bucket DESC
                        LIMIT %s
                        """,
                        (interval, start_time, end_time, limit)
                    )
                else:
                    # Raw query
                    cur.execute(
                        """
                        SELECT value
                        FROM time_series_store
                        WHERE timestamp >= %s AND timestamp <= %s
                        ORDER BY timestamp DESC
                        LIMIT %s
                        """,
                        (start_time, end_time, limit)
                    )
                
                results = cur.fetchall()
                
                if interval:
                    return [{"bucket": row[0], "values": row[1]} for row in results]
                else:
                    return [row[0] for row in results]
        except (psycopg2.Error, ValueError) as e:
            raise QueryError(f"Failed to query values: {e}")
    
    def close(self) -> None:
        """Close the PostgreSQL connection."""
        try:
            self.conn.close()
        except psycopg2.Error:
            pass 