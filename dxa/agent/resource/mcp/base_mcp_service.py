"""Base MCP Service class"""

import functools
from abc import ABC
from typing import Literal, Optional
from mcp.server.fastmcp import FastMCP
from ....common import DXA_LOGGER

# This is to pass into derived classes to use because "self" is not set when called by the MCP framework
_SERVER = FastMCP("FastMCP Server")
_SELF: Optional['BaseMcpService'] = None
_TOOL_NAMES = []

class BaseMcpService(ABC):
    """Baes MCP Service class"""

    def __init__(self, transport: Literal['stdio', 'sse'] = 'stdio') -> None:
        """Initialize"""
        self.logger = DXA_LOGGER.getLogger(__file__.rsplit('/', maxsplit=1)[-1])
        self.transport: Literal['stdio', 'sse'] = transport
        global _SELF  # pylint: disable=global-statement
        _SELF = self
    
    def run(self):
        """Run the service"""
        self.logger.debug("Starting %s service", self.__class__.__name__)
        _SERVER.run(transport=self.transport) 

    @classmethod
    def tool(cls, name: str | None = None, description: str | None = None):
        """Decorator to register the function as a tool"""
        def decorator_tool(func):

            @functools.wraps(func)
            def wrapper_tool(*args, **kwargs):
                # Replace the first arg placeholder with the actual SELF
                if args:
                    args = (_SELF,) + args[1:]
                return func(*args, **kwargs)

            if _SERVER is not None:
                # Don't register if tool name already registered in _TOOL_NAMES
                if name not in _TOOL_NAMES:
                    _SERVER.add_tool(wrapper_tool, name=name, description=description)
                    _TOOL_NAMES.append(name)

            return wrapper_tool

        return decorator_tool 