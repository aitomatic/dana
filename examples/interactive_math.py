"""Example of interactive agent solving math problems."""

import asyncio
import os
from dxa.core.factory import create_agent

async def main():
    """Run interactive math solver example."""
    # Check environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    # Basic configuration
    config = {
        "api_key": api_key,
        "name": "math_solver",
        "resources": ["math_expert"],
        "model": "gpt-4",
        "system_prompt": """You are a helpful math tutor.
        Break down problems step by step and explain your reasoning clearly."""
    }
    
    async with create_agent("interactive", config) as agent:
        result = await agent.run({
            "domain": "mathematics",
            "parameters": {
                "style": "tutorial",
                "show_work": True
            }
        })
        print(f"Session completed: {result['success']}")

if __name__ == "__main__":
    asyncio.run(main()) 