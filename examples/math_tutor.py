"""Example of interactive agent solving math problems."""

import asyncio
import os
from dxa.agent.interactive_agent import InteractiveAgent
from dxa.core.reasoning import ChainOfThoughtReasoning

def create_math_tutor(api_key: str = None) -> InteractiveAgent:
    """Create a math tutor agent with sensible defaults."""
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    config = {
        "model": "gpt-4",
        "temperature": 0.7,
        "api_key": api_key,
        "system_prompt": """You are a skilled mathematics tutor. Your approach is to:
        1. Help students understand problems by breaking them down
        2. Guide them through step-by-step solutions
        3. Explain mathematical concepts clearly using examples
        4. Verify solutions and check for errors
        5. Encourage students to think through problems""",
        "description": "Interactive math tutor agent"
    }

    return InteractiveAgent(
        name="math_tutor",
        config=config,
        reasoning=ChainOfThoughtReasoning()  # No config needed, CoT is the default strategy
    )

async def main():
    """Run interactive math solver example."""
    agent = create_math_tutor()
    
    print("Math Tutor Assistant")
    print("-------------------")
    print("I can help you solve math problems step by step.")
    print("Type your math question or problem to begin.\n")

    result = await agent.run({
        "objective": "Help solve math problems",
        "user_input": "Ready to help with math problems"
    })
    
    if not result['success']:
        print("Error:", result.get('error'))

if __name__ == "__main__":
    asyncio.run(main()) 