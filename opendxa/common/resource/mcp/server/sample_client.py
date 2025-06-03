import asyncio
from mcp.client.streamable_http import streamablehttp_client

from fastmcp.client.transports import StreamableHttpTransport

async def main():
    http_params = {
        "url": "http://localhost:8000",  # adjust if running on a different host/port
    }

    async with streamablehttp_client(**http_params) as client:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")

        # Call get_alerts tool
        print("\nCalling get_alerts('CA')...\n")
        alerts_result = await client.call_tool("get_alerts", {"state": "CA"})
        print(alerts_result)

        # Call get_forecast tool
        print("\nCalling get_forecast(latitude=37.7749, longitude=-122.4194)...\n")
        forecast_result = await client.call_tool("get_forecast", {
            "latitude": 37.7749,
            "longitude": -122.4194
        })
        print(forecast_result)

if __name__ == "__main__":
    asyncio.run(main())
