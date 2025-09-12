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
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

class MCPClient(Loggable):
    def __init__(self, *args, **kwargs):
        Loggable.__init__(self)

        # Validate transport and store it
        self._streams_context = None
        self._session = None
        self._streams_context_cls, self._streams_context_args, self._streams_context_kwargs = self._validate_stream_context(*args, **kwargs)

    async def __aenter__(self) -> ClientSession:
        """Async context manager entry - create fresh streams and return session."""
        if self._streams_context is None:
            self._streams_context = self._streams_context_cls(*self._streams_context_args, **self._streams_context_kwargs)
        # Get the streams - handle different return patterns
        streams_result = await self._streams_context.__aenter__()
        read_stream, write_stream = streams_result[0], streams_result[1]

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
    def _validate_stream_context(cls, *args, **kwargs) -> tuple[type, list, dict]:
        for stream_context_cls in [sse_client, streamablehttp_client]:
            parse_result = Misc.parse_args_kwargs(stream_context_cls, *args, **kwargs)
            stream_context = stream_context_cls(*parse_result.matched_args, **parse_result.matched_kwargs)
            is_valid = Misc.safe_asyncio_run(cls._try_client_with_valid_stream_context, stream_context, \
                                             *parse_result.matched_args, **parse_result.matched_kwargs)
            if is_valid:
                return stream_context_cls, parse_result.matched_args, parse_result.matched_kwargs
        raise ValueError(f"No valid stream context found kwargs : {kwargs}")


    @classmethod
    async def _try_client_with_valid_stream_context(cls, stream_context, *args, **kwargs) -> bool:
        """Test stream context connection."""
        session_context = None
        streams_context = None

        try:
            # Create streams context based on stream context type
            streams_context = stream_context
            stream_tuple = await streams_context.__aenter__()
            read_stream, write_stream = stream_tuple[0], stream_tuple[1]

            # Test the connection
            session_context = ClientSession(read_stream, write_stream)
            session = await session_context.__aenter__()

            # Initialize and test connection
            await session.initialize()
            response = await session.list_tools()
            tools = response.tools
            print(f"Connected to mcp server {args}, {kwargs} with {len(tools)} tools:", [tool.name for tool in tools])

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