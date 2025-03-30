"""MCP remote resource using HTTP transport"""

from typing import Dict, Any, Optional, Union, Literal
from dataclasses import dataclass
import httpx
from ..base_resource import BaseResource, ResourceResponse
from ....common import DXA_LOGGER

@dataclass
class McpRemoteConnectionParams:
    """Parameters for connecting to a remote MCP resource via HTTP"""
    connection_type: Literal['http'] = 'http'
    base_url: str = None
    timeout: Optional[float] = 5.0

class McpRemoteResource(BaseResource):
    """MCP resource for remote HTTP tool execution"""
    
    def __init__(self, name: str, connection_params: Optional[Union[McpRemoteConnectionParams, Dict[str, Any]]] = None, expose: bool = False, **params):
        super().__init__(name)
        self.logger = DXA_LOGGER.getLogger(__class__.__name__)
        self.expose = expose
        
        if isinstance(connection_params, McpRemoteConnectionParams):
            self.base_url = connection_params.base_url
            timeout = connection_params.timeout
        elif isinstance(connection_params, dict):
            self.base_url = connection_params.get("base_url")
            timeout = connection_params.get("timeout", 5.0)
        else:
            self.base_url = params.get("base_url")
            timeout = params.get("timeout", 5.0)
            
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout)
        )
        self.timeout = timeout

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Handle HTTP tool execution request"""
        try:
            response = await self.client.post(
                f"/tools/{request['tool']}",
                json={"method": request["tool"], "params": request.get("arguments", {})}
            )
            response.raise_for_status()
            return ResourceResponse(
                success=True,
                content=response.json().get("result")
            )
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error("HTTP tool execution failed", exc_info=True)
            return ResourceResponse(success=False, error=str(e))

    async def cleanup(self):
        """Cleanup HTTP client"""
        await self.client.aclose()

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check for HTTP tool execution pattern"""
        return "tool" in request and "base_url" in request

    def get_connection_params(self) -> McpRemoteConnectionParams:
        """Get parameters for other agents to connect to this resource"""
        if not self.expose:
            raise ValueError(f"MCP resource '{self.name}' is not configured for exposure")
            
        return McpRemoteConnectionParams(
            base_url=self.base_url,
            timeout=self.timeout
        )