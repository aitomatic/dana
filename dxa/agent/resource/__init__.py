"""DXA resource module."""

from .agent_resource import AgentResource
from .base_resource import BaseResource, ResourceResponse
from .expert_resource import ExpertResource
from .human_resource import HumanResource
from .llm_resource import LLMResource
from .mcp import McpResource, McpTransportType, McpConnectionParams, BaseMcpService, McpEchoService
from .resource_factory import ResourceFactory
from .wot_resource import WoTResource
from .resource_executor import ResourceExecutor

__all__ = [
    "BaseResource",
    "LLMResource",
    "ExpertResource",
    "ResourceFactory",
    "HumanResource",
    "McpResource",
    "McpTransportType",
    "McpConnectionParams",
    "BaseMcpService",
    "McpEchoService",
    "WoTResource",
    "AgentResource",
    "ResourceResponse",
    "ResourceExecutor",
]
