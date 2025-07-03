"""MCP (Model Context Protocol) Integration."""

# Import core MCP resource
from .core.mcp_resource import McpResource

# Import A2A (Agent-to-Agent) components
from .a2a.resource.a2a.a2a_agent import A2AAgent

__all__ = [
    # Core MCP
    'McpResource',
    # Agent-to-Agent
    'A2AAgent'
]