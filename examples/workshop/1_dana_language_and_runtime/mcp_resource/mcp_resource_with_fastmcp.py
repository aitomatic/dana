"""MCP Querying with FastMCP."""

import asyncio
from pprint import pformat

from fastmcp.client.client import Client
from fastmcp.client.transports import StreamableHttpTransport
from loguru import logger

WEATHER_MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"

CITY = "Tokyo"
START_DATE = "2025-06-26"
END_DATE = "2025-06-30"

# instantiate MCP client
mcp_client = Client(transport=StreamableHttpTransport(url=WEATHER_MCP_SERVER_URL),
                    roots=None,
                    sampling_handler=None,
                    log_handler=None,
                    message_handler=None,
                    progress_handler=None,
                    timeout=None)

# inspect server
async def inspect_server():
    """Inspect prompts, resources and tools available on the MCP server."""
    async with mcp_client:
        prompts, resources, resource_templates, tools = \
            await asyncio.gather(mcp_client.list_prompts(),
                                 mcp_client.list_resources(),
                                 mcp_client.list_resource_templates(),
                                 mcp_client.list_tools(),
                                 return_exceptions=True)

        logger.debug(f"MCP Prompts:\n\n{pformat(prompts, indent=2)}\n")
        logger.debug(f"MCP Resources:\n\n{pformat(resources, indent=2)}\n")
        logger.debug(f"MCP Resource templates:\n\n{pformat(resource_templates, indent=2)}\n")
        logger.debug(f"MCP Tools:\n\n{pformat(tools, indent=2)}\n")

asyncio.run(inspect_server())

# call tool
async def get_weather():
    async with mcp_client:
        return await mcp_client.call_tool(name="get_weather_by_datetime_range",
                                          arguments={'city': CITY, 'start_date': START_DATE, 'end_date': END_DATE},
                                          timeout=None,
                                          progress_handler=None)

print(asyncio.run(get_weather()))
