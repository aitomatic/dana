"""Example of interactive agent solving math problems."""

import asyncio
import os
from dxa.agents.interactive import ConsoleAgent
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.experts.math import create_math_expert
from dxa.utils.logging import configure_logging

# MathSolverAgent Prompt Configuration
#
# This file defines the base prompts for the MathSolverAgent.
# The agent is aware of available resources but does not specify interaction formats
# (those are handled by the reasoning strategies).
#
# Key characteristics:
# - Defines the agent's core mathematical problem-solving personality
# - Lists available resources the agent can access
# - Maintains precision and methodical approach
# - Resource descriptions are clear but interaction details are left to reasoning
math_solver_agent_prompts = {
    "system_prompt": """You are a precise and methodical mathematics problem solver with access to the following resources:

AVAILABLE_RESOURCES:
  agents:
    math_expert: Advanced mathematics domain expert
    calculus_expert: Calculus and analysis specialist
    statistics_expert: Statistical analysis expert
    geometry_expert: Geometry and visualization specialist
  
  llm:
    external_llm: More powerful but slower LLM for complex computations
  
  users:
    student: The person who posed the problem
    teacher: Educational supervisor who can clarify requirements
    
  knowledge:
    mathematical_database: Database of mathematical formulas and theorems
    wolfram_alpha: Computational and plotting engine
    research_papers: Mathematical research database
    mathematical_visualizer: Tool for creating mathematical visualizations

Key principles:
- Always state given information and what needs to be found
- Define variables clearly when used
- Show each mathematical step explicitly
- Verify answers with units and sanity checks
- Include mathematical notation in LaTeX when beneficial
- Express numerical results with appropriate precision
- Note any assumptions made or special cases to consider""",

    "user_prompt": """Consider this mathematics problem:"""
}

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

        # Create reasoning pattern
        reasoning = ChainOfThoughtReasoning()

        # Create interactive agent with math expert
        agent = ConsoleAgent(
            name="math_solver",
            agent_prompts=math_solver_agent_prompts,
            reasoning=reasoning,
            resources={"math_expert": math_expert},
            llm_config={
                "api_key": api_key,
                "model": "gpt-4"
            },
            description="Interactive math solving agent"
        )

        try:
            async with agent:
                result = await agent.run({
                    "domain": "mathematics",
                    "parameters": {
                        "style": "tutorial",
                        "show_work": True
                    }
                })
                print(f"Session completed: {result['success']}")
        finally:
            await reasoning.cleanup()

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