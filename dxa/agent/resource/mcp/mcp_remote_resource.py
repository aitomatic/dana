"""MCP remote resource using HTTP transport"""

from typing import Dict, Any
import httpx
from ..base_resource import BaseResource, ResourceResponse
from ....common import DXA_LOGGER

class McpRemoteResource(BaseResource):
    """MCP resource for remote HTTP tool execution"""
    
    def __init__(self, name: str, base_url: str, **params):
        super().__init__(name)
        self.logger = DXA_LOGGER.getLogger(__class__.__name__)
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(params.get("timeout", 5.0))
        )

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