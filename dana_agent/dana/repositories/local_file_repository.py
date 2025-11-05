from pathlib import Path
from dana.config.storage_config import FileStorageConfig
from dana.core.agent.base_agent import BaseAgent
from dana.common.base_war import BaseWAR
from dana.common.schemas import PromptVersionSnapshot
from dana.common.protocols.war import ResourceProtocol, AgentProtocol, WorkflowProtocol

class LocalFileRepository:
    def __init__(self, storage_config: FileStorageConfig):
        self.storage_config = storage_config
        self._workspace_folder = Path(self.storage_config.workspace_folder)


    def _get_relative_prompt_path(self, agent: BaseAgent, component: BaseWAR | None = None) -> Path:
        _codec = getattr(agent, "_codec", None)
        if _codec is None or "magic" in str(_codec.__qualname__):
            _codec_str = "default"
        else:
            _codec_str = _codec.__qualname__
        if component is None:
            # NOTE : For agent, we only store system prompt template
            target_path = Path(self._workspace_folder / _codec_str / agent.__class__.__qualname__) / "prompts" / "system_prompt_template"
        else:
            # NOTE : For resource and workflow, we store prompts in the respective subfolders
            if isinstance(component, AgentProtocol):
                subfolder = "agents"
            elif isinstance(component, ResourceProtocol):
                subfolder = "resources"
            elif isinstance(component, WorkflowProtocol):
                subfolder = "workflows"
            else:
                raise ValueError(f"Invalid component type: {type(component)}. Only accepts instance of subclasses of {ResourceProtocol.__name__}, {AgentProtocol.__name__}, {WorkflowProtocol.__name__}")
            target_path = Path(self._workspace_folder / _codec_str / agent.__class__.__qualname__) / "prompts" / subfolder / component.__class__.__qualname__
        target_path.mkdir(parents=True, exist_ok=True)
        return target_path


    def has_any_prompt_versions(self, agent: BaseAgent, component: BaseWAR | None = None) -> bool:
        return len(self.list_prompt_versions(agent, component)) > 0

    def get_active_prompt(self, agent: BaseAgent, component: BaseWAR | None = None) -> PromptVersionSnapshot:
        pass

    def list_prompt_versions(self, agent: BaseAgent, component: BaseWAR | None = None) -> list[str]:
        def _filter(item: str) -> bool:
            return item.startswith("v") and item[1:].isdigit()
        relative_prompt_path = self._get_relative_prompt_path(agent, component)
        versions_folder = self._workspace_folder / relative_prompt_path / "versions"
        if not versions_folder.exists():
            return []
        items = [_path.stem for _path in versions_folder.iterdir()]
        return sorted([item for item in items if _filter(item)], key=lambda x: int(x.split("v")[1]))