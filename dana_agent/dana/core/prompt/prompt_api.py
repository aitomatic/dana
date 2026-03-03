from abc import abstractmethod
import re
from typing import TYPE_CHECKING

from structlog import get_logger

from dana.common.protocols import Persistable, PrivatePromptsProtocol, PublicPromptsProtocol
from dana.core.knowledge.prompts.codecs import AbstractCodec
from dana.core.knowledge.prompts.prompt_engineer import (
    AgentPromptEngineer,
    BasePromptEngineer,
    ResourcePromptEngineer,
    WorkflowPromptEngineer,
)
from dana.core.prompt.environment_info import EnvironmentInfo
from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryFactory, RepositoryType


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
    def reset(self) -> None: ...

    @abstractmethod
    def persist(self) -> None: ...

    @abstractmethod
    def load(self) -> str | None: ...

    @abstractmethod
    def render(self, template: str) -> str: ...


TEMPLATE_SYSTEM_PROMPT = """
{{identity}}

# Core Principles

<guardrails>
**Safety boundaries:**
- Refuse requests for harmful, illegal, or deceptive content
- Protect user privacy - never expose credentials, PII, or sensitive data in outputs
- When uncertain about appropriateness, ask for clarification before proceeding

**Quality principles:**
- Prioritize accuracy over validation. If the user's approach seems suboptimal, explain why and propose alternatives.
- Verify your work before responding - did you fully address the request?
</guardrails>

# Task Management

You have access to the `todo_write` tool to plan and track tasks. Use it frequently to:
- Break complex tasks into discrete steps
- Give users visibility into your progress
- Avoid forgetting important subtasks

**CRITICAL:** Mark todos as completed IMMEDIATELY after finishing each task. Never batch completions.

<example>
user: Run the build and fix any type errors
assistant: [Creates todos: "Run build", "Fix type errors"]
→ Runs build → finds 3 type errors
→ [Expands to 3 specific error fix todos]
→ [Marks error #1 in_progress] → fixes → [Marks #1 completed]
→ [Marks error #2 in_progress] → fixes → [Marks #2 completed]
→ [Marks error #3 in_progress] → fixes → [Marks #3 completed]
→ [Marks "Fix type errors" completed]
</example>

# Doing Tasks

- Tool results and user messages may include `<system-reminder>` tags containing contextual information and reminders added by the system.
- The conversation has unlimited context through automatic summarization.

<available_tools>
{{available_tools_prompt}}
</available_tools>

{{available_skills_prompt}}

<tool_usage>
**Rules:**
1. Follow tool schemas exactly as specified above.
2. Never mention tool names to users. Say "I'll search for that" not "I need to use the search tool."
3. Only call tools listed above.
4. Only call tools when necessary - if you know the answer, respond directly.

**Strategy:**
- PARALLEL: Call multiple independent tools in ONE response. Need data for 5 items? Make 5 calls at once.
- SEQUENTIAL: Chain tools only when output of one feeds into another.

**Handling Failures:**
- If a tool fails, try an alternative approach (different parameters, different tool).
- After 2-3 failed attempts on the SAME sub-problem, explain what you tried and provide what information you have.
</tool_usage>

<output_format>
{{tool_instruction_prompt}}

**Response Guidelines:**
- Match response length to request: short questions get concise answers; detailed requests get comprehensive responses.
- Synthesize tool results into a coherent answer - don't dump raw output.
- If you used tools, briefly explain what you found before answering.
</output_format>

<problem_solving>
For every task:

1. **UNDERSTAND**: What is the user asking? What information do I need?

2. **PLAN**: For multi-step tasks, break into discrete steps. Call MULTIPLE INDEPENDENT tools in parallel when possible.

3. **EXECUTE**: Work through your plan. Use tool results to inform next steps. If a step fails, diagnose and retry.

4. **SYNTHESIZE**: After 2-3 tool call attempts on the SAME sub-problem without resolution, STOP and synthesize. A good partial answer beats endless searching.
</problem_solving>

<decision_framework>
**Act Independently When:**
- The request is clear (or you can reasonably infer intent)
- You have tools to complete the task
- The action is reversible or low-risk

**Ask for Clarification Only When:**
- Multiple valid interpretations exist AND you cannot reasonably infer intent
- Critical information is truly missing (not findable via tools)
- The action is irreversible AND high-impact AND you need explicit user choice

**Never Ask:**
- If you can find the answer yourself with available tools
- To delay or stall - if you're uncertain, make your best attempt and explain your reasoning
</decision_framework>

<autonomy>
You solve tasks through systematic tool use. Complete the user's request thoroughly and efficiently.

**Default Behavior:**
- ACT if you have the tools and information needed - don't ask permission
- VERIFY your work before responding - did you fully address the request?
- CONTINUE until completion unless you hit a true blocker
</autonomy>
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
        provider: str | None = None,
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
        self._provider = provider
        # Use provided factory or default
        self._repository_factory = repository_factory or DEFAULT_REPOSITORY_FACTORY
        # NOTE: This agent repository (changed from store) - created via factory
        self._store = self._repository_factory.create(
            RepositoryType.PROMPT,
            agent=self._agent,
            component=None,  # For system prompt template
            provider=self._provider,
        )
        # NOTE : Registry management will be added later
        self._agent_prompt_engineers = {}
        self._resource_prompt_engineers = {}
        self._workflow_prompt_engineers = {}
        self._env = EnvironmentInfo(agent, self.relative_path)
        self._system_prompt = None
        self._template = None

    def _instantiate_prompt_engineer(
        self, prompt_engineer_cls: type[BasePromptEngineer], component, relative_path: str, **kwargs
    ) -> BasePromptEngineer:
        # Create repository via factory with provider context
        repository = self._repository_factory.create(RepositoryType.PROMPT, agent=self._agent, component=component, provider=self._provider)
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
        return f"{self._codec.__qualname__}/{self._agent.object_id}/prompts"

    @property
    def public_description(self) -> str:
        if self not in self._agent_prompt_engineers:
            self._agent_prompt_engineers[self] = self._instantiate_prompt_engineer(
                self._agent_prompt_engineer_cls, self._agent, relative_path=f"{self.relative_path}/public_description"
            )
        return self._agent_prompt_engineers[self].load()

    @property
    def identity(self) -> str:
        # Check for identity override (used by fork subagents with skill content)
        if hasattr(self._agent, "_identity_override") and self._agent._identity_override:
            return self._agent._identity_override
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
            value = None
            if hasattr(self, variable):
                attr = getattr(self, variable)
                value = attr() if callable(attr) else attr
            elif hasattr(self._env, variable):
                attr = getattr(self._env, variable)
                value = attr() if callable(attr) else attr
            if value is not None:
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

    @property
    def available_skills_prompt(self) -> str:
        """Generate skills section for system prompt."""
        for resource in self._agent._resources:
            if hasattr(resource, "list_model_invocable"):
                skills = resource.list_model_invocable()
                if skills:
                    descriptions = resource.get_prompt_descriptions()
                    return f"""<available_skills>
# Available Skills

Skills are task templates you can invoke. When a user's request matches a skill,
use the skills resource to invoke it by name.

{descriptions}

To use a skill, call: skills.invoke(skill_name="<name>", args="<arguments>")
</available_skills>"""
        return ""

    def reset(self) -> None:
        pass

    def build_tool_schemas(self) -> list[dict]:
        """Build OpenAI-compatible tool schemas for native function calling.

        Returns:
            List of tool schema dictionaries for the agent's resources and workflows.
        """
        from dana.core.tool.tool_schema import generate_tool_schemas

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
