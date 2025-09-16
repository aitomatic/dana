"""MCP Querying with MCP Python SDK."""

import asyncio
from pprint import pformat

from loguru import logger
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

WEATHER_MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"

CITY = "Tokyo"
# START_DATE = "2025-06-26"
# END_DATE = "2025-06-30"


# inspect server
async def inspect_server():
    """Inspect prompts, resources and tools available on the MCP server."""
    # Use the same pattern as Dana's MCP client implementation
    streams_context = streamablehttp_client(WEATHER_MCP_SERVER_URL)
    streams = await streams_context.__aenter__()

    try:
        # Create session from first two streams only (read_stream, write_stream)
        # The third item is a callable function that causes the timeout error
        read_stream, write_stream = streams[:2]
        client_session = ClientSession(read_stream, write_stream)
        session = await client_session.__aenter__()

        try:
            await session.initialize()

            prompts, resources, resource_templates, tools = await asyncio.gather(
                session.list_prompts(),
                session.list_resources(),
                session.list_resource_templates(),
                session.list_tools(),
                return_exceptions=True,
            )

            logger.debug(f"MCP Prompts:\n\n{pformat(prompts, indent=2)}\n")
            logger.debug(f"MCP Resources:\n\n{pformat(resources, indent=2)}\n")
            logger.debug(f"MCP Resource templates:\n\n{pformat(resource_templates, indent=2)}\n")
            logger.debug(f"MCP Tools:\n\n{pformat(tools, indent=2)}\n")
        finally:
            await client_session.__aexit__(None, None, None)
    finally:
        await streams_context.__aexit__(None, None, None)


# call tool
async def get_weather():
    # Use the same pattern as Dana's MCP client implementation
    streams_context = streamablehttp_client(WEATHER_MCP_SERVER_URL)
    streams = await streams_context.__aenter__()

    try:
        # Create session from first two streams only (read_stream, write_stream)
        # The third item is a callable function that causes the timeout error
        read_stream, write_stream = streams[:2]
        client_session = ClientSession(read_stream, write_stream)
        session = await client_session.__aenter__()

        try:
            await session.initialize()
            return await session.call_tool(
                name="get_current_weather",
                arguments={
                    "city": CITY,
                    # "start_date": START_DATE, "end_date": END_DATE
                },
            )
        finally:
            await client_session.__aexit__(None, None, None)
    finally:
        await streams_context.__aexit__(None, None, None)


if __name__ == "__main__":
    # Only run if executed directly, not when imported
    print("Running MCP client examples...")
    asyncio.run(inspect_server())
    print(asyncio.run(get_weather()))
