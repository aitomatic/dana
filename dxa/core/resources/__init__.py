"""DXA resource management."""

from dxa.core.resources.base_resource import BaseResource
from dxa.core.resources.expert import ExpertResource
from dxa.core.resources.agents import AgentResource
from dxa.core.resources.llm_resource import LLMResource
from dxa.core.resources.human import HumanResource

__all__ = [
    'BaseResource',
    'ExpertResource',
    'AgentResource',
    'LLMResource',
    'HumanResource'
]

# Note: HumanResource is temporarily removed until human.py is properly implemented 