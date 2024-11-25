"""Core DXA functionality."""

from dxa.core.resources.expert import DomainExpertise, ExpertResource
from dxa.core.resources.base import BaseResource
from dxa.core.reasoning.base_reasoning import BaseReasoning

__all__ = [
    'DomainExpertise',
    'ExpertResource',
    'BaseResource',
    'BaseReasoning'
]
