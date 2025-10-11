"""
PingResource - A simple resource for testing connectivity.
"""

from adana.common.protocols.types import DictParams
from adana.common.protocols.war import tool_use
from adana.core.resource.base_resource import BaseResource


class PingResource(BaseResource):
    """A simple resource that responds to ping requests."""

    def __init__(self, **kwargs):
        """Initialize the PingResource."""
        super().__init__(resource_type="ping", **kwargs)

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
