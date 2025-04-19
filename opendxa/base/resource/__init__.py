"""DXA resource module."""

from opendxa.base.resource.base_resource import (
    BaseResource,
    ResourceResponse,
    ResourceError,
    ResourceUnavailableError
)
from opendxa.base.resource.human_resource import HumanResource
from opendxa.base.resource.llm_resource import LLMResource
from opendxa.base.resource.mcp import (
    McpResource, StdioTransportParams, HttpTransportParams,
    BaseMcpService, McpEchoService
)
from opendxa.base.resource.wot_resource import WoTResource

__all__ = [
    "BaseResource",
    "ResourceResponse",
    "ResourceError",
    "ResourceUnavailableError",
    "LLMResource",
    "HumanResource",
    "McpResource",
    "StdioTransportParams",
    "HttpTransportParams",
    "BaseMcpService",
    "McpEchoService",
    "WoTResource",
]
