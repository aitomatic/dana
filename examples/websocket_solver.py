"""Example of WebSocket-based agent solving problems."""

import asyncio
import os
from dxa.agents.websocket import WebSocketAgent
from dxa.core.reasoning.ooda import OODALoopReasoning

async def main():
    """Run WebSocket-based solver example."""
    api_key = os.getenv('OPENAI_API_KEY')
    websocket_url = os.getenv('WEBSOCKET_URL')
    if not api_key or not websocket_url:
        raise ValueError(
            "Both OPENAI_API_KEY and WEBSOCKET_URL environment variables are required"
        )

    # Initialize reasoning pattern
    reasoning = OODALoopReasoning()
    await reasoning.initialize()

    try:
        # Create WebSocket agent
        agent = WebSocketAgent(
            name="websocket_solver",
            llm_config={"api_key": api_key},
            reasoning=reasoning,
            websocket_url=websocket_url,
            system_prompt="""You are a problem-solving agent that communicates through WebSocket.
            Break down problems systematically and explain your reasoning clearly."""
        )

        async with agent:  # Uses context manager for cleanup
            result = await agent.run({
                "domain": "general",
                "style": "systematic"
            })
            
            if result["success"]:
                print("Session completed successfully")
                print("\nState History:")
                for state in result["state_history"]:
                    print(f"\nTimestamp: {state['timestamp']}")
                    print(f"State: {state['new_state']}")
                    print(f"Reason: {state['reason']}")
            else:
                print(f"Session failed: {result.get('error')}")

    finally:
        await reasoning.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 