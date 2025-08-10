"""
SQL Database Resource

A Python-based resource for SQL database operations.
This demonstrates how to create resources that need Python libraries.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
import json

from dana.core.resource import BaseResource


@dataclass
class SQLResource(BaseResource):
    """SQL database resource for executing queries and managing connections."""

    kind: str = "sql"
    connection_string: str = ""
    database_type: str = "sqlite"  # sqlite, postgresql, mysql
    pool_size: int = 5
    query_timeout: int = 30

    # Internal state (not exposed to Dana)
    _connection_pool: List[Any] = field(default_factory=list, init=False, repr=False)

    def initialize(self) -> bool:
        """Initialize database connection pool."""
        if not self.connection_string:
            # Use in-memory SQLite for demo
            self.connection_string = ":memory:"

        print(f"Initializing SQL resource '{self.name}' with {self.database_type}")

        # In a real implementation, would create actual DB connections
        # For now, simulate connection pool
        self._connection_pool = [f"connection_{i}" for i in range(self.pool_size)]

        self.state = self.state.__class__.RUNNING
        self.capabilities = ["query", "execute", "transaction", "schema"]
        return True

    def cleanup(self) -> bool:
        """Close all database connections."""
        print(f"Closing SQL connections for '{self.name}'")
        self._connection_pool.clear()
        self.state = self.state.__class__.TERMINATED
        return True

    def query(self, request: Any) -> Any:
        """Execute a SQL query and return results."""
        if not self.is_running():
            return {"error": f"SQL resource {self.name} not running"}

        # Parse request
        if isinstance(request, str):
            sql_query = request
            params = []
        elif isinstance(request, dict):
            sql_query = request.get("query", "")
            params = request.get("params", [])
        else:
            return {"error": "Invalid request format"}

        # Simulate query execution
        if sql_query.upper().startswith("SELECT"):
            # Simulate SELECT query results
            return {
                "success": True,
                "query": sql_query,
                "rows": [{"id": 1, "name": "Alice", "email": "alice@example.com"}, {"id": 2, "name": "Bob", "email": "bob@example.com"}],
                "row_count": 2,
                "columns": ["id", "name", "email"],
            }
        elif sql_query.upper().startswith(("INSERT", "UPDATE", "DELETE")):
            # Simulate DML operations
            return {"success": True, "query": sql_query, "rows_affected": 1, "message": "Operation completed successfully"}
        elif sql_query.upper().startswith(("CREATE", "ALTER", "DROP")):
            # Simulate DDL operations
            return {"success": True, "query": sql_query, "message": "Schema operation completed"}
        else:
            return {"success": True, "query": sql_query, "message": f"Query executed: {sql_query[:50]}..."}

    def execute(self, sql: str, params: List[Any] = None) -> Dict[str, Any]:
        """Execute a SQL statement with parameters."""
        if not self.is_running():
            return {"error": f"SQL resource {self.name} not running"}

        # Use the query method with proper format
        return self.query({"query": sql, "params": params or []})

    def get_schema(self, table_name: str = None) -> Dict[str, Any]:
        """Get database schema information."""
        if not self.is_running():
            return {"error": f"SQL resource {self.name} not running"}

        if table_name:
            # Return schema for specific table
            return {
                "table": table_name,
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True},
                    {"name": "name", "type": "VARCHAR(100)", "nullable": False},
                    {"name": "email", "type": "VARCHAR(255)", "nullable": True},
                    {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"},
                ],
                "indexes": ["idx_email"],
                "foreign_keys": [],
            }
        else:
            # Return all tables
            return {
                "database": self.database_type,
                "tables": ["users", "products", "orders"],
                "views": ["user_orders_view"],
                "stored_procedures": [],
            }

    def begin_transaction(self) -> Dict[str, Any]:
        """Begin a database transaction."""
        if not self.is_running():
            return {"error": f"SQL resource {self.name} not running"}

        return {"transaction_id": "txn_12345", "status": "active", "isolation_level": "READ_COMMITTED"}

    def commit_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Commit a database transaction."""
        return {"transaction_id": transaction_id, "status": "committed", "message": "Transaction committed successfully"}

    def rollback_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Rollback a database transaction."""
        return {"transaction_id": transaction_id, "status": "rolled_back", "message": "Transaction rolled back"}

    def get_stats(self) -> Dict[str, Any]:
        """Get database connection statistics."""
        return {
            "name": self.name,
            "database_type": self.database_type,
            "state": self.state.value,
            "connection_string": self.connection_string[:20] + "..." if len(self.connection_string) > 20 else self.connection_string,
            "pool_size": self.pool_size,
            "active_connections": len(self._connection_pool),
            "query_timeout": self.query_timeout,
            "capabilities": self.capabilities,
        }
