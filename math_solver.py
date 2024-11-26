"""Example of interactive agent solving math problems."""

import asyncio
import os
from dxa.agents.interactive import ConsoleAgent
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.experts.math import create_math_expert
from dxa.utils.logging import configure_logging

async def main() -> None:
    """Run interactive math solver example."""
    # Set up logging
    configure_logging(
        log_dir="logs",
        log_level="INFO",
        json_format=True,
        console_output=True
    )

    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    try:
        # Create math expert
        math_expert = create_math_expert(api_key)
        await math_expert.initialize()

        # Initialize reasoning pattern
        reasoning = ChainOfThoughtReasoning()
        await reasoning.initialize()

        # Create interactive agent with math expert
        agent = InteractiveAgent(
            name="math_solver",
            reasoning=reasoning,
            internal_llm_config={
                "api_key": api_key,
                "model": "gpt-4",
                "description": "Internal reasoning LLM"
            },
            expert_resources=[math_expert],
            system_prompt="""You are a helpful math tutor that can solve problems by:
            1. Understanding the problem
            2. Breaking it down into steps
            3. Using the math expert when needed
            4. Explaining the solution clearly
            
            Before solving, check if you need expert help by considering:
            1. Problem complexity
            2. Required mathematical concepts
            3. Need for formal proofs or verification""",
            description="Interactive math solving agent"
        )

        async with agent:
            result = await agent.run({
                "domain": "mathematics",
                "style": "tutorial"
            })
            print(f"Session completed: {result['success']}")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise

    finally:
        # Clean up resources
        if 'reasoning' in locals():
            await reasoning.cleanup()
        if 'math_expert' in locals():
            await math_expert.cleanup()

if __name__ == "__main__":
    asyncio.run(main())