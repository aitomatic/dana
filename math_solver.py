"""Example implementation of MUA for solving math problems."""

import asyncio
import os
from mua2 import ConsoleModelUsingAgent, DomainExpertLLM, User, configure_logging

async def main():
    """Initialize and start a math-focused console agent session."""
    configure_logging(
        level="DEBUG",
        log_file="math_solver.log",
        json_logs=True,
        include_performance=True
    )
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Create math expert
    math_expert = DomainExpertLLM.create(
        domain="mathematics",
        llm_config={"api_key": api_key},
        system_prompt="""You are an expert mathematician. When analyzing problems:
        1. Break down complex calculations step by step
        2. Show your work clearly
        3. Verify your answers
        4. Explain mathematical concepts when relevant
        5. Point out any assumptions made

        Structure your response as:
        CONFIDENCE: <percentage>%
        ANALYSIS:
        <your detailed analysis>
        ASSUMPTIONS:
        - list any assumptions
        LIMITATIONS:
        - list any limitations
        RECOMMENDATIONS:
        - list your recommendations"""
    )

    # Define single user
    user = User(
        role="problem_owner",
        name="User",
        description="The person who needs help solving a mathematical problem",
        permissions=[
            "specify_problem",    # Can specify the initial problem
            "clarify",           # Can provide clarification when asked
            "validate",          # Can validate proposed solutions
            "modify"             # Can modify the problem statement if needed
        ]
    )

    # Initialize agent with math expert and user
    agent = ConsoleModelUsingAgent(
        agent_llm_config={"api_key": api_key},
        domain_experts=[math_expert],
        users=[user],
        agent_system_prompt="""You are a problem-solving agent working with a user to solve 
        mathematical problems. You have access to a mathematics expert for technical analysis.

        When you need expert help, write:
        CONSULT mathematics: <your question>
        CONTEXT: <relevant context>
        REASON: <why you need expert input>

        When you need user input, write:
        ASK USER problem_owner: <your question>
        CONTEXT: <relevant context>
        PURPOSE: <why you need their input>

        Remember to:
        1. Ask for clarification if the problem is unclear
        2. Explain your reasoning in user-friendly terms
        3. Verify your understanding before proceeding
        4. Show your work step by step"""
    )
    
    await agent.start_session()

if __name__ == "__main__":
    asyncio.run(main()) 