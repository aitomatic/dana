from abc import abstractmethod

from dana.common.llm import LLMMessage
from dana.common.protocols import Persistable
from dana.common.llm.types import LLMMessage
from dana.common.protocols import PrivatePromptsProtocol, PublicPromptsProtocol
from dana.common.storage import AbstractStorage, StorageFactory
from dana.core.agent.star_agent import BaseSTARAgent
from dana.core.agent.timeline import Timeline
from hashlib import sha256
import inspect
from .agent_prompt_engineer import AgentPromptEngineer
from .base_prompt_engineer import BasePromptEngineer
from .codecs import AbstractCodec, CSXMLCodec
from .resource_prompt_engineer import ResourcePromptEngineer
from .workflow_prompt_engineer import WorkflowPromptEngineer
from pathlib import Path
import re
from structlog import get_logger

logger = get_logger()


class PromptEngineerManagerProtocol(PublicPromptsProtocol, PrivatePromptsProtocol, Persistable):
    @property
    def prefix(self) -> str:
        filepath = inspect.getfile(self._agent.__class__)
        filename = Path(filepath).stem
        return f"{self._agent.__class__.__qualname__}__{filename}/prompts"
        
    @property
    def key(self) -> str:
        return f"{self.prefix}/system_prompt.template"

    @property
    @abstractmethod
    def public_description(self) -> str: ...

    @property
    @abstractmethod
    def identity(self) -> str: ...

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @property
    @abstractmethod
    def available_tools_prompt(self) -> str: ...

    @abstractmethod
    def build_llm_request(self, timeline: Timeline) -> list[LLMMessage]: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def persist(self) -> None: ...

    @abstractmethod
    def load(self) -> str | None: ...


TEMPLATE_SYSTEM_PROMPT = """
{{identity}}

<tool_calling>
You have tools at your disposal to solve the coding task. Follow these rules regarding tool calls:
1. ALWAYS follow the tool call schema <available_tools> exactly as specified and make sure to provide all necessary parameters.
2. The conversation may reference tools that are no longer available. NEVER call tools that are not explicitly provided.
3. **NEVER refer to tool names when speaking to the USER.** For example, instead of saying 'I need to use the edit_file tool to edit your file', just say 'I will edit your file'.
4. Only calls tools when they are necessary. If the USER's task is general or you already know the answer, just respond without calling tools.
5. Before calling each tool, first explain to the USER why you are calling it.
</tool_calling>

<available_tools>
{{tool_instruction_prompt}}

# Available tools:
{{available_tools_prompt}}
</available_tools>
"""


class PromptEngineerManager(PromptEngineerManagerProtocol, Persistable):
    def __init__(
        self,
        agent: BaseSTARAgent,
        agent_prompt_engineer_cls: type[BasePromptEngineer] = AgentPromptEngineer,
        resource_prompt_engineer_cls: type[BasePromptEngineer] = ResourcePromptEngineer,
        workflow_prompt_engineer_cls: type[BasePromptEngineer] = WorkflowPromptEngineer,
        storage: AbstractStorage | None = None,
        codec: type[AbstractCodec] | None = None,
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs,
    ):
        self._agent = agent
        self._agent_prompt_engineer_cls = agent_prompt_engineer_cls
        self._resource_prompt_engineer_cls = resource_prompt_engineer_cls
        self._workflow_prompt_engineer_cls = workflow_prompt_engineer_cls
        self._storage = storage or StorageFactory.get_storage()
        self._force_generate = force_generate
        self._check_conflicts = check_conflicts
        self._codec = codec or CSXMLCodec
        # NOTE : Registry management will be added later
        self._agent_prompt_engineers = {}
        self._resource_prompt_engineers = {}
        self._workflow_prompt_engineers = {}
        self._system_prompt = None
        self._template = None

    def _instantiate_prompt_engineer(
        self, prompt_engineer_cls: type[BasePromptEngineer], component, prefix: str, **kwargs
    ) -> BasePromptEngineer:
        return prompt_engineer_cls(
            component=component,
            storage=self._storage,
            codec=self._codec,
            force_generate=self._force_generate,
            check_conflicts=self._check_conflicts,
            **kwargs,
        ).with_prefix(prefix)


    @property
    def public_description(self) -> str:
        if self not in self._agent_prompt_engineers:
            self._agent_prompt_engineers[self] = self._instantiate_prompt_engineer(
                self._agent_prompt_engineer_cls, self._agent, prefix=self.prefix
            )
        return self._agent_prompt_engineers[self].load()

    @property
    def identity(self) -> str:
        return f"{self._agent.__class__.__doc__}"

    @property
    def tool_instruction_prompt(self) -> str:
        return self._codec.get_instruction()

    @property
    def available_tools_prompt(self) -> str:
        # Load tool prompts for all agents, resources, and workflows
        tools_prompt = ""
        for agent in self._agent._agents:
            if agent not in self._agent_prompt_engineers:
                self._agent_prompt_engineers[agent] = self._instantiate_prompt_engineer(
                    self._agent_prompt_engineer_cls, agent, prefix=f"{self.prefix}/agents"
                )
            tools_prompt += self._agent_prompt_engineers[agent].prompt + "\n"
        for resource in self._agent._resources:
            if resource not in self._resource_prompt_engineers:
                self._resource_prompt_engineers[resource] = self._instantiate_prompt_engineer(
                    self._resource_prompt_engineer_cls, resource, prefix=f"{self.prefix}/resources"
                )
            tools_prompt += self._resource_prompt_engineers[resource].prompt + "\n"
        for workflow in self._agent._workflows:
            if workflow not in self._workflow_prompt_engineers:
                self._workflow_prompt_engineers[workflow] = self._instantiate_prompt_engineer(
                    self._workflow_prompt_engineer_cls, workflow, prefix=f"{self.prefix}/workflows"
                )
            tools_prompt += self._workflow_prompt_engineers[workflow].prompt + "\n"
        return tools_prompt

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = self._get_system_prompt()
        return self._system_prompt

    def _get_system_prompt(self) -> str:
        _template = self.load()
        if _template is None or self._force_generate:
            _template = TEMPLATE_SYSTEM_PROMPT
            self._template = _template
            self.persist()
            logger.info(f"Prompt template persisted for {self._agent.__class__.__qualname__} with key {self.key}")
        variables = re.findall(r"\{\{(.*?)\}\}", _template)
        for variable in variables:
            if hasattr(self, variable):
                attr = getattr(self, variable)
                if callable(attr):
                    value = attr()
                else:
                    value = attr
                _template = _template.replace(f"{{{{{variable}}}}}", str(value))
        return _template

    def build_llm_request(self, timeline: Timeline) -> list[LLMMessage]:
        return []

    def reset(self) -> None:
        # NOTE : Placeholder for future implementation
        pass

    def persist(self) -> None:
        if self._template is None:
            raise ValueError(f"[{self.__class__.__qualname__}] Template for {self._agent.__class__.__qualname__} is not generated yet")
        self._storage.persist(self.key, self._template)

    def load(self) -> str | None:
        return self._storage.load(self.key)
