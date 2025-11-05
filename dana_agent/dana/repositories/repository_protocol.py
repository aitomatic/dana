from typing import Protocol

from dana.common.base_war import BaseWAR
from dana.common.schemas import PromptVersionSnapshot
from dana.core.agent.base_agent import BaseAgent


class RepositoryProtocol(Protocol):
    def has_any_prompt_versions(self, agent: BaseAgent, component: BaseWAR | None = None) -> bool:
        ...
    
    def get_active_prompt(self, agent: BaseAgent, component: BaseWAR | None = None) -> PromptVersionSnapshot:
        ...
    
    def list_prompt_versions(self, agent: BaseAgent, component: BaseWAR | None = None) -> list[str]:
        ...

    def load_prompt_snapshot(self, version: str,  agent: BaseAgent, component: BaseWAR | None = None) -> PromptVersionSnapshot:
        ...


    def set_active_prompt(self, agent: BaseAgent, component: BaseWAR | None = None) -> None:
        ...

    def create_snapshot(self, content: str, provenance: dict, metrics: dict, agent: BaseAgent, component: BaseWAR | None = None) -> PromptVersionSnapshot:
        ...