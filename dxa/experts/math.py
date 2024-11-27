"""Mathematics domain expert.

This module provides functionality to create a specialized mathematics expert
resource capable of solving various mathematical problems including algebra,
calculus, geometry, and statistics.

The math expert can:
- Solve algebraic equations and systems
- Perform calculus operations (derivatives, integrals)
- Analyze geometric problems and proofs
- Handle statistical analysis and probability calculations
- Process numerical computations with step-by-step explanations

Example:
    >>> from dxa.experts import create_math_expert
    >>> expert = create_math_expert(api_key="your-api-key")
    >>> result = expert.analyze("Solve the equation: x² + 5x + 6 = 0")
    >>> print(result)
    Step 1: Identify this as a quadratic equation...

Notes:
    - The expert requires a valid API key for the underlying LLM service
    - Confidence threshold is set to 0.7 by default
    - Uses GPT-4 as the default model for complex mathematical reasoning
"""

from dxa.core.resource.expert import DomainExpertise, ExpertResource

def create_math_expert(api_key: str) -> ExpertResource:
    """Create a mathematics expert resource."""
    expertise = DomainExpertise(
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
    
    # Create and return the expert resource
    return ExpertResource(
        name="math_expert",
        expertise=expertise,
        config={
            "api_key": api_key,
            "model": "gpt-4"
        },
        system_prompt="""You are an expert mathematician. When analyzing problems:
        1. Break down complex calculations step by step
        2. Show your work clearly
        3. Verify your answers
        4. Explain mathematical concepts when relevant
        5. Point out any assumptions made""",
        confidence_threshold=0.7
    ) 