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
- MCPClient: Main client class that wraps the MCP client session with transport management.

Usage Example:
    client = MCPClient(url="http://localhost:8000/mcp")
    async with client as session:
        tools = await session.list_tools()

Design Notes:
- Transport validation is performed during client instantiation, ensuring only valid transports are used.
- The client is compatible with both synchronous and asynchronous usage patterns.
- Raises `ValueError` if no valid transport can be found for the provided arguments.

"""

from mcp.client.session import ClientSession

from dana.common.mixins.loggable import Loggable
from dana.common.utils.misc import Misc
from dana.integrations.mcp.client.transport import BaseTransport, MCPHTTPTransport, MCPSSETransport


class MCPClient(Loggable):
    def __init__(self, *args, **kwargs):
        Loggable.__init__(self)

        # Validate transport and store it
        self.transport = self._validate_transport(*args, **kwargs)
        self._session = None
        self._streams_context = None

    async def __aenter__(self) -> ClientSession:
        """Async context manager entry - create fresh streams and return session."""
        from mcp.client.sse import sse_client
        from mcp.client.streamable_http import streamablehttp_client

        # Create streams context based on transport type
        if isinstance(self.transport, MCPSSETransport):
            self._streams_context = sse_client(url=self.transport.url)
        elif isinstance(self.transport, MCPHTTPTransport):
            self._streams_context = streamablehttp_client(url=self.transport.url)
        else:
            raise ValueError(f"Invalid transport type: {type(self.transport)}")

        # Get the streams - handle different return patterns
        streams_result = await self._streams_context.__aenter__()
        if isinstance(self.transport, MCPSSETransport):
            read_stream, write_stream = streams_result
        elif isinstance(self.transport, MCPHTTPTransport):
            read_stream, write_stream, _ = streams_result
        else:
            raise ValueError(f"Invalid transport type: {type(self.transport)}")

        # Create and initialize the session
        self._session = ClientSession(read_stream, write_stream)
        session = await self._session.__aenter__()
        await session.initialize()

        return session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        try:
            if self._session:
                await self._session.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            if self._streams_context:
                await self._streams_context.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None
            self._streams_context = None

    @classmethod
    def _validate_transport(cls, *args, **kwargs) -> BaseTransport:
        for transport_cls in [MCPSSETransport, MCPHTTPTransport]:
            parse_result = transport_cls.parse_init_params(*args, **kwargs)
            transport = transport_cls(*parse_result.matched_args, **parse_result.matched_kwargs)
            is_valid = Misc.safe_asyncio_run(cls._try_client_with_valid_transport, transport)
            if is_valid:
                return transport
        raise ValueError(f"No valid transport found kwargs : {kwargs}")

    @classmethod
    async def _try_client_with_valid_transport(cls, transport: BaseTransport) -> bool:
        """Test transport connection."""
        session_context = None
        streams_context = None

        try:
            from mcp.client.sse import sse_client
            from mcp.client.streamable_http import streamablehttp_client

            # Create streams context based on transport type
            if isinstance(transport, MCPSSETransport):
                streams_context = sse_client(url=transport.url)
                read_stream, write_stream = await streams_context.__aenter__()
            elif isinstance(transport, MCPHTTPTransport):
                streams_context = streamablehttp_client(url=transport.url)
                read_stream, write_stream, _ = await streams_context.__aenter__()
            else:
                raise ValueError(f"Invalid transport type: {type(transport)}")

            # Test the connection
            session_context = ClientSession(read_stream, write_stream)
            session = await session_context.__aenter__()

            # Initialize and test connection
            await session.initialize()
            response = await session.list_tools()
            tools = response.tools
            print(f"Connected to mcp server ({transport.url}) with {len(tools)} tools:", [tool.name for tool in tools])

            return True

        except BaseException:
            # Catch all exceptions including CancelledError during validation
            return False
        finally:
            # Clean up test connection - guard against cancellation during cleanup
            try:
                if session_context:
                    await session_context.__aexit__(None, None, None)
            except BaseException:
                # Swallow any exceptions during cleanup to prevent them from escaping
                pass
            try:
                if streams_context:
                    await streams_context.__aexit__(None, None, None)
            except BaseException:
                # Swallow any exceptions during cleanup to prevent them from escaping
                pass
