"""Example of interactive agent solving math problems."""

import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dxa.agent.interactive_agent import InteractiveAgent
from dxa.core.reasoning import ChainOfThoughtReasoning
from dxa.core.reasoning.base_reasoning import ReasoningConfig

def create_math_tutor(api_key: str = None) -> InteractiveAgent:
    """Create a math tutor agent with sensible defaults."""
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    reasoning_config = ReasoningConfig(
        strategy="cot",
        llm_config={
            "model": "gpt-4",
            "api_key": api_key,
            "temperature": 0.7,
            "max_tokens": 1000
        }
    )
    agent_config = {
        "name": "math_tutor",
        "model": "gpt-4",
        "temperature": 0.7,
        "api_key": api_key,
        "system_prompt": """You are a skilled mathematics tutor. Your approach is to:
        1. Help students understand problems by breaking them down
        2. Guide them through step-by-step solutions
        3. Explain mathematical concepts clearly using examples
        4. Verify solutions and check for errors
        5. Encourage students to think through problems""",
        "reasoning": reasoning_config,
    }

    return InteractiveAgent(
        config=agent_config,
        reasoning=ChainOfThoughtReasoning(config=reasoning_config)
    )

async def main():
    """Run interactive math solver example."""
    agent = create_math_tutor()
    
    print("Math Tutor Assistant")
    print("-------------------")
    print("I can help you solve math problems step by step.")
    print("Type your math question or problem to begin.\n")

    result = await agent.run()
    
    if not result['success']:
        print("Error:", result.get('error'))
    response = result["results"]
    print(response["response"])

if __name__ == "__main__":
    asyncio.run(main()) 