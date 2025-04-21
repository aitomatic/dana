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
from opendxa.base.resource.queryable import QueryResponse
from opendxa.base.resource.storage_backed_resource import StorageBackedResource, StorageEntry

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
    "QueryResponse",
    "StorageBackedResource",
    "StorageEntry",
]
