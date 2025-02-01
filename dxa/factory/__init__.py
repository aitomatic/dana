"""Domain Expert Implementations for DXA Framework.

This package provides specialized domain experts that can be integrated with the DXA
framework. Each expert is designed to handle specific types of problems within
their domain of expertise, leveraging advanced language models for analysis and
problem-solving.

Available Experts:
    - Mathematics Expert: Handles mathematical problem-solving including algebra,
      calculus, geometry, and statistics.
    - Finance Expert: Performs financial analysis, valuations, and investment
      assessments with both quantitative and qualitative insights.

Example:
    >>> from dxa.experts import create_math_expert, create_finance_expert
    >>> math_expert = create_math_expert(api_key="your-api-key")
    >>> finance_expert = create_finance_expert(api_key="your-api-key")
    >>> math_result = math_expert.analyze("Solve: 2x + 5 = 13")
    >>> finance_result = finance_expert.analyze("Calculate ROI: Cost 1000, Revenue 1500")

Notes:
    - All experts require valid API keys for the underlying LLM services
    - Experts use GPT-4 by default for complex reasoning tasks
    - Each expert has specialized capabilities and knowledge in their domain
    - Experts can be combined or used independently based on use case
"""

from .dxa_factory import DXAFactory
from .math import create_math_expert
from .finance import create_finance_expert

__all__ = [
    'DXAFactory',
    'create_math_expert',
    'create_finance_expert'
]
