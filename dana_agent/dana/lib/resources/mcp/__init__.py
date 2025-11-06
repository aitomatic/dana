"""
MCP (Model Context Protocol) Resources Package.

This package provides MCP client resources for communicating with various
MCP-compatible services, including both HTTP-based and local MCP servers.
"""

from .clients import BrightQueryResource, GitHubMCPResource, SlackMCPResource
from .mcp_client import MCPClientResource


__all__ = [
    "MCPClientResource",
    "BrightQueryResource",
    "GitHubMCPResource",
    "SlackMCPResource",
]
