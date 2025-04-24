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
from opendxa.base.resource.kb_resource import KBResource
from opendxa.base.resource.memory_resource import (
    MemoryResource,
    LTMemoryResource,
    STMemoryResource,
    PermMemoryResource
)

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
    "KBResource",
    "MemoryResource",
    "LTMemoryResource",
    "STMemoryResource",
    "PermMemoryResource",
]
