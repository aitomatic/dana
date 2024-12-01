"""DXA resource management."""

from dxa.core.resource.base_resource import BaseResource
from dxa.core.resource.expert_resource import ExpertResource
from dxa.core.resource.agent_resource import AgentResource
from dxa.core.resource.llm_resource import LLMResource
from dxa.core.resource.human_resource import HumanResource

__all__ = [
    'BaseResource',
    'ExpertResource',
    'AgentResource',
    'LLMResource',
    'HumanResource'
]
