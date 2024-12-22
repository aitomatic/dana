"""
Flows are responsible for:
1. Suggesting next steps for a plan
2. Validating plans
3. Updating world state
"""

from .base_flow import BaseFlow
from .research_flow import ResearchFlow

__all__ = ["BaseFlow", "ResearchFlow"]