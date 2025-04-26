"""Web of Things (WoT) resource implementation."""

from typing import Dict, Any, Optional
import aiohttp
from opendxa.base.resource.base_resource import BaseResource
from opendxa.common.mixins.tool_callable import ToolCallable
from opendxa.common.types import BaseRequest, BaseResponse

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
    async def query(self, request: BaseRequest = None) -> BaseResponse:
        """Get WOT input."""
        if not self._io:
            await self.initialize()

        # Ensure we pass a proper dictionary with prompt
        prompt = request.get("prompt") or ""
        response = await self._io.query({"prompt": prompt})
        return response

    async def _handle_interaction(self, thing: Dict[str, Any], request: BaseRequest) -> BaseResponse:
        """Handle WoT interaction based on type."""
        interaction_type = request.get("interaction_type")
        if interaction_type == "read_property":
            return await self._read_property(thing, request)
        elif interaction_type == "write_property":
            return await self._write_property(thing, request)
        elif interaction_type == "invoke_action":
            return await self._invoke_action(thing, request)
        else:
            return BaseResponse.error_response(f"Unsupported interaction type: {interaction_type}")

    async def _read_property(self, thing: Dict[str, Any], request: BaseRequest) -> BaseResponse:
        """Read a property from a WoT thing."""
        property_name = request.get("property_name")
        if not property_name:
            return BaseResponse.error_response("Missing property name")

        try:
            value = thing["properties"][property_name]
            return BaseResponse.success_response({"value": value})
        except KeyError:
            return BaseResponse.error_response(f"Property not found: {property_name}")

    async def _write_property(self, thing: Dict[str, Any], request: BaseRequest) -> BaseResponse:
        """Write a property to a WoT thing."""
        property_name = request.get("property_name")
        value = request.get("value")
        if not property_name or value is None:
            return BaseResponse.error_response("Missing property name or value")

        try:
            thing["properties"][property_name] = value
            return BaseResponse.success_response({"status": "success"})
        except KeyError:
            return BaseResponse.error_response(f"Property not found: {property_name}")

    async def _invoke_action(self, thing: Dict[str, Any], request: BaseRequest) -> BaseResponse:
        """Invoke an action on a WoT thing."""
        action_name = request.get("action_name")
        if not action_name:
            return BaseResponse.error_response("Missing action name")

        try:
            action = thing["actions"][action_name]
            result = await action(request.get("parameters", {}))
            return BaseResponse.success_response({"result": result})
        except KeyError:
            return BaseResponse.error_response(f"Action not found: {action_name}")

    async def cleanup(self) -> None:
        """Cleanup WoT connections."""
        if self.session:
            assert self.session is not None
            await self.session.close()
            self.session = None

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check for WoT interaction patterns."""
        return "thing_id" in request and "interaction_type" in request 