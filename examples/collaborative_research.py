"""Example of collaborative agents working on research."""

import asyncio
import os
from dxa.agents.interactive import ConsoleAgent
from dxa.agents.websocket import WebSocketAgent
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.core.reasoning.ooda import OODALoopReasoning

async def main():
    """Run collaborative research example."""
    api_key = os.getenv('OPENAI_API_KEY')
    websocket_url = os.getenv('WEBSOCKET_URL')
    if not api_key or not websocket_url:
        raise ValueError(
            "Both OPENAI_API_KEY and WEBSOCKET_URL environment variables are required"
        )

    # Initialize reasoning patterns
    researcher_reasoning = ChainOfThoughtReasoning()
    analyst_reasoning = ChainOfThoughtReasoning()
    coordinator_reasoning = OODALoopReasoning()
    
    await researcher_reasoning.initialize()
    await analyst_reasoning.initialize()
    await coordinator_reasoning.initialize()

    try:
        # Create specialized research agents
        researcher = ConsoleAgent(
            name="researcher",
            llm_config={"api_key": api_key},
            reasoning=researcher_reasoning,
            system_prompt="""You are a research specialist. 
            Analyze information systematically and draw well-supported conclusions."""
        )

        analyst = WebSocketAgent(
            name="analyst",
            llm_config={"api_key": api_key},
            reasoning=analyst_reasoning,
            websocket_url=websocket_url,
            system_prompt="""You are a data analyst.
            Process and analyze data to extract meaningful insights."""
        )

        # Create coordinator agent
        coordinator = ConsoleAgent(
            name="research_coordinator",
            llm_config={"api_key": api_key},
            reasoning=coordinator_reasoning,
            system_prompt="""You are a research coordinator.
            Coordinate between researchers and analysts to complete research tasks.
            Break down complex problems and delegate effectively."""
        )

        # Initialize all agents
        async with researcher, analyst, coordinator:
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

    finally:
        # Clean up reasoning patterns
        await researcher_reasoning.cleanup()
        await analyst_reasoning.cleanup()
        await coordinator_reasoning.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 