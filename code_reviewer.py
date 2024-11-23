"""Example implementation of MUA for code review."""

import asyncio
import os
from mua2 import ConsoleModelUsingAgent, DomainExpertLLM, User, configure_logging

async def main():
    """Initialize and start a code review agent session."""
    configure_logging(
        level="DEBUG",
        log_file="code_review.log",
        json_logs=True,
        include_performance=True
    )

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Create code review expert
    code_expert = DomainExpertLLM.create(
        domain="software engineering",
        llm_config={"api_key": api_key},
        system_prompt="""You are an expert software engineer. When reviewing code:
        1. Analyze code quality and potential issues
        2. Suggest specific improvements
        3. Consider performance implications
        4. Check for security vulnerabilities
        5. Evaluate maintainability and readability
        Always provide concrete examples in your suggestions.
        Format your suggestions using markdown code blocks."""
    )

    # Define users
    code_owner = User(
        role="code_owner",
        name="Developer",
        description="The developer who wrote the code and needs review",
        permissions=["specify_code", "clarify", "provide_context", "modify"]
    )

    reviewer = User(
        role="reviewer",
        name="Senior Developer",
        description="Senior developer who validates the code changes",
        permissions=["review", "approve", "request_changes", "provide_feedback"]
    )

    # Initialize agent with code review expert and users
    agent_prompt = """You are a problem-solving agent facilitating code reviews.
    You work with:
    1. The code owner who needs their code reviewed
    2. A senior reviewer who provides final approval
    3. A software engineering expert for technical analysis

    When you need technical analysis, use the format:
    {
        "reasoning": "why you need engineering expertise",
        "consultations": [
            {
                "expert": "software engineering",
                "question": "your specific question",
                "context": "relevant code or technical context"
            }
        ]
    }

    When you need user input, use the format:
    {
        "user_interaction": {
            "role": "code_owner or reviewer",
            "purpose": "why you need their input",
            "question": "what you need to ask",
            "context": "relevant code or review context"
        }
    }"""

    agent = ConsoleModelUsingAgent(
        agent_llm_config={"api_key": api_key},
        domain_experts=[code_expert],
        users=[code_owner, reviewer],
        agent_system_prompt=agent_prompt
    )
    
    await agent.start_session()

if __name__ == "__main__":
    asyncio.run(main()) 