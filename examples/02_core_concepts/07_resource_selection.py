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

from dxa.agent import Agent
from dxa.agent.resource import (
    AgentResource,
    BaseResource,
    ResourceResponse,
    McpResource,
    McpTransportType,
    McpConnectionParams
)

print("\n=== Starting Resource Selection Example ===")
print(
    "This example demonstrates how an agent can intelligently select and use different resources"
)
print("based on the task requirements.\n")

MCP_SERVICE_NAME = "weather_mcp_service"
MCP_TOOL_NAME = "get_forecast"
MCP_TOOL_ARGUMENTS = {"latitude": 37.7749, "longitude": -122.4194}
MCP_SERVICE_SCRIPT = "dxa/agent/resource/mcp/mcp_services/mcp_weather_service.py"
MCP_SCRIPT_COMMAND = "python3"


class RestaurantResource(BaseResource):
    """Resource for finding and booking restaurants."""

    def __init__(self, name: str):
        super().__init__(name, "Provides access to restaurant information and booking")

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


class TransportResource(BaseResource):
    """Resource for checking transportation options."""

    def __init__(self, name: str):
        super().__init__(name, "Provides access to transportation information")

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
    restaurant = RestaurantResource(name="restaurant_service")
    transport = TransportResource(name="transport_service")
    print("✓ Restaurant and transport resources created")

    print("\nInitializing weather MCP service...")
    weather = McpResource(
        name=MCP_SERVICE_NAME,
        connection_params=McpConnectionParams(
            transport_type=McpTransportType.STDIO,
            command=MCP_SCRIPT_COMMAND,
            args=[MCP_SERVICE_SCRIPT]
        )
    )
    print("✓ Weather MCP service initialized")

    print("\n=== Step 2: Creating Specialized Agents ===")
    print("Setting up planner and researcher agents with specific roles...")

    # Create specialized agents
    planner_agent = Agent(
        "planner",
        "Agent responsible for creating structured plans and coordinating "
        "activities based on available information",
    )
    planner_agent.with_llm(
        {"model": "openai:gpt-4o-mini", "temperature": 0.7, "max_tokens": 1000}
    )
    print("✓ Planner agent created and configured")

    researcher_agent = Agent(
        "researcher",
        "Agent focused on gathering, analyzing and synthesizing information "
        "from multiple sources to support decision making",
    )
    researcher_agent.with_llm(
        {"model": "openai:gpt-4o-mini", "temperature": 0.7, "max_tokens": 1000}
    )
    print("✓ Researcher agent created and configured")

    print("\n=== Step 3: Creating Agent Pool ===")
    print("Combining specialized agents into a resource pool...")

    # Create agent resource
    agent_pool = AgentResource(
        "agent_pool", {"planner": planner_agent, "researcher": researcher_agent}
    )
    print("✓ Agent pool created with planner and researcher agents")

    print("\n=== Step 4: Setting Up Main Agent ===")
    print("Creating main planning assistant with all resources...")

    # Create main agent with all resources
    agent = Agent("planning_assistant")
    agent.with_resources(
        {
            "weather": weather,
            "restaurant": restaurant,
            "transport": transport,
            "agents": agent_pool,
        }
    )
    print("✓ Main agent created with all resources attached")

    # Configure LLM with more specific parameters
    agent.with_llm(
        {"model": "openai:gpt-4o-mini", "temperature": 0.7, "max_tokens": 1000}
    )
    print("✓ LLM configured for the main agent")

    print("\n=== Step 5: Processing User Query ===")
    print(
        "The agent will now process the query and select appropriate resources for each task..."
    )

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

    print("\nExpected Resource Selection:")
    print("1. Task 1: Will use researcher agent to gather information")
    print("2. Task 2: Will use weather MCP service to get forecast")
    print("3. Task 3: Will use restaurant resource for recommendations")

    print("\nProcessing query...")
    result = agent.ask(query)

    print("\n=== Final Result ===")
    print("+" * 100)
    print(f"\nRESULT: \n{result}")
    print("+" * 100)
    print("\n=== Resource Selection Example Complete ===")


if __name__ == "__main__":
    main()
