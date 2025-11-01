from abc import abstractmethod
from typing import Protocol

from dana.common.llm import LLMMessage
from dana.common.llm.types import LLMMessage
from dana.common.storage import AbstractStorage
from dana.core.agent.star_agent import BaseSTARAgent
from dana.core.agent.timeline import Timeline

from .agent_prompt_engineer import AgentPromptEngineer
from .base_prompt_engineer import BasePromptEngineer
from .resource_prompt_engineer import ResourcePromptEngineer
from .workflow_prompt_engineer import WorkflowPromptEngineer


class PromptEngineerManagerProtocol(Protocol):
    @property
    @abstractmethod
    def public_description(self) -> str:
        pass

    @property
    @abstractmethod
    def identity(self) -> str:
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @abstractmethod
    def build_llm_request(self, timeline: Timeline) -> list[LLMMessage]:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

class PromptEngineerManager:
    def __init__(self, agent : BaseSTARAgent,
        agent_prompt_engineer_cls: type[BasePromptEngineer] = AgentPromptEngineer,
        resource_prompt_engineer_cls: type[BasePromptEngineer] = ResourcePromptEngineer,
        workflow_prompt_engineer_cls: type[BasePromptEngineer] = WorkflowPromptEngineer,
        storage: AbstractStorage | None = None,
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs
    ):
        self.agent = agent


    @property
    def public_description(self) -> str:
        return ""

    @property
    def identity(self) -> str:
        return ""

    @property
    def system_prompt(self) -> str:
        return ""

    def build_llm_request(self, timeline: Timeline) -> list[LLMMessage]:
        return []    

    def reset(self) -> None:
        # NOTE : Placeholder for future implementation
        pass