"""DXA resource module."""

from opendxa.common.resource.base_resource import BaseResource, ResourceError, ResourceUnavailableError
from opendxa.common.resource.human_resource import HumanResource
from opendxa.common.resource.kb_resource import KBResource
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.resource.mcp import BaseMcpService, HttpTransportParams, McpEchoService, McpResource, StdioTransportParams
from opendxa.common.resource.memory_resource import LTMemoryResource, MemoryResource, PermMemoryResource, STMemoryResource
from opendxa.common.resource.wot_resource import WoTResource

__all__ = [
    "BaseResource",
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
