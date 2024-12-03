"""Example of WebSocket-based agent solving problems."""

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

from dotenv import load_dotenv
load_dotenv("../.env")

async def main():
    """Run WebSocket-based solver example."""
    api_key = os.getenv('OPENAI_API_KEY')
    websocket_url = os.getenv('WEBSOCKET_URL')
    if not api_key or not websocket_url:
        raise ValueError(
            "Both OPENAI_API_KEY and WEBSOCKET_URL environment variables are required"
        )

    try:
        # Create and run WebSocket agent
        async with create_agent("websocket", {
            "name": "websocket_solver",
            "api_key": api_key,
            "websocket_url": websocket_url,
            "model": "gpt-4",
            "system_prompt": """You are a problem-solving agent that communicates through WebSocket.
            Break down problems systematically and explain your reasoning clearly.
            
            Key principles:
            - Observe: Gather all relevant information
            - Orient: Analyze the context and constraints
            - Decide: Choose the best approach
            - Act: Execute the solution systematically"""
        }) as agent:
            
            # Run with progress updates
            async for progress in agent.run_with_progress({
                "domain": "general",
                "style": "systematic"
            }):
                if progress.is_progress:
                    print(f"Progress: {progress.percent}% - {progress.message}")
                elif progress.is_result:
                    result = progress.result
                    if result["success"]:
                        print("Session completed successfully")
                        print(f"Final result: {result['output']}")
                    else:
                        print(f"Session failed: {result['error']}")

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