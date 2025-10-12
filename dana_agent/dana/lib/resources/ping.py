"""
PingResource - A simple resource for testing connectivity.
"""

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class PingResource(BaseResource):
    """A simple resource that responds to ping requests."""

    def __init__(self, resource_id: str | None = None, **kwargs):
        """Initialize the PingResource."""
        super().__init__(resource_type="ping", resource_id=resource_id or "ping", **kwargs)

    @tool_use
    def query(self, **kwargs) -> DictParams:
        """
        Respond to a ping request.

        Args:
            **kwargs: The arguments to the query method.

        Returns:
            A dictionary with the response message
        """
        response_message = kwargs.get("message", "Pong") if kwargs else "Pong"
        return {"message": response_message}
