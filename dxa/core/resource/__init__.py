"""DXA resource management."""

from dxa.core.resource.base_resource import BaseResource
from dxa.core.resource.expert import ExpertResource
from dxa.core.resource.agents import AgentResource
from dxa.core.resource.llm_resource import LLMResource
from dxa.core.resource.human import HumanResource

__all__ = [
    'BaseResource',
    'ExpertResource',
    'AgentResource',
    'LLMResource',
    'HumanResource'
]

# Note: HumanResource is temporarily removed until human.py is properly implemented 