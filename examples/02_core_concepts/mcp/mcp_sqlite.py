import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Optional

from dxa.agent.resource.mcp.mcp_services import BaseMcpService

_SELF: Optional["SqliteMcpServer"]


class SqliteDatabase:
    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).expanduser())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize connection to the SQLite database"""
        print("Initializing database connection")
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            conn.close()

    def _execute_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a SQL query and return results as a list of dictionaries"""
        print(f"Executing query: {query}")
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                with closing(conn.cursor()) as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")):
                        conn.commit()
                        affected = cursor.rowcount
                        print(f"Write query affected {affected} rows")
                        return [{"affected_rows": affected}]

                    results = [dict(row) for row in cursor.fetchall()]
                    print(f"Read query returned {len(results)} rows")
                    return results
        except Exception as e:
            print(f"Database error executing query: {e}")
            raise


class SqliteMcpServer(BaseMcpService):
    """MCP Server for SQLite Database"""

    def __init__(self, db_path: str):
        super().__init__()
        self.db = SqliteDatabase(db_path)
        global _SELF  # pylint: disable=global-statement
        _SELF = self

    @BaseMcpService.tool(name="read_query", description="Execute a SELECT query on the SQLite database")
    def read_query(self, query: str) -> str:
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed for read_query")
        results = _SELF.db._execute_query(query)  # type: ignore
        return str(results)

    @BaseMcpService.tool(
        name="write_query", description="Execute an INSERT, UPDATE, or DELETE query on the SQLite database"
    )
    def write_query(self, query: str) -> str:
        if query.strip().upper().startswith("SELECT"):
            raise ValueError("SELECT queries are not allowed for write_query")
        results = _SELF.db._execute_query(query)  # type: ignore
        return str(results)

    @BaseMcpService.tool(name="create_table", description="Create a new table in the SQLite database")
    def create_table(self, query: str) -> str:
        if not query.strip().upper().startswith("CREATE TABLE"):
            raise ValueError("Only CREATE TABLE statements are allowed")
        _SELF.db._execute_query(query)  # type: ignore
        return "Table created successfully"

    @BaseMcpService.tool(name="list_tables", description="List all tables in the SQLite database")
    def list_tables(self) -> str:
        results = _SELF.db._execute_query("SELECT name FROM sqlite_master WHERE type='table'")  # type: ignore
        return str(results)

    @BaseMcpService.tool(name="describe_table", description="Get the schema information for a specific table")
    def describe_table(self, table_name: str) -> str:
        results = _SELF.db._execute_query(f"PRAGMA table_info({table_name})")  # type: ignore
        return str(results)


if __name__ == "__main__":
    # Start the SQLite server
    print("Starting SQLite Server...")
    print("Available tools:")
    print("  - read_query: Execute a SELECT query on the SQLite database")
    print("  - write_query: Execute an INSERT, UPDATE, or DELETE query on the SQLite database")
    print("  - create_table: Create a new table in the SQLite database")
    print("  - list_tables: List all tables in the SQLite database")
    print("  - describe_table: Get the schema information for a specific table")
    print("\nService is running. Press Ctrl+C to stop.")

    db_path = os.environ.get("SQLITE_DB_PATH", "./sqlite_mcp_server.db")
    print(f"Using database at: {db_path}")

    try:
        SqliteMcpServer(db_path=db_path).run()
    except Exception as e:
        print(f"Error starting SQLite server: {e}")
