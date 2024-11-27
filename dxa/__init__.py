"""Domain-Expert Agent (DXA) framework.

DXA is a framework for building domain-expert agents that combine:
- Domain-specific expertise
- LLM-powered reasoning
- Interactive capabilities

Key Components:
- StateManager: Manages agent state and conversation history
- DomainExpertise: Defines areas of expertise and capabilities
- ExpertResource: Implements domain-expert behavior
- ChainOfThoughtReasoning: Provides step-by-step reasoning patterns

Example:
    >>> from dxa import DomainExpertise, ExpertResource
    >>> expertise = DomainExpertise(
    ...     name="mathematics",
    ...     description="Expert in algebra and calculus",
    ...     capabilities=["equation solving", "differentiation"],
    ...     keywords=["solve", "calculate", "equation"],
    ...     requirements=["mathematical expression"],
    ...     example_queries=["solve x^2 + 2x + 1 = 0"]
    ... )
"""

from dxa.agents.state import StateManager
from dxa.core.capabilities.expertise import DomainExpertise
from dxa.core.resources.expert import ExpertResource
from dxa.core.reasoning.cot import ChainOfThoughtReasoning

__all__ = [
    'StateManager',
    'DomainExpertise',
    'ExpertResource',
    'ChainOfThoughtReasoning'
]
