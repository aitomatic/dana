"""Web of Things (WoT) resource implementation."""

from typing import Dict, Any, Optional
import aiohttp
from .base_resource import BaseResource, ResourceResponse, ResourceError

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

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Interact with WoT Thing."""
        required_params = ["thing_id", "interaction_type", "operation"]
        if not all(p in request for p in required_params):
            return ResourceResponse(success=False, error="Missing required WoT parameters")

        thing = self.things.get(request["thing_id"])
        if not thing:
            return ResourceResponse(success=False, error=f"Thing not found: {request['thing_id']}")

        try:
            result = await self._handle_interaction(thing, request)
            return ResourceResponse(success=True, content=result)
        except aiohttp.ClientError as e:
            return ResourceResponse(success=False, error=f"WoT communication failed: {str(e)}")

    async def _handle_interaction(self, thing: Dict[str, Any], request: Dict) -> ResourceResponse:
        """Execute WoT interaction based on type."""
        interaction_type = request["interaction_type"]
        handler = {
            "property": self._handle_property,
            "action": self._handle_action,
            "event": self._handle_event
        }.get(interaction_type)

        if not handler:
            raise ResourceError(f"Invalid interaction type: {interaction_type}")

        return await handler(thing, request)

    async def _handle_property(self, thing: Dict[str, Any], request: Dict) -> ResourceResponse:
        """Handle property read/write."""
        property_name = request["property"]
        url = f"{thing['base']}/properties/{property_name}"

        if request["operation"] == "read":
            assert self.session is not None
            async with self.session.get(url) as resp:
                return ResourceResponse(
                    success=resp.status == 200,
                    content=await resp.json(),
                    error=None if resp.status == 200 else await resp.text()
                )
        
        if request["operation"] == "write":
            assert self.session is not None
            async with self.session.put(url, json=request.get("value")) as resp:
                return ResourceResponse(
                    success=resp.status == 200,
                    error=None if resp.status == 200 else await resp.text()
                )

        raise ResourceError(f"Invalid property operation: {request['operation']}")

    async def _handle_action(self, thing: Dict[str, Any], request: Dict) -> ResourceResponse:
        """Handle action invocation."""
        action_name = request["action"]
        url = f"{thing['base']}/actions/{action_name}"
        
        assert self.session is not None
        async with self.session.post(
            url,
            json=request.get("parameters", {})
        ) as resp:
            return ResourceResponse(
                success=resp.status == 200,
                content=await resp.json(),
                error=None if resp.status == 200 else await resp.text()
            )

    async def _handle_event(self, thing: Dict[str, Any], request: Dict) -> ResourceResponse:
        """Handle event retrieval."""
        event_name = request["event"]
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