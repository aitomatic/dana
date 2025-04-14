"""DXA resource module."""

from .base_resource import (
    BaseResource,
    ResourceResponse,
    ResourceError,
    ResourceUnavailableError
)
from .human_resource import HumanResource
from .llm_resource import LLMResource
from .llm_result_resource import LLMResultResource
from .mcp import (
    McpResource, StdioTransportParams, HttpTransportParams,
    BaseMcpService, McpEchoService
)
from .wot_resource import WoTResource

__all__ = [
    "BaseResource",
    "ResourceResponse",
    "ResourceError",
    "ResourceUnavailableError",
    "LLMResource",
    "HumanResource",
    "LLMResultResource",
    "McpResource",
    "StdioTransportParams",
    "HttpTransportParams",
    "BaseMcpService",
    "McpEchoService",
    "WoTResource",
]
