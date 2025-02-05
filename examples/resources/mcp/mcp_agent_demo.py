"""MCP Echo Service Demo

Demonstrates:
1. Agent configuration with MCP resource
2. MCP context management
3. Model execution through agent
"""

import asyncio
from dxa.agent import Agent
from dxa.agent.resource import McpLocalResource, McpRemoteResource
from dxa.common import DXA_LOGGER

DXA_LOGGER.basicConfig(level=DXA_LOGGER.DEBUG)
logger = DXA_LOGGER.getLogger(__file__.rsplit('/', maxsplit=1)[-1])

MCP_SERVICE_NAME = "local_echo"
MCP_TOOL_NAME = "echo"
MCP_TOOL_ARGUMENTS = {"message": "Hello from DXA agent!"}
MCP_SERVICE_SCRIPT = "/Users/ctn/src/aitomatic/dxa/dxa/agent/resource/mcp/services/mcp_echo_service.py"
MCP_SCRIPT_COMMAND = "python3"

async def main():
    """Main function"""
    # Create agent with MCP resources
    logger.debug("Creating agent with MCP resources")
    agent = Agent("MCP-Using-Agent").with_resources({
        MCP_SERVICE_NAME: McpLocalResource(
            name=MCP_SERVICE_NAME,
            server_script=MCP_SERVICE_SCRIPT,
            command=MCP_SCRIPT_COMMAND
        ),
        "remote_time": McpRemoteResource(
            name="remote_time",
            base_url="http://time.service/mcp"
        )
    })

    # Execute queries
    logger.debug("Executing %s tool", MCP_TOOL_NAME)
    response = await agent.resources[MCP_SERVICE_NAME].query({
        "tool": "ping"
    })

    response = await agent.resources[MCP_SERVICE_NAME].query({
        "tool": "echo",
        "arguments": {"message": "Hello from DXA agent!"}
    })

    # time_response = await agent.resources["remote_time"].query({
    #     "tool": "time",
    #     "arguments": {}
    # })

    print(f"{MCP_SERVICE_NAME} %{MCP_TOOL_NAME} response: {response.content}")
    # print(f"Current time: {time_response.content}")

if __name__ == "__main__":
    logger.debug("Starting MCP agent demo environment")
    asyncio.run(main()) 