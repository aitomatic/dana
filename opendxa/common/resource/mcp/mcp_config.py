"""MCP configuration management module.

This module provides utilities for loading and managing MCP server configurations
from JSON files or dictionaries. It supports both STDIO and HTTP transport configurations.
"""

import json
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field


class StdioTransportParams(BaseModel):
    """Parameters for STDIO transport.

    Args:
        server_script: Path to the Python script that will be executed as the MCP server.
            This script should implement the MCP server protocol over standard input/output.
        command: Command to execute the server script (default: "python3").
            This is the interpreter or executable that will run the server_script.
        args: Optional list of additional arguments to pass to the command.
            If not provided, only the server_script will be passed as an argument.
        env: Optional dictionary of environment variables to set for the server process.
            These will be merged with the default environment variables.
        stdio_config: Optional additional configuration for STDIO transport.
            This can include settings specific to the STDIO communication protocol.
            Common parameters include:
            - buffer_size: Size of the read/write buffers (default: 8192)
            - encoding: Text encoding for communication (default: "utf-8")
            - line_buffering: Whether to use line buffering (default: True)
            - timeout: Timeout for read/write operations in seconds

            The STDIO transport is ideal for local MCP servers that run in the same process
            or on the same machine. It uses standard input/output streams for communication,
            making it simple to set up and debug.
    """

    server_script: str = Field(..., description="Path to the Python script that will be executed as the MCP server")
    command: str = Field(default="python3", description="Command to execute the server script")
    args: Sequence[str] | None = Field(default=None, description="Optional list of additional arguments to pass to the command")
    env: dict[str, str] | None = Field(
        default=None, description="Optional dictionary of environment variables to set for the server process"
    )
    stdio_config: dict[str, Any] | None = Field(default=None, description="Optional additional configuration for STDIO transport")


class HttpTransportParams(BaseModel):
    """Parameters for HTTP transport.

    Args:
        url: URL for the HTTP endpoint
        headers: Optional dictionary of HTTP headers
        timeout: HTTP request timeout in seconds.
            This is a relatively short timeout (default: 5.0s) used for the basic HTTP
            request/response cycle.
        sse_read_timeout: Server-Sent Events (SSE) read timeout in seconds.
            This is a longer timeout (default: 300s/5min) used for maintaining the SSE
            connection and receiving data over time. SSE connections are long-lived
            and may receive data for extended periods.
        sse_config: Optional additional configuration for SSE transport.
            Common parameters include:
            - retry_interval: Time to wait between reconnection attempts (default: 1.0s)
            - max_retries: Maximum number of reconnection attempts (default: 3)
            - backoff_factor: Multiplier for retry interval after each attempt
            - event_types: List of SSE event types to listen for
            - keep_alive: Whether to send keep-alive messages (default: True)
            - keep_alive_interval: Interval for keep-alive messages in seconds

            The HTTP transport with SSE is ideal for remote MCP servers that need to
            maintain long-lived connections for real-time updates. SSE allows the server
            to push data to the client asynchronously, making it suitable for streaming
            responses and long-running operations.
    """

    url: str = Field(..., description="URL for the HTTP endpoint")
    headers: dict[str, Any] | None = Field(default=None, description="Optional dictionary of HTTP headers")
    timeout: float = Field(default=5.0, description="HTTP request timeout in seconds")
    sse_read_timeout: float = Field(default=60 * 5, description="Server-Sent Events (SSE) read timeout in seconds")
    sse_config: dict[str, Any] | None = Field(default=None, description="Optional additional configuration for SSE transport")


class McpConfigError(Exception):
    """Base exception for MCP configuration errors."""

    pass


class McpConfig:
    """MCP configuration manager.

    This class handles loading and managing MCP server configurations from JSON files
    or dictionaries. It supports both STDIO and HTTP transport configurations.

    Example configuration:
    ```json
    {
        "mcpServers": {
            "server1": {
                "command": "python3",
                "args": ["path/to/script.py"],
                "env": {
                    "ENV_VAR": "value"
                }
            },
            "server2": {
                "url": "https://api.example.com/mcp",
                "headers": {
                    "Authorization": "Bearer token"
                }
            }
        }
    }
    ```
    """

    def __init__(self, config: str | dict[str, Any]):
        """Initialize MCP configuration manager.

        Args:
            config: Either a path to a JSON configuration file or a configuration dictionary

        Raises:
            McpConfigError: If configuration is invalid or missing required keys
        """
        if isinstance(config, str):
            self.config = self._load_config_from_file(config)
        else:
            self.config = self._load_config_from_dict(config)

    def _load_config_from_file(self, config_path: str) -> dict[str, Any]:
        """Load configuration from JSON file.

        Args:
            config_path: Path to the JSON configuration file

        Returns:
            Dict containing server configuration

        Raises:
            McpConfigError: If configuration file is invalid or missing required keys
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
        except FileNotFoundError as exc:
            raise McpConfigError(f"Configuration file not found: {config_path}") from exc
        except json.JSONDecodeError as exc:
            raise McpConfigError(f"Invalid JSON in configuration file: {exc}") from exc

        return self._validate_config(config)

    def _load_config_from_dict(self, config: dict[str, Any]) -> dict[str, Any]:
        """Load configuration from dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            Validated configuration dictionary

        Raises:
            McpConfigError: If configuration is invalid or missing required keys
        """
        return self._validate_config(config)

    def _validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate configuration structure.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration dictionary

        Raises:
            McpConfigError: If configuration is invalid or missing required keys
        """
        if not isinstance(config, dict):
            raise McpConfigError("Configuration must be a dictionary")

        if "mcpServers" not in config:
            raise McpConfigError("Configuration must contain 'mcpServers' key")

        if not isinstance(config["mcpServers"], dict):
            raise McpConfigError("'mcpServers' must be a dictionary")

        return config

    def get_server_config(self, name: str) -> dict[str, Any]:
        """Get configuration for a specific server.

        Args:
            name: Name of the server in the configuration

        Returns:
            Server configuration dictionary

        Raises:
            McpConfigError: If server configuration is not found
        """
        if name not in self.config["mcpServers"]:
            raise McpConfigError(f"Server '{name}' not found in configuration")

        return self.config["mcpServers"][name]

    def get_transport_params(self, name: str) -> StdioTransportParams | HttpTransportParams:
        """Get transport parameters for a specific server.

        Args:
            name: Name of the server in the configuration

        Returns:
            Transport parameters for the server

        Raises:
            McpConfigError: If server configuration is invalid
        """
        server_config = self.get_server_config(name)

        # Determine transport type from config
        if "url" in server_config:
            # HTTP transport
            return HttpTransportParams(
                url=server_config["url"],
                headers=server_config.get("headers"),
                timeout=server_config.get("timeout", 5.0),
                sse_read_timeout=server_config.get("sse_read_timeout", 300.0),
                sse_config=server_config.get("sse_config"),
            )
        else:
            # STDIO transport
            return StdioTransportParams(
                server_script=server_config.get("server_script", ""),
                command=server_config.get("command", "python3"),
                args=server_config.get("args"),
                env=server_config.get("env"),
                stdio_config=server_config.get("stdio_config"),
            )

    def list_servers(self) -> list[str]:
        """List all configured servers.

        Returns:
            List of server names
        """
        return list(self.config["mcpServers"].keys())
