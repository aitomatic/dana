"""DXA resource module."""

from .base_resource import (
    BaseResource,
    ResourceResponse,
    ResourceConfig,
    ResourceError,
    ResourceUnavailableError
)
from .human_resource import HumanResource
from .llm_resource import LLMResource
from .mcp import (
    McpResource, StdioTransportParams, HttpTransportParams,
    BaseMcpService, McpEchoService
)
from .wot_resource import WoTResource
from .resource_executor import ResourceExecutor

__all__ = [
    "BaseResource",
    "ResourceConfig",
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
    "ResourceExecutor",
]
