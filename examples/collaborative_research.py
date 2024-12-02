"""Example of collaborative agents working on research."""

import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dxa.core.factory import create_agent
from dxa.common.errors import (
    ConfigurationError,
    ResourceError,
    AgentError,
    ReasoningError
)

async def main():
    """Run collaborative research example."""
    api_key = os.getenv('OPENAI_API_KEY')
    websocket_url = os.getenv('WEBSOCKET_URL')
    if not api_key or not websocket_url:
        raise ValueError(
            "Both OPENAI_API_KEY and WEBSOCKET_URL environment variables are required"
        )

    try:
        researcher_config = {
            "name": "researcher",
            "api_key": api_key,
            "model": "gpt-4",
            "reasoning": "chain-of-thought",
            "system_prompt": """You are a research specialist. 
            Analyze information systematically and draw well-supported conclusions."""
        }

        analyst_config = {
            "name": "analyst",
            "api_key": api_key,
            "model": "gpt-4",
            "websocket_url": websocket_url,
            "reasoning": "chain-of-thought",
            "system_prompt": """You are a data analyst.
            Process and analyze data to extract meaningful insights."""
        }

        coordinator_config = {
            "name": "coordinator",
            "api_key": api_key,
            "model": "gpt-4",
            "reasoning": "ooda-loop",
            "system_prompt": """You are a research coordinator.
            Coordinate between researchers and analysts to complete research tasks.
            Break down complex problems and delegate effectively."""
        }

        # Create specialized research agents using context managers
        async with \
                create_agent("console", researcher_config) as researcher, \
                create_agent("websocket", analyst_config) as analyst, \
                create_agent("console", coordinator_config) as coordinator:

            # Run the collaborative research task
            result = await coordinator.run({
                "research_topic": "Impact of AI on job markets",
                "required_analyses": [
                    "historical trends",
                    "current statistics",
                    "future projections"
                ],
                "output_format": "research report",
                "collaborators": {
                    "researcher": researcher,
                    "analyst": analyst
                }
            })
            
            if result["success"]:
                print("Research completed successfully")
                print("\nState History:")
                for state in result["state_history"]:
                    print(f"\nTimestamp: {state['timestamp']}")
                    print(f"State: {state['new_state']}")
                    print(f"Reason: {state['reason']}")
            else:
                print(f"Research failed: {result.get('error')}")

    except ValueError as e:
        print(f"Configuration error: {str(e)}")
    except ConfigurationError as e:
        print(f"Agent configuration error: {str(e)}")
    except ResourceError as e:
        print(f"Resource error: {str(e)}")
    except ReasoningError as e:
        print(f"Reasoning error: {str(e)}")
    except AgentError as e:
        print(f"Agent error: {str(e)}")
    except KeyError as e:
        print(f"Missing required configuration key: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 