"""Example of interactive agent solving math problems."""

import asyncio
import os
from dxa.agents.interactive import InteractiveAgent
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.core.io.console import ConsoleIO

async def main():
    """Run interactive math solver example."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Initialize reasoning pattern
    reasoning = ChainOfThoughtReasoning()
    await reasoning.initialize()  # Initialize before use

    # Create interactive agent
    agent = InteractiveAgent(
        name="math_solver",
        llm_config={"api_key": api_key},
        reasoning=reasoning,  # Pass initialized reasoning
        io=ConsoleIO(),
        system_prompt="""You are a helpful math tutor. Break down problems 
        step by step and explain your reasoning clearly."""
    )

    try:
        async with agent:  # Uses context manager for cleanup
            result = await agent.run({
                "domain": "mathematics",
                "style": "tutorial"
            })
            print(f"Session completed: {result['success']}")
    finally:
        await reasoning.cleanup()  # Clean up reasoning resources

if __name__ == "__main__":
    asyncio.run(main()) 