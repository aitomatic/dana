"""DXA core module."""

from dxa.core.resource.base_resource import BaseResource
from dxa.core.resource.expert_resource import DomainExpertise
from dxa.core.resource.llm_resource import LLMResource
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.config import LLMConfig

__version__ = "0.1.0"

__all__ = [
    "BaseResource",
    "DomainExpertise",
    "LLMResource",
    "BaseReasoning",
    "LLMConfig",
]
