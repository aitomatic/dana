"""Example of interactive agent solving math problems."""

import asyncio
import os
from dxa.agents.console import ConsoleAgent
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.core.resources.llm import LLMResource
from dxa.core.expertise import DomainExpertise, ExpertResource
from dxa.utils.logging import configure_logging

# Define mathematics expertise
MATH_EXPERTISE = DomainExpertise(
    name="mathematics",
    description="Expert in mathematical problem-solving and concepts",
    capabilities=[
        "Solve algebraic equations",
        "Perform calculus operations",
        "Analyze geometric problems",
        "Work with statistics and probability",
        "Handle numerical computations"
    ],
    keywords=[
        "solve", "calculate", "equation", "formula", "proof",
        "algebra", "geometry", "calculus", "statistics"
    ],
    requirements=[
        "Clear problem statement",
        "Known variables and constraints",
        "Expected form of solution"
    ],
    example_queries=[
        "Solve this quadratic equation: x² + 5x + 6 = 0",
        "Find the derivative of f(x) = x³ + 2x² - 4x + 1",
        "Calculate the probability of rolling two sixes with fair dice"
    ]
)

async def main():
    """Run interactive math solver example."""
    configure_logging(
        log_dir="logs",
        log_level="INFO",
        json_format=True,
        console_output=True
    )

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Create math expert LLM resource and expert resource
    math_llm = LLMResource(
        name="math_expert",
        api_key=api_key,
        model="gpt-4",
        system_prompt="""You are an expert mathematician. When analyzing problems:
        1. Break down complex calculations step by step
        2. Show your work clearly
        3. Verify your answers
        4. Explain mathematical concepts when relevant
        5. Point out any assumptions made"""
    )

    # Create expert resource with domain expertise and its LLM
    math_expert_resource = ExpertResource(
        llm_resource=math_llm,
        expertise=MATH_EXPERTISE,
        confidence_threshold=0.7
    )

    # Initialize reasoning pattern
    reasoning = ChainOfThoughtReasoning()
    await reasoning.initialize()

    # Create interactive agent with math expert
    agent = ConsoleAgent(
        name="math_solver",
        reasoning=reasoning,
        expert_resources=[math_expert_resource],
        system_prompt="""You are a helpful math tutor that can solve problems by:
        1. Understanding the problem
        2. Breaking it down into steps
        3. Using the math expert when needed
        4. Explaining the solution clearly
        
        Before solving, check if you need expert help by considering:
        1. Problem complexity
        2. Required mathematical concepts
        3. Need for formal proofs or verification"""
    )

    try:
        async with agent:
            result = await agent.run({
                "domain": "mathematics",
                "style": "tutorial"
            })
            print(f"Session completed: {result['success']}")
    finally:
        await reasoning.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 