"""Web of Things (WoT) resource implementation."""

from typing import Dict, Any, Optional
import aiohttp
from opendxa.base.resource.base_resource import BaseResource, ResourceResponse, ResourceError
from opendxa.common.mixins import ToolCallable
from opendxa.common.mixins.queryable import QueryParams

class WoTResource(BaseResource):
    """WoT resource handling Thing interactions."""
    
    def __init__(self,
                 name: str,
                 directory_endpoint: str,
                 thing_description: Optional[Dict[str, Any]] = None):
        super().__init__(name)
        self.directory_endpoint = directory_endpoint
        self.thing_description = thing_description
        self.session: Optional[aiohttp.ClientSession] = None
        self.things: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Discover and register Things."""
        self.session = aiohttp.ClientSession()
        async with self.session.get(f"{self.directory_endpoint}/things") as resp:
            if resp.status == 200:
                self.things = await resp.json()

    @ToolCallable.tool
    async def query(self, params: QueryParams = None) -> ResourceResponse:
        """Query WoT resource."""
        if not self._is_available:
            return ResourceResponse.error_response("WoT resource not available")

        if not params.get("thing_id") or not params.get("interaction_type"):
            return ResourceResponse.error_response("Missing required WoT parameters")

        try:
            thing = self.things.get(params["thing_id"])
            if not thing:
                return ResourceResponse.error_response(f"Thing not found: {params['thing_id']}")

            return await self._handle_interaction(thing, params)
        except Exception as e:
            return ResourceResponse.error_response(f"WoT communication failed: {str(e)}")

    async def _handle_interaction(self, thing: Dict[str, Any], params: QueryParams) -> ResourceResponse:
        """Execute WoT interaction based on type."""
        interaction_type = params["interaction_type"]
        handler = {
            "property": self._handle_property,
            "action": self._handle_action,
            "event": self._handle_event
        }.get(interaction_type)

        if not handler:
            raise ResourceError(f"Invalid interaction type: {interaction_type}")

        return await handler(thing, params)

    async def _handle_property(self, thing: Dict[str, Any], params: QueryParams) -> ResourceResponse:
        """Handle property read/write."""
        property_name = params["property"]
        url = f"{thing['base']}/properties/{property_name}"

        if params["operation"] == "read":
            assert self.session is not None
            async with self.session.get(url) as resp:
                return ResourceResponse(
                    success=resp.status == 200,
                    content=await resp.json(),
                    error=None if resp.status == 200 else await resp.text()
                )
        
        if params["operation"] == "write":
            assert self.session is not None
            async with self.session.put(url, json=params.get("value")) as resp:
                return ResourceResponse(
                    success=resp.status == 200,
                    error=None if resp.status == 200 else await resp.text()
                )

        raise ResourceError(f"Invalid property operation: {params['operation']}")

    async def _handle_action(self, thing: Dict[str, Any], params: QueryParams) -> ResourceResponse:
        """Handle action invocation."""
        action_name = params["action"]
        url = f"{thing['base']}/actions/{action_name}"
        
        assert self.session is not None
        async with self.session.post(
            url,
            json=params.get("parameters", {})
        ) as resp:
            return ResourceResponse(
                success=resp.status == 200,
                content=await resp.json(),
                error=None if resp.status == 200 else await resp.text()
            )

    async def _handle_event(self, thing: Dict[str, Any], params: QueryParams) -> ResourceResponse:
        """Handle event retrieval."""
        event_name = params["event"]
        url = f"{thing['base']}/events/{event_name}"
        assert self.session is not None
        async with self.session.get(url) as resp:
            return ResourceResponse(
                success=resp.status == 200,
                content=await resp.json(),
                error=None if resp.status == 200 else await resp.text()
            )

    async def cleanup(self) -> None:
        """Cleanup WoT connections."""
        if self.session:
            assert self.session is not None
            await self.session.close()
            self.session = None

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check for WoT interaction patterns."""
        return "thing_id" in request and "interaction_type" in request 