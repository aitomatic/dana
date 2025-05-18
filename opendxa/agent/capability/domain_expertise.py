"""Domain expertise definitions for DXA.

This module defines the foundational structures for representing domain expertise,
enabling agents to:
- Define specialized knowledge domains
- Specify expert capabilities and requirements
- Match queries to appropriate expert resources
- Validate expertise requirements

The DomainExpertise class serves as a blueprint for creating specialized expert
resources with well-defined capabilities and requirements.

Classes:
    DomainExpertise: Defines a knowledge domain and its capabilities

Example:
    >>> finance_expert = DomainExpertise(
    ...     name="finance",
    ...     description="Expert in financial analysis and planning",
    ...     capabilities=["stock analysis", "risk assessment"],
    ...     keywords=["investment", "portfolio", "risk"],
    ...     requirements=["financial data", "time period"],
    ...     example_queries=["Analyze risk for AAPL stock"]
    ... )
"""

from typing import List

from pydantic import BaseModel, Field


class DomainExpertise(BaseModel):
    """Definition of a domain of expertise.

    This class encapsulates all the information needed to define an expert's
    domain of knowledge, capabilities, and requirements. It serves as a
    blueprint for creating specialized expert resources.

    Attributes:
        name (str): Domain identifier (e.g., "mathematics")
        description (str): Detailed description of the expert's knowledge domain
        capabilities (List[str]): Specific abilities and skills this expert has
        keywords (List[str]): Trigger words/phrases that indicate this expertise is needed
        requirements (List[str]): Required information or context for queries in this domain
        example_queries (List[str]): Sample questions demonstrating proper usage

    Example:
        >>> math_expert = DomainExpertise(
        ...     name="mathematics",
        ...     description="Expert in algebra and calculus",
        ...     capabilities=["equation solving", "differentiation"],
        ...     keywords=["solve", "calculate", "equation"],
        ...     requirements=["mathematical expression"],
        ...     example_queries=["solve x^2 + 2x + 1 = 0"]
        ... )
    """

    name: str = Field(..., description="Domain identifier (e.g., 'mathematics')")
    description: str = Field(..., description="Detailed description of the expert's knowledge domain")
    capabilities: List[str] = Field(default_factory=list, description="Specific abilities and skills this expert has")
    keywords: List[str] = Field(default_factory=list, description="Trigger words/phrases that indicate this expertise is needed")
    requirements: List[str] = Field(default_factory=list, description="Required information or context for queries in this domain")
    example_queries: List[str] = Field(default_factory=list, description="Sample questions demonstrating proper usage")
