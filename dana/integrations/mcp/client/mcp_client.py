"""
MCP Client: Unified Interface for Model Context Protocol (MCP) Server Communication

This module provides the `MCPClient` class, a high-level client for interacting with MCP servers
using various transport mechanisms (e.g., SSE, HTTP). It abstracts transport selection and
resource management, offering a seamless interface for both synchronous and asynchronous workflows.

Key Features:
- Automatic transport selection: Chooses the appropriate transport (SSE, HTTP, etc.) based on initialization arguments.
- Async context management: Ensures proper resource handling for all operations.
- Extensible: Easily supports new transport types by extending the transport validation logic.
- Logging: Integrates with the application's logging system for traceability.

Classes:
- MCPMetaclass: Custom metaclass that intercepts instantiation to validate and select the correct transport.
- MCPClient: Main client class, inheriting from `fastmcp.Client` and a logging mixin, using the metaclass for transport management.

Usage Example:
    client = MCPClient(url="http://localhost:8000/mcp")
    print(client.transport)

Design Notes:
- Transport validation is performed before client instantiation, ensuring only valid transports are used.
- The client is compatible with both synchronous and asynchronous usage patterns.
- Raises `ValueError` if no valid transport can be found for the provided arguments.

"""

from typing import Any

from mcp.client.session import ClientSession as Client

from dana.common.mixins.loggable import Loggable
from dana.common.utils.misc import Misc
from dana.integrations.mcp.client.transport import BaseTransport, MCPHTTPTransport, MCPSSETransport


class MCPMetaclass(type):
    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        transport, unmatched_args, unmatched_kwargs = cls._validate_transport(*args, **kwds)
        return super().__call__(transport=transport, *unmatched_args, **unmatched_kwargs)


class MCPClient(Client, Loggable, metaclass=MCPMetaclass):
    def __init__(self, *args, **kwargs):
        Client.__init__(self, *args, **kwargs)
        Loggable.__init__(self)

    @classmethod
    def _validate_transport(cls, *args, **kwargs) -> tuple[BaseTransport, list[Any], dict[str, Any]]:
        for transport_cls in [MCPSSETransport, MCPHTTPTransport]:
            parse_result = transport_cls.parse_init_params(*args, **kwargs)
            transport = transport_cls(*parse_result.matched_args, **parse_result.matched_kwargs)
            result = Misc.safe_asyncio_run(cls._try_client_with_valid_transport, transport)
            if result:
                return transport, parse_result.unmatched_args, parse_result.unmatched_kwargs
        raise ValueError(f"No valid transport found kwargs : {kwargs}")

    @classmethod
    async def _try_client_with_valid_transport(cls, transport: BaseTransport) -> bool:
        try:
            async with Client(transport=transport) as test_client:
                await test_client.list_tools()
                await test_client.list_resources()
                await test_client.list_prompts()
                return True
        except Exception:
            pass
        return False
