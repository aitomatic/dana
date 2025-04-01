from dxa.agent import Agent
from dxa.agent.resource import BaseResource, AgentResource
from dxa.agent.resource.mcp import McpLocalResource
from typing import Dict, Any

MCP_SERVICE_NAME = "weather_mcp_service"
MCP_TOOL_NAME = "get_forecast"
MCP_TOOL_ARGUMENTS = {"latitude": 37.7749, "longitude": -122.4194}
MCP_SERVICE_SCRIPT = "dxa/agent/resource/mcp/mcp_services/mcp_weather_service.py"
MCP_SCRIPT_COMMAND = "python3"

class RestaurantResource(BaseResource):
    """Resource for finding and booking restaurants."""

    def __init__(self, name: str):
        super().__init__(name, "Provides access to restaurant information and booking")

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Mock implementation - would call restaurant API
        return {
            "success": True,
            "content": {
                "restaurants": [
                    {
                        "name": "Park Bistro",
                        "cuisine": "American",
                        "rating": 4.5,
                        "price": "$$",
                        "location": "123 Park St",
                        "available_times": ["1:00 PM", "2:00 PM", "3:00 PM"]
                    },
                    {
                        "name": "Garden Cafe",
                        "cuisine": "Farm-to-table",
                        "rating": 4.7,
                        "price": "$$$",
                        "location": "456 Garden Ave",
                        "available_times": ["2:30 PM", "3:30 PM"]
                    }
                ]
            },
            "request": request
        }

class TransportResource(BaseResource):
    """Resource for checking transportation options."""

    def __init__(self, name: str):
        super().__init__(name, "Provides access to transportation information")

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Mock implementation - would call transport API
        return {
            "success": True,
            "content": {
                "options": [
                    {
                        "mode": "bus",
                        "route": "45",
                        "duration": "20 mins",
                        "cost": "$2.50"
                    },
                    {
                        "mode": "rideshare",
                        "duration": "10 mins",
                        "cost": "$15.00"
                    }
                ]
            },
            "request": request
        }

def main():
    # Initialize resources
    restaurant = RestaurantResource(name="restaurant_service")
    transport = TransportResource(name="transport_service")
    weather = McpLocalResource(
        name=MCP_SERVICE_NAME,
        server_script=MCP_SERVICE_SCRIPT,
        command=MCP_SCRIPT_COMMAND
    )
    # weather = McpLocalResource(
    #     name="weather",
    #     connection_params={
    #         "command": "npx",
    #         "args": ["-y", "@h1deya/mcp-server-weather"]
    #     }
    # )

    # Create specialized agents
    planner_agent = Agent("planner", "Agent responsible for creating structured plans and coordinating activities based on available information")
    planner_agent.with_llm({
        "model": "openai:gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000
    })
    researcher_agent = Agent("researcher", "Agent focused on gathering, analyzing and synthesizing information from multiple sources to support decision making")
    researcher_agent.with_llm({
        "model": "openai:gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000
    })

    # Create agent resource
    agent_pool = AgentResource("agent_pool", {
        "planner": planner_agent,
        "researcher": researcher_agent
    })

    # Create main agent with all resources
    agent = Agent("planning_assistant")
    agent.with_resources({
        "weather": weather,
        "restaurant": restaurant,
        "transport": transport,
        "agents": agent_pool
    })

    # Configure LLM with more specific parameters
    agent.with_llm({
        "model": "openai:gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000
    })

    query =  "I'm in San Francisco and would like to plan a nice out-of-town trip. " \
        "Could you help me plan: " \
        "1. Plan how to get information about the best places to visit in San Francisco " \
        "2. Check the weather for this afternoon " \
        "3. Suggest the restaurant to go to " \
        "Please provide a detailed plan considering all these factors."

    # Agent should select 'researcher agent resource' (not planner agent) for task 1
    # Agent should select 'weather resource (get_forecast mcp tool)' for task 2
    # Agent should select 'restaurant resource' for task 3
    result = agent.ask(query)
    
    print("+"*100)
    print(f"\nRESULT: \n{result}")
    print("+"*100)


if __name__ == "__main__":
    main()