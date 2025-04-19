"""Resource Selection Example

This example demonstrates how to create and use different types of resources with an agent,
including how the agent intelligently selects the appropriate resource for each task.

Key concepts demonstrated:
1. Creating custom resources by extending BaseResource
2. Using MCP (Model Control Protocol) resources
3. Creating specialized agents as resources
4. Resource selection based on task requirements
5. Combining multiple resources in a single agent

What you'll learn:
1. How to create custom resources for specific functionalities
2. How to integrate MCP services as resources
3. How to create specialized agents as resources
4. How the agent automatically selects the most appropriate resource for each task
5. How to combine different types of resources in a single agent

The example implements a trip planning assistant that can:
1. Research tourist attractions (using researcher agent)
2. Check weather conditions (using weather MCP service)
3. Find restaurant recommendations (using restaurant resource)
4. Plan transportation (using transport resource)

Expected output:
- The agent will process the user's query and select appropriate resources for each task
- For task 1: Uses the researcher agent to gather information
- For task 2: Uses the weather MCP service to get forecast
- For task 3: Uses the restaurant resource to get recommendations
- The final result will be a comprehensive plan combining all gathered information
"""

from typing import Any, Dict

from opendxa.agent import Agent
from opendxa.agent.resource import (
    AgentResource,
)
from opendxa.common.resource.base_resource import BaseResource, ResourceResponse
from opendxa.common.resource.mcp.mcp_resource import McpResource, StdioTransportParams

print("\n=== Starting Resource Selection Example ===")
print("This example demonstrates how an agent can intelligently select and use different resources")
print("based on the task requirements.\n")

WEATHER_SERVICE_NAME = "weather_mcp_service"
WEATHER_TOOL_NAME = "get_forecast"
WEATHER_TOOL_ARGUMENTS = {"latitude": 37.7749, "longitude": -122.4194}
WEATHER_SERVICE_SCRIPT = "opendxa/common/resource/mcp/mcp_weather_service.py"


class RestaurantOptions(BaseResource):
    """Resource for finding and booking restaurants."""

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        # Mock implementation - would call restaurant API
        return ResourceResponse(
            success=True,
            content={
                "restaurants": [
                    {
                        "name": "Park Bistro",
                        "cuisine": "American",
                        "rating": 4.5,
                        "price": "$$",
                        "location": "123 Park St",
                        "available_times": ["1:00 PM", "2:00 PM", "3:00 PM"],
                    },
                    {
                        "name": "Garden Cafe",
                        "cuisine": "Farm-to-table",
                        "rating": 4.7,
                        "price": "$$$",
                        "location": "456 Garden Ave",
                        "available_times": ["2:30 PM", "3:30 PM"],
                    },
                ]
            },
        )


class TransportOptions(BaseResource):
    """Resource for checking transportation options."""

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        # Mock implementation - would call transport API
        return ResourceResponse(
            success=True,
            content={
                "options": [
                    {
                        "mode": "bus",
                        "route": "45",
                        "duration": "20 mins",
                        "cost": "$2.50",
                    },
                    {"mode": "rideshare", "duration": "10 mins", "cost": "$15.00"},
                ]
            },
        )


def main():
    """Main function to run the resource selection example."""

    print("\n=== Step 1: Initializing Resources ===")
    print("Creating custom resources for restaurant and transport services...")

    # Initialize resources
    restaurant_options = RestaurantOptions(name="restaurant_service", description="Provides access to restaurant information and booking")
    transport_options = TransportOptions(name="transport_service", description="Provides access to transportation information")
    print("✓ Restaurant and transport resources created")

    print("\nInitializing weather MCP service...")
    weather = McpResource(name=WEATHER_SERVICE_NAME, transport_params=StdioTransportParams(server_script=WEATHER_SERVICE_SCRIPT))
    print("✓ Weather MCP service initialized")

    print("\n=== Step 2: Creating Specialized Agents ===")
    print("Setting up planner and researcher agents with specific roles...")

    # Create specialized agents
    planner = AgentResource(
        name="planner",
        description="Agent responsible for creating structured plans and coordinating activities based on available information",
        agent=Agent("planner").with_llm({"model": "openai:gpt-4o-mini", "temperature": 0.7, "max_tokens": 1000}),
    )
    print("✓ Planner agent created and configured")

    researcher = AgentResource(
        name="researcher",
        description="Agent focused on gathering, analyzing and synthesizing information from multiple sources to support decision making",
        agent=Agent("researcher").with_llm({"model": "openai:gpt-4o-mini", "temperature": 0.7, "max_tokens": 1000}),
    )

    print("\n=== Step 3: Setting Up Main Agent ===")
    print("Creating main planning assistant with all resources...")

    # Create main agent with all resources
    agent = Agent("planning_assistant")
    agent.with_llm({"model": "openai:gpt-4o-mini", "temperature": 0.7, "max_tokens": 1000})
    agent.with_resources(
        {
            "weather": weather,
            "restaurant_options": restaurant_options,
            "transport_options": transport_options,
            "planner": planner,
            "researcher": researcher,
        }
    )
    print("✓ Main agent created with all resources attached")

    print("\n=== Step 5: Processing User Query ===")
    print("The agent will now process the query and select appropriate resources for each task...")

    query = (
        "I'm in San Francisco and would like to plan a nice out-of-town trip. "
        "Could you help me plan: "
        "1. Plan how to get information about the best places to visit in San Francisco "
        "2. Check the weather for this afternoon "
        "3. Suggest the restaurant to go to "
        "Please provide a detailed plan considering all these factors."
    )
    print("\nUser Query:")
    print("-" * 50)
    print(query)
    print("-" * 50)

    print("\nProcessing query...")
    result = agent.ask(query)

    print("\n=== Final Result ===")
    print("+" * 100)
    print(f"\nRESULT: \n{result}")
    print("+" * 100)
    print("\n=== Resource Selection Example Complete ===")


if __name__ == "__main__":
    main()
