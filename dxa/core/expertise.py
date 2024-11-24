"""Domain expertise definitions for DXA."""

from dataclasses import dataclass
from typing import List
from dxa.core.resources.base import BaseResource

@dataclass
class DomainExpertise:
    """Definition of a domain of expertise."""
    name: str                    # e.g., "mathematics"
    description: str            # What this expert knows
    capabilities: List[str]     # What this expert can do
    keywords: List[str]         # Trigger words/phrases
    requirements: List[str]     # What input this expert needs
    example_queries: List[str]  # Example questions this expert can answer

@dataclass
class ExpertResource:
    """A resource with specific domain expertise."""
    resource_name: str          # Name of the resource
    expertise: DomainExpertise  # The domain expertise it provides
    resource: BaseResource  # Add the actual resource
    confidence_threshold: float  # When to use this expert (0-1)