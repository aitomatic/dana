from abc import abstractmethod
import inspect
from pathlib import Path
import re
from typing import TYPE_CHECKING

from structlog import get_logger

from dana.common.llm.types import LLMMessage
from dana.common.observable import observable
from dana.common.protocols import Persistable, PrivatePromptsProtocol, PublicPromptsProtocol
from dana.core.agent.timeline import Timeline
from dana.core.context import ContextBuilder
from dana.core.knowledge.prompts.codecs import AbstractCodec
from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryFactory, RepositoryType

from .prompt_engineer import AgentPromptEngineer, BasePromptEngineer, ResourcePromptEngineer, WorkflowPromptEngineer


logger = get_logger()

if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent


class PromptAPIProtocol(PublicPromptsProtocol, PrivatePromptsProtocol, Persistable):
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

    @abstractmethod
    def render(self, template: str) -> str: ...


TEMPLATE_SYSTEM_PROMPT = """
{{identity}}

<tool_calling>
You have tools at your disposal to solve the task. Follow these rules regarding tool calls:
1. ALWAYS follow the tool call schema <available_tools> exactly as specified and make sure to provide all necessary parameters.
2. The conversation may reference tools that are no longer available. NEVER call tools that are not explicitly provided.
3. **NEVER refer to tool names when speaking to the USER.** For example, instead of saying 'I need to use the edit_file tool to edit your file', just say 'I will edit your file'.
4. Only call tools when they are necessary. If the USER's task is general or you already know the answer, just respond without calling tools.
</tool_calling>

<output_format>
## STRICT OUTPUT FORMAT

Every response MUST follow this exact XML structure:

```xml
<done>false</done>
<function_call>
<invoke name="tool-name:method">
<parameter name="param">value</parameter>
</invoke>
</function_call>
<response></response>
```
OR
```xml
<done>true</done>
<function_call></function_call>
<response>Final answer with actual data</response>
```

## CRITICAL RULES

1. **<done> is ALWAYS required** - must be literal `true` or `false`
2. **done=false** → non-empty `<function_call>` and empty `<response>`
3. **done=true** → non-empty `<response>` and empty `<function_call>`
4. **NEVER output plain text** without these tags

If you need more data, set `<done>false</done>` and call a tool.
If you have the actual answer, set `<done>true</done>` and respond.
</output_format>

<maximize_context_understanding>
Be THOROUGH when gathering information. Make sure you have the FULL picture before replying. Use additional tool calls or clarifying questions as needed.
TRACE every symbol back to its definitions and usages so you fully understand it.
Look past the first seemingly relevant result. EXPLORE alternative implementations, edge cases, and varied search terms until you have COMPREHENSIVE coverage of the topic.
Bias towards not asking the user for help if you can find the answer yourself.
</maximize_context_understanding>

<available_tools>
{{tool_instruction_prompt}}

# Available tools:
{{available_tools_prompt}}
</available_tools>
"""


class LocalPromptAPI(PromptAPIProtocol):
    """
    Codec-aware prompt API implementation.
    
    This is the RECOMMENDED prompt management implementation. It provides codec-aware
    prompt generation and tool signature formatting, working in conjunction with
    CodecToolCaller for reliable tool execution.
    
    Key advantages over the legacy PromptEngineer:
    - Codec-aware prompt management
    - Structured tool signature formatting using codecs
    - Better integration with the codec system
    - More reliable tool call parsing
    
    Usage:
        Automatically used when you pass a codec to STARAgent initialization:
        
        .. code-block:: python
        
            from dana.core.knowledge.prompts.codecs import CSXMLCodec
            
            class MyAgent(STARAgent):
                def __init__(self, **kwargs):
                    super().__init__(
                        agent_type="my-agent",
                        codec=CSXMLCodec,  # Enables LocalPromptAPI
                        **kwargs
                    )
    
    See also:
        - PromptEngineer: Legacy implementation (available for backward compatibility)
        - dana.core.knowledge.prompts.codecs: Available codec implementations
    """
    
    # If static prompt variables are provided, they will be replaced in the template, then save.
    # These variables will not be constructed dynamically next time.
    static_prompt_variables = ["identity"]

    def __init__(
        self,
        agent: "BaseAgent",
        codec: type[AbstractCodec],
        agent_prompt_engineer_cls: type[AgentPromptEngineer] = AgentPromptEngineer,
        resource_prompt_engineer_cls: type[ResourcePromptEngineer] = ResourcePromptEngineer,
        workflow_prompt_engineer_cls: type[WorkflowPromptEngineer] = WorkflowPromptEngineer,
        template_system_prompt: str = TEMPLATE_SYSTEM_PROMPT,
        force_generate: bool = False,
        check_conflicts: bool = False,
        repository_factory: RepositoryFactory | None = None,
        **kwargs,
    ):
        self._agent = agent
        self._agent_prompt_engineer_cls = agent_prompt_engineer_cls
        self._resource_prompt_engineer_cls = resource_prompt_engineer_cls
        self._workflow_prompt_engineer_cls = workflow_prompt_engineer_cls
        self._codec = codec
        self._force_generate = force_generate
        self._check_conflicts = check_conflicts
        self._template_system_prompt = template_system_prompt
        # Use provided factory or default
        self._repository_factory = repository_factory or DEFAULT_REPOSITORY_FACTORY
        # NOTE: This agent repository (changed from store) - created via factory
        self._store = self._repository_factory.create(
            RepositoryType.PROMPT,
            agent=self._agent,
            component=None,  # For system prompt template
        )
        # NOTE : Registry management will be added later
        self._agent_prompt_engineers = {}
        self._resource_prompt_engineers = {}
        self._workflow_prompt_engineers = {}
        self._system_prompt = None
        self._template = None

    def _instantiate_prompt_engineer(
        self, prompt_engineer_cls: type[BasePromptEngineer], component, relative_path: str, **kwargs
    ) -> BasePromptEngineer:
        # Create repository via factory
        repository = self._repository_factory.create(RepositoryType.PROMPT, agent=self._agent, component=component)
        return prompt_engineer_cls(
            component=component,
            repository=repository,
            codec=self._codec,
            force_generate=self._force_generate,
            check_conflicts=self._check_conflicts,
            **kwargs,
        )

    @property
    def relative_path(self) -> str:
        filepath = inspect.getfile(self._agent.__class__)
        filename = Path(filepath).stem
        return f"{self._codec.__qualname__}/{self._agent.__class__.__qualname__}__{filename}/prompts"

    @property
    def public_description(self) -> str:
        if self not in self._agent_prompt_engineers:
            self._agent_prompt_engineers[self] = self._instantiate_prompt_engineer(
                self._agent_prompt_engineer_cls, self._agent, relative_path=f"{self.relative_path}/public_description"
            )
        return self._agent_prompt_engineers[self].load()

    @property
    def identity(self) -> str:
        return f"{self._agent.__class__.__doc__}"

    @property
    def tool_instruction_prompt(self) -> str:
        return self._codec.get_instruction()

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            _template = self.load()
            if _template is None or self._force_generate:
                # FILL STATIC VARIABLES BEFORE PERSIST
                _template = self._template_system_prompt
                for variable in self.static_prompt_variables:
                    if f"{{{{{variable}}}}}" in _template:
                        attr = getattr(self, variable)
                        if callable(attr):
                            value = attr()
                        else:
                            value = attr
                        _template = _template.replace(f"{{{{{variable}}}}}", str(value))
                self._template = _template
                self.persist()
            self._system_prompt = self.render(_template)
        return self._system_prompt

    def render(self, template: str) -> str:
        variables = re.findall(r"\{\{(.*?)\}\}", template)
        for variable in variables:
            if hasattr(self, variable):
                attr = getattr(self, variable)
                if callable(attr):
                    value = attr()
                else:
                    value = attr
                template = template.replace(f"{{{{{variable}}}}}", str(value))
        return template

    @property
    def available_tools_prompt(self) -> str:
        # Load tool prompts for all agents, resources, and workflows
        tools_prompt = ""
        for agent in self._agent._agents:
            if agent not in self._agent_prompt_engineers:
                self._agent_prompt_engineers[agent] = self._instantiate_prompt_engineer(
                    self._agent_prompt_engineer_cls, agent, relative_path=f"{self.relative_path}/agents/{agent.__class__.__qualname__}"
                )
            tools_prompt += self._agent_prompt_engineers[agent].prompt + "\n"
        for resource in self._agent._resources:
            if resource not in self._resource_prompt_engineers:
                self._resource_prompt_engineers[resource] = self._instantiate_prompt_engineer(
                    self._resource_prompt_engineer_cls,
                    resource,
                    relative_path=f"{self.relative_path}/resources/{resource.__class__.__qualname__}",
                )
            tools_prompt += self._resource_prompt_engineers[resource].prompt + "\n"
        for workflow in self._agent._workflows:
            if workflow not in self._workflow_prompt_engineers:
                self._workflow_prompt_engineers[workflow] = self._instantiate_prompt_engineer(
                    self._workflow_prompt_engineer_cls,
                    workflow,
                    relative_path=f"{self.relative_path}/workflows/{workflow.__class__.__qualname__}",
                )
            tools_prompt += self._workflow_prompt_engineers[workflow].prompt + "\n"
        return tools_prompt

    @observable
    def build_llm_request(self, timeline: Timeline) -> list[LLMMessage]:
        """
        Build LLM messages for the agent using the Timeline's LLM conversion API.

        Args:
            timeline: Timeline object containing conversation history

        Returns:
            List of LLMMessage objects ready for LLM request
        """
        messages = []

        # System prompt - use the system prompt from PromptEngineerManager
        system_prompt = self.system_prompt
        messages.append(LLMMessage(role="system", content=system_prompt))

        # Use Timeline's LLM conversion with latest user message separation
        if timeline:
            # Get timeline messages with latest user separation
            timeline_messages = timeline.to_llm_messages(separate_latest_user=True)

            # Check if we have a latest user message (last message should be user role)
            if timeline_messages and timeline_messages[-1].role == "user":
                # Separate context from latest user message
                context_messages = timeline_messages[:-1]
                latest_user_message = timeline_messages[-1]

                task = latest_user_message.content
                class _TaggedQueryable:
                    def __init__(self, source, tag: str):
                        self._source = source
                        self._tag = tag

                    def query(self, question: str) -> str:
                        result = self._source.query(question)
                        return f"<{self._tag}>\n{result}\n</{self._tag}>"

                ctx = ContextBuilder(token_budget=getattr(timeline, "max_context_tokens", 100000))
                ltmemory = getattr(self._agent, "_ltmemory", None)
                if ltmemory is not None:
                    ctx.add_source("ltmemory", _TaggedQueryable(ltmemory, "LTMEMORY"))

                for resource in getattr(self._agent, "_resources", []):
                    if hasattr(resource, "query") and hasattr(resource, "resource_id"):
                        ctx.add_source(resource.resource_id, _TaggedQueryable(resource, resource.resource_id.upper()))

                context = ctx.build(task=task)

                # Wrap context in structured format if we have context
                if context_messages or context.text:
                    timeline_lines = ["<CONTEXT>"]
                    if context_messages:
                        timeline_lines.append("<TIMELINE>")
                        for msg in context_messages:
                            timeline_lines.append(f"<ENTRY>{msg.content}</ENTRY>")
                        timeline_lines.append("</TIMELINE>")
                    if context.text:
                        timeline_lines.append(context.text)
                    timeline_lines.append("</CONTEXT>")
                    timeline_content = "\n".join(timeline_lines)
                    messages.append(LLMMessage(role="assistant", content=timeline_content))

                # Add latest user message as separate user message
                messages.append(latest_user_message)
            else:
                # No latest user message, use all timeline messages
                messages.extend(timeline_messages)

        # Debug logging - log message building
        from dana.common.llm.debug_logger import get_debug_logger

        debug_logger = get_debug_logger()
        system_prompt_length = len(system_prompt)
        debug_logger.log_agent_interaction(
            agent_id=self._agent.object_id,
            agent_type=self._agent.agent_type,
            interaction_type="build_llm_request",
            content=f"Built {len(messages)} messages for LLM request",
            metadata={
                "message_count": len(messages),
                "system_prompt_length": system_prompt_length,
                "timeline_entries": len(timeline.timeline) if timeline else 0,
            },
        )

        return messages

    def reset(self) -> None:
        pass

    def build_tool_schemas(self) -> list[dict]:
        """Build OpenAI-compatible tool schemas for native function calling.

        Returns:
            List of tool schema dictionaries for the agent's resources and workflows.
        """
        from dana.core.agent.components.prompt_engineer import generate_tool_schemas

        return generate_tool_schemas(
            agents=getattr(self._agent, "_agents", []),
            resources=getattr(self._agent, "_resources", []),
            workflows=getattr(self._agent, "_workflows", []),
        )

    def persist(self) -> None:
        if self._template is None:
            raise ValueError(f"[{self.__class__.__qualname__}] Template for {self._agent.__class__.__qualname__} is not generated yet")
        res = self._store.create_snapshot(
            self._template,
            provenance={
                "source": "auto-generated",
                "reasoning": "auto-generated",
                "parent_version": None,
                "force_generate": self._force_generate,
            },
            metrics={},
        )
        self._store.set_active(res.version)
        logger.info(
            f"Prompt template persisted for {self._agent.__class__.__qualname__} and codec {self._codec.__qualname__} with version {res.version}"
        )

    def load(self) -> str | None:
        snapshot = self._store.get_active(error_if_not_found=False)
        if snapshot is None:
            return None
        return snapshot.content
