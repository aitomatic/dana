#!/usr/bin/env python3
"""
Use Case 08: Dana Agent Deployment via MCP Protocol

This example demonstrates deploying and accessing Dana agents via the MCP (Model Context Protocol).
Shows how to expose Dana AI capabilities as standardized tools that can be consumed by
AI assistants and MCP-compatible applications.

Business Value:
- Deploy Dana agents as MCP-compatible tools
- Enable AI assistant integration (Claude, ChatGPT, etc.)
- Standardized tool interface for AI agent capabilities
- Seamless integration with MCP ecosystem

Prerequisites:
1. Deploy the Dana agent: dana deploy dana/manufacturing_qa_agent.na --protocol mcp
2. Ensure agent is running on localhost:8000 (default)

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import argparse
import asyncio
import sys
from typing import Any

from fastmcp import Client


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    try:
        import fastmcp  # noqa: F401

        print("✅ All dependencies installed correctly")
        return True
    except ImportError:
        print("❌ Missing dependency: fastmcp")
        print("Please install: pip install fastmcp")
        return False


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Dana MCP Client Example")
    parser.add_argument("--port", type=int, default=8000, help="Port to connect to (default: 8000)")
    parser.add_argument("--agent-name", type=str, default="Manufacturing-QA-Agent", help="Name of the Dana agent to connect to")
    return parser.parse_args()


class MCPDanaClient:
    """MCP client for connecting to Dana agents."""

    def __init__(self, base_url: str, agent_name: str):
        self.base_url = base_url.rstrip("/")
        self.agent_name = agent_name
        self.mcp_endpoint = f"{base_url}/{agent_name}/mcp"
        print(f"MCP endpoint: {self.mcp_endpoint}")
        self.client = Client(self.mcp_endpoint)

    async def get_tools(self) -> dict[str, Any] | None:
        """Get available tools from the MCP server."""
        try:
            async with self.client:
                result = await self.client.list_tools()
                return {"tools": result} if result else None

        except Exception as e:
            print(f"❌ Error getting tools: {e}")
            return None

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
        """Call a tool on the MCP server."""
        try:
            async with self.client:
                result = await self.client.call_tool(tool_name, arguments)
                if result and isinstance(result, list) and len(result) > 0:
                    content = result[0]
                    if hasattr(content, "text"):
                        return content.text
                    return str(content)
                return "No result content"

        except Exception as e:
            print(f"❌ Error calling tool: {e}")
            return None

    async def solve_query(self, query: str) -> str | None:
        """Send a query to the Dana agent's solve function."""
        return await self.call_tool("solve", {"query": query})


async def get_agent_info(client: MCPDanaClient) -> None:
    """Retrieve and display agent information."""
    try:
        print("\n=== Agent Information ===")
        tools = await client.get_tools()

        if tools and "tools" in tools:
            for tool in tools["tools"]:
                print(f"Tool: {tool.name}")
                print(f"Description: {tool.description}")

                if tool.inputSchema:
                    schema = tool.inputSchema
                    print(f"Input Schema: {schema}")
                    if schema["properties"]:
                        print("Parameters:")
                        for param, details in schema["properties"].items():
                            param_type = details["type"]
                            # Skip description if not present
                            print(f"  - {param} ({param_type})")
                print()
        else:
            print("⚠️ Could not retrieve tool information")

    except Exception as e:
        print(f"⚠️ Could not retrieve agent info: {e}")


async def test_agent_queries(client: MCPDanaClient) -> None:
    """Test manufacturing quality queries."""
    test_queries = [
        "Analyze batch quality: defect rate 2.3%, Cpk=1.1, 5 dimensional failures out of 100 parts",
        "Equipment alert: CNC machine temperature 95°C, vibration 0.8mm/s, cycle time increased 15%",
        "Quality deviation investigation: adhesive bond strength dropped from 850N to 720N average",
        "Process optimization request: injection molding cycle 45s, 8% scrap rate, target <5%",
    ]

    print("🤖 Testing MCP Agent Communication")
    print("-" * 40)

    for i, query in enumerate(test_queries, 1):
        print(f"\n📤 Test {i}: {query}")

        try:
            response = await client.solve_query(query)
            if response:
                print(f"📥 Response: {response}")
            else:
                print("❌ No response received")
        except Exception as e:
            print(f"❌ Error: {e}")

        if i < len(test_queries):
            await asyncio.sleep(1)


async def main() -> int:
    """Main execution function."""
    print("🎯 Use Case 08: Dana Agent Deployment via MCP Protocol")
    print("=" * 60)

    if not check_dependencies():
        return 1

    args = parse_arguments()
    base_url = f"http://localhost:{args.port}"

    print(f"🔌 Connecting to MCP agent at: {base_url}/{args.agent_name.lower()}")

    try:
        client = MCPDanaClient(base_url, args.agent_name.lower())

        await get_agent_info(client)
        await test_agent_queries(client)

        print("\n✅ Dana Agent Deployment via MCP Success!")
        print("💡 Key Benefits:")
        print("   - Dana agents deployed as MCP-compatible tools")
        print("   - Direct AI assistant integration capabilities")
        print("   - Standardized tool interface for AI workflows")
        print("   - Seamless MCP ecosystem compatibility")
        return 0

    except Exception as e:
        print(f"\n❌ Error connecting to agent: {e}")
        print("\nPossible reasons:")
        print("- The endpoint URL is incorrect")
        print("- The manufacturing QA agent is not running")
        print("- Network connectivity issues")
        print("\n📋 To deploy the agent, run:")
        print("   dana deploy dana/manufacturing_qa_agent.na --protocol mcp")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)
