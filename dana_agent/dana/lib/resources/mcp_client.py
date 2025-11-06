"""
MCPClientResource - A resource for making MCP (Model Context Protocol) calls.

This resource provides a flexible interface for making MCP calls to both HTTP-based
and local MCP servers. It supports different transport methods and can be configured
to work with various MCP server types.

Example usage:
    # For HTTP-based MCP servers
    mcp_client = MCPClientResource(
        server_type="http",
        server_config={
            "url": "https://api.example.com/mcp",
            "headers": {"Authorization": "Bearer your-token"}
        }
    )

    # For local MCP servers (like BrightData)
    mcp_client = MCPClientResource(
        server_type="local",
        server_config={
            "command": "npx",
            "args": ["@brightdata/mcp"],
            "env": {"API_TOKEN": "your-token"}
        }
    )

    # Make dynamic calls using magic methods
    result = mcp_client.some_method(param1="value1", param2="value2")

    # Or use the direct query method
    result = mcp_client.query("some_method", param1="value1", param2="value2")
"""

import json
import logging
import subprocess
from typing import Any
from urllib.parse import urlencode

import httpx

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


logger = logging.getLogger(__name__)


class MCPClientResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    MCP (Model Context Protocol) client resource for making dynamic API calls.

    This resource provides a flexible interface for communicating with both HTTP-based
    and local MCP servers. It supports different transport methods and can be configured
    to work with various MCP server types including local npm packages like BrightData.

    USE CASES:
    - Integration with HTTP-based MCP services
    - Communication with local MCP servers (npm packages, etc.)
    - Dynamic API calls to MCP-compatible endpoints
    - Flexible service communication without hardcoded methods
    - Testing and prototyping with MCP services

    FEATURES:
    - Support for HTTP and local MCP servers
    - Dynamic method calling via magic methods
    - Configurable server parameters (URLs, commands, environment variables)
    - Automatic request/response handling
    - Error handling and logging
    - JSON payload support

    EXAMPLE USAGE:
    ```python
    # For HTTP-based MCP servers
    mcp_client = MCPClientResource(
        server_type="http",
        server_config={
            "url": "https://api.example.com/mcp",
            "headers": {"Authorization": "Bearer your-token"}
        }
    )

    # For local MCP servers (like BrightData)
    mcp_client = MCPClientResource(
        server_type="local",
        server_config={
            "command": "npx",
            "args": ["@brightdata/mcp"],
            "env": {"API_TOKEN": "your-token"}
        }
    )

    # Make dynamic calls
    result = mcp_client.some_method(param1="value1", param2="value2")
    ```
    </PUBLIC_DESCRIPTION>
    """

    def __init__(
        self,
        server_type: str = "http",
        server_config: dict[str, Any] | None = None,
        resource_id: str | None = None,
        timeout: float = 30.0,
        **kwargs,
    ):
        """
        Initialize the MCPClientResource.

        Args:
            server_type: Type of MCP server ("http" or "local")
            server_config: Configuration for the MCP server
            resource_id: Unique identifier for this resource
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to parent classes
        """
        super().__init__(resource_type="mcp-client", resource_id=resource_id or f"mcp-client-{server_type}", **kwargs)

        self.server_type = server_type
        self.server_config = server_config or {}
        self.timeout = timeout
        self._process = None
        self._session_id = None

        # Initialize based on server type
        if server_type == "http":
            self._init_http_server()
        elif server_type == "local":
            self._init_local_server()
        else:
            raise ValueError(f"Unsupported server type: {server_type}")

    def _init_http_server(self) -> None:
        """Initialize HTTP-based MCP server configuration."""
        self.url = self.server_config.get("url", "").rstrip("/")
        if not self.url:
            raise ValueError("URL is required for HTTP server type")

        self.headers = self.server_config.get("headers", {})
        self.uri_params = self.server_config.get("uri_params", {})

        # Build the full URL with parameters
        self._build_full_url()

    def _init_local_server(self) -> None:
        """Initialize local MCP server configuration."""
        self.command = self.server_config.get("command", "npx")
        self.args = self.server_config.get("args", [])
        self.env = self.server_config.get("env", {})

        if not self.args:
            raise ValueError("args are required for local server type")

        # Start the local MCP server process
        self._start_local_server()

    def _build_full_url(self) -> None:
        """Build the full URL with URI parameters."""
        if self.uri_params:
            # Add parameters to the URL
            param_string = urlencode(self.uri_params)
            separator = "&" if "?" in self.url else "?"
            self.full_url = f"{self.url}{separator}{param_string}"
        else:
            self.full_url = self.url

    def _start_local_server(self) -> None:
        """Start the local MCP server process."""
        try:
            # Prepare environment variables
            env = {**self.env}

            # Start the process
            self._process = subprocess.Popen(
                [self.command] + self.args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
            )

            logger.info(f"Started local MCP server: {self.command} {' '.join(self.args)}")

        except Exception as e:
            logger.error(f"Failed to start local MCP server: {e}")
            raise RuntimeError(f"Failed to start local MCP server: {e}")

    def _stop_local_server(self) -> None:
        """Stop the local MCP server process."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
                logger.info("Stopped local MCP server")
            except subprocess.TimeoutExpired:
                self._process.kill()
                logger.warning("Force killed local MCP server")
            except Exception as e:
                logger.error(f"Error stopping local MCP server: {e}")
            finally:
                self._process = None

    def __getattr__(self, method_name: str):
        """
        Magic method to handle dynamic method calls.

        This allows calling any method name on the resource, which will be
        forwarded as an MCP call to the configured server.

        Args:
            method_name: The name of the method being called

        Returns:
            A callable that will make the MCP request
        """

        def mcp_call(**kwargs) -> DictParams:
            """
            Make an MCP call with the given method name and parameters.

            Args:
                **kwargs: Parameters to send with the MCP call

            Returns:
                Response from the MCP service
            """
            return self._make_mcp_call(method_name, kwargs)

        return mcp_call

    def _make_mcp_call(self, method_name: str, params: dict[str, Any]) -> DictParams:
        """
        Make an MCP call to the configured service.

        Args:
            method_name: The method name to call
            params: Parameters to send with the call

        Returns:
            Response from the MCP service
        """
        if self.server_type == "http":
            return self._make_http_mcp_call(method_name, params)
        elif self.server_type == "local":
            return self._make_local_mcp_call(method_name, params)
        else:
            return {"error": f"Unsupported server type: {self.server_type}", "method": method_name}

    def _make_http_mcp_call(self, method_name: str, params: dict[str, Any]) -> DictParams:
        """
        Make an HTTP-based MCP call.

        Args:
            method_name: The method name to call
            params: Parameters to send with the call

        Returns:
            Response from the MCP service
        """
        # Prepare the MCP request payload
        payload = {"method": method_name, "params": params}

        logger.info(f"Making HTTP MCP call to {self.full_url}: {method_name}")
        logger.debug(f"MCP payload: {payload}")

        try:
            # Make the HTTP request
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.full_url, json=payload, headers={**self.headers, "Content-Type": "application/json"})
                response.raise_for_status()

                # Parse the JSON response
                result = response.json()

                logger.info(f"HTTP MCP call successful: {method_name}")
                logger.debug(f"MCP response: {result}")

                return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during MCP call {method_name}: {e}")
            return {
                "error": f"HTTP error: {str(e)}",
                "method": method_name,
                "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error during MCP call {method_name}: {e}")
            return {"error": f"JSON decode error: {str(e)}", "method": method_name}
        except Exception as e:
            logger.error(f"Unexpected error during MCP call {method_name}: {e}")
            return {"error": f"Unexpected error: {str(e)}", "method": method_name}

    def _make_local_mcp_call(self, method_name: str, params: dict[str, Any]) -> DictParams:
        """
        Make a local MCP call via subprocess communication.

        Args:
            method_name: The method name to call
            params: Parameters to send with the call

        Returns:
            Response from the MCP service
        """
        if not self._process:
            return {"error": "Local MCP server process not running", "method": method_name}

        # Prepare the MCP request payload (JSON-RPC 2.0 format)
        payload = {"jsonrpc": "2.0", "method": method_name, "params": params, "id": 1}

        logger.info(f"Making local MCP call: {method_name}")
        logger.debug(f"MCP payload: {payload}")

        try:
            # Send the request to the local MCP server
            request_json = json.dumps(payload) + "\n"
            if self._process.stdin:
                self._process.stdin.write(request_json)
                self._process.stdin.flush()

            # Read the response
            if self._process.stdout:
                response_line = self._process.stdout.readline()
                if not response_line:
                    return {"error": "No response from local MCP server", "method": method_name}
            else:
                return {"error": "No stdout available from local MCP server", "method": method_name}

            # Parse the JSON response
            result = json.loads(response_line.strip())

            logger.info(f"Local MCP call successful: {method_name}")
            logger.debug(f"MCP response: {result}")

            # Return the result or error from JSON-RPC response
            if "result" in result:
                return result["result"]
            elif "error" in result:
                return {"error": result["error"], "method": method_name}
            else:
                return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error during local MCP call {method_name}: {e}")
            return {"error": f"JSON decode error: {str(e)}", "method": method_name}
        except Exception as e:
            logger.error(f"Unexpected error during local MCP call {method_name}: {e}")
            return {"error": f"Unexpected error: {str(e)}", "method": method_name}

    @tool_use
    def query(self, **kwargs) -> DictParams:
        """
        Make a direct MCP call using the query method.

        This provides an alternative way to make MCP calls without using
        the magic method approach.

        Args: kwargs: including:
            method_name: The method name to call
            any other parameters to send with the call

        Returns:
            Response from the MCP service
        """
        method_name = kwargs.pop("method_name")
        if not method_name or len(method_name) == 0:
            raise ValueError("method_name is required and must be a non-empty string")
        return self._make_mcp_call(method_name, kwargs)

    @tool_use
    def get_info(self) -> DictParams:
        """
        Get information about this MCP client resource.

        Returns:
            Dictionary containing resource information
        """
        info = {
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "server_type": self.server_type,
            "timeout": self.timeout,
        }

        if self.server_type == "http":
            info.update(
                {
                    "url": getattr(self, "url", ""),
                    "full_url": getattr(self, "full_url", ""),
                    "headers": getattr(self, "headers", {}),
                    "uri_params": getattr(self, "uri_params", {}),
                }
            )
        elif self.server_type == "local":
            info.update(
                {
                    "command": getattr(self, "command", ""),
                    "args": getattr(self, "args", []),
                    "env": getattr(self, "env", {}),
                    "process_running": self._process is not None,
                }
            )

        return info

    def update_server_config(self, new_config: dict[str, Any]) -> None:
        """
        Update the server configuration.

        Args:
            new_config: New server configuration to use
        """
        self.server_config.update(new_config)

        if self.server_type == "http":
            self._init_http_server()
        elif self.server_type == "local":
            # Stop existing process and restart with new config
            self._stop_local_server()
            self._init_local_server()

        logger.info(f"Updated server configuration: {self.server_config}")

    def restart_local_server(self) -> None:
        """
        Restart the local MCP server process.
        """
        if self.server_type == "local":
            self._stop_local_server()
            self._start_local_server()
            logger.info("Restarted local MCP server")
        else:
            logger.warning("restart_local_server() only works for local server type")

    def __del__(self):
        """Cleanup when the resource is destroyed."""
        if self.server_type == "local":
            self._stop_local_server()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self.server_type == "local":
            self._stop_local_server()
