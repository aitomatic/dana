"""
STARAgent implementation using composition-based architecture.

This is the main STARAgent implementation using composition instead of mixin inheritance.
It provides a cleaner, more maintainable architecture for the STAR (See-Think-Act-Reflect) pattern
and conversational agent functionality using composable components.
"""

from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime
import inspect
from typing import Any
from uuid import uuid4
import warnings

import structlog

from dana.common.config import config_manager
from dana.common.llm.llm import LLM
from dana.common.observable import observable
from dana.common.protocols import AgentProtocol, DictParams, Notifiable, ResourceProtocol, WorkflowProtocol
from dana.common.protocols.types import LearningPhase
from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryFactory

from ..knowledge.prompts.codecs import AbstractCodec, CSXMLCodec
from ..knowledge.prompts.prompt_api import PromptAPIProtocol
from ..runtime import AgentRuntime
from .base_star_agent import BaseSTARAgent
from .components import Communicator, LearnerProtocol, State
from .components.observer import ObserverProtocol
from .timeline import Timeline, TimelineEntry, TimelineEntryType


logger = structlog.get_logger()

_CODEC_SENTINEL = object()


# from dana.apps.dana.thought_logger import ThoughtLogger  # Moved to avoid circular import


class STARAgent(BaseSTARAgent):
    """STARAgent implementation using composition-based architecture."""

    # Configuration constants
    MAX_THINK_RETRIES = 3  # Maximum retries when output format or done/response rules are invalid

    def __init__(
        self,
        agent_type: str | None = None,
        agent_id: str | None = None,
        llm_provider: str | None = None,
        model: str | None = None,
        config: dict[str, Any] | None = None,
        max_context_tokens: int = 32000,
        auto_register: bool = True,
        registry=None,
        codec: type[AbstractCodec] | None | object = _CODEC_SENTINEL,
        runtime: AgentRuntime | None = None,
        repository_factory: RepositoryFactory = DEFAULT_REPOSITORY_FACTORY,
        prompt_api: PromptAPIProtocol | None = None,
        observer: ObserverProtocol | None = None,
        learner: LearnerProtocol | None = None,
        ltmemory_path: str | None = None,
        enable_skills: bool = True,
        skills_output_dir: str = "./skill_output",
        enable_web_search: bool = True,
        enable_code_execution: bool = True,
        enable_assistant: bool = True,
        **kwargs,
    ):
        """
        Initialize the STARAgent with composition-based architecture.

        Args:
            agent_type: Type of agent (e.g., 'coding', 'financial_analyst').
            agent_id: ID of the agent (defaults to None)
            llm_provider: LLM provider name (e.g., 'anthropic', 'openai')
            model: Model name to use (defaults to provider's default)
            config: Optional configuration dictionary
            max_context_tokens: Maximum tokens for timeline context
            auto_register: Whether to automatically register with the global registry
            registry: Specific registry to use (defaults to global registry)
            enable_web_search: Whether to enable web search resource (default: True).
                Provides search() and fetch_url() methods without requiring API keys.
            enable_code_execution: Whether to enable code execution resource (default: True).
                Provides secure Python code execution in a sandbox.
            runtime: Runtime implementation that encapsulates prompt building, LLM calls,
                response parsing, and tool execution. Defaults to DefaultRuntime.
            codec: Deprecated. Use runtime instead.
                - Default: maps to DefaultRuntime.
                - If explicitly set to None: uses LegacyRuntime.
            ltmemory_path: Optional path for long-term memory storage (enables cross-session learning)
            enable_skills: Whether to enable Claude Code skills resource discovery
            skills_output_dir: Directory to use for skill output files
            enable_code_execution: Whether to enable code execution resource (default: True).
                Provides safe Python code execution with timeout and module restrictions.
            enable_assistant: Whether to enable the built-in AssistantAgent (default: True).
                The assistant can search the web and execute code, returning concise results.
                Useful for delegating subtasks that require research or computation.
            **kwargs: Additional arguments passed to components
        """
        # Initialize base class first (handles registration)
        kwargs |= {
            "agent_type": agent_type,
            "agent_id": agent_id,
            "auto_register": auto_register,
            "registry": registry,
        }
        super().__init__(**kwargs)

        # Determine effective LLM provider: explicit > first available > anthropic fallback
        if llm_provider is None:
            llm_provider = config_manager.get_first_available_provider() or "anthropic"

        # Initialize LLM (lazy - only created when first accessed)
        self._llm_client = None  # Explicit init to avoid __getattr__ interception
        self._llm_config = {
            "provider": llm_provider,
            "model": model,
        }

        self._session_id = str(uuid4())
        self._repository_factory = repository_factory
        codec_provided = codec is not _CODEC_SENTINEL
        if codec is _CODEC_SENTINEL:
            codec = CSXMLCodec
        self._codec = codec

        if runtime is None:
            if codec is None:
                # codec=None explicitly triggers LegacyRuntime (deprecated)
                if codec_provided:
                    warnings.warn(
                        "codec=None is deprecated and will be removed in a future version. "
                        "LegacyRuntime is no longer maintained. Use DefaultRuntime instead.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                from dana.core.runtime.legacy import LegacyRuntime

                runtime = LegacyRuntime()
            else:
                # Use the runtime registry to choose the appropriate runtime
                from dana.core.runtime import RuntimeRegistry

                runtime = RuntimeRegistry.select_runtime(provider=llm_provider, model=model)
                if codec_provided:
                    warnings.warn(
                        "The codec parameter is deprecated; pass runtime=... instead.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
        else:
            if codec_provided:
                warnings.warn(
                    "The codec parameter is deprecated and ignored when runtime is provided.",
                    DeprecationWarning,
                    stacklevel=2,
                )

        self._runtime = runtime

        # Initialize other components
        self._communicator = Communicator(self)
        self._state = State(self)
        # self._learner = learner or Learner(self, repository_factory=self._repository_factory)
        self._learner = learner
        if self._learner is not None:
            self._learner._agent = self

        # Initialize long-term memory if path provided
        if ltmemory_path:
            from dana.core.memory import LTMemory

            self._ltmemory = LTMemory(
                path=ltmemory_path,
                llm_provider=llm_provider,
                llm_model=model or config_manager.get_provider_default_model(llm_provider),
            )
        else:
            self._ltmemory = None

        # Determine storage_config for timeline and event_log

        # Initialize timeline at agent level with agent, codec, and storage_config
        self._timeline = Timeline(
            max_context_tokens=max_context_tokens,
            agent=self,
            repository_factory=self._repository_factory,
        )

        # Initialize EventLog API (only if observer AND codec provided)
        # Events ONLY come from Observer - no observer = no EventLog
        if observer is not None:
            from dana.core.agent.components.event_log_api import EventLogAPI

            self._event_log = EventLogAPI(
                agent=self,
                observer=observer,  # REQUIRED - EventLog only works with Observer
                repository_factory=self._repository_factory,
            )
        else:
            # No observer or codec = no EventLog (events only come from Observer)
            self._event_log = None

        if enable_web_search:
            try:
                from dana.core.resource.simple_search import SimpleWebSearch

                self.with_resources(SimpleWebSearch(resource_id="web-search"))
            except ImportError:
                pass  # Web search not available

        if enable_skills:
            from dana.core.skills import ClaudeCodeSkills

            skills = ClaudeCodeSkills(output_dir=skills_output_dir)
            if skills.enabled:
                self.with_resources(skills)

        if enable_code_execution:
            try:
                from dana.common.resource.code_execution_resource import CodeExecutionResource

                self.with_resources(CodeExecutionResource())
            except ImportError:
                pass  # Code execution not available

        if enable_assistant:
            from dana.core.agent.assistant_agent import AssistantAgent

            # Create assistant with web search and code execution
            # The assistant runs in its own context, so it needs its own resources
            assistant = AssistantAgent(
                agent_id=f"{self.agent_id}_assistant",
                auto_register=False,  # Don't register sub-agent globally
            )
            self.with_agents(assistant)

    def set_session_id(self, session_id: str) -> None:
        """Set the session id for the agent."""
        self._session_id = session_id

    @property
    def llm_client(self) -> LLM:
        """Get the LLM client."""
        if self._llm_client is None:
            self._llm_client = LLM(provider=self._llm_config["provider"], model=self._llm_config["model"])
        return self._llm_client

    @llm_client.setter
    def llm_client(self, value: LLM):
        """Set the LLM client."""
        self._llm_client = value
        if hasattr(self._runtime, "set_llm"):
            self._runtime.set_llm(value)

    # ============================================================================
    # PUBLIC API - AGENT IDENTITY & PROMPTS
    # ============================================================================

    def with_agents(self, *agents: AgentProtocol) -> BaseSTARAgent:
        """Add agents to the agent."""
        if hasattr(self._runtime, "reset"):
            self._runtime.reset()
        super().with_agents(*agents)
        return self

    def with_resources(self, *resources: ResourceProtocol) -> BaseSTARAgent:
        """Add resources to the agent."""
        if hasattr(self._runtime, "reset"):
            self._runtime.reset()
        super().with_resources(*resources)
        return self

    def with_workflows(self, *workflows: WorkflowProtocol) -> BaseSTARAgent:
        """Add workflows to the agent."""
        if hasattr(self._runtime, "reset"):
            self._runtime.reset()
        super().with_workflows(*workflows)
        return self

    def with_notifiable(self, *notifiables: Notifiable) -> BaseSTARAgent:
        """Add notifiables to the agent."""
        for agent in self._agents:
            agent.with_notifiable(*notifiables)
        for resource in self._resources:
            resource.with_notifiable(*notifiables)
        for workflow in self._workflows:
            workflow.with_notifiable(*notifiables)
        super().with_notifiable(*notifiables)
        return self

    @property
    def public_description(self) -> str:
        """Get the public description of the agent."""
        if hasattr(self._runtime, "public_description"):
            return self._runtime.public_description(self)
        return inspect.getdoc(self.__class__) or f"{self.agent_type} agent."

    @property
    def private_identity(self) -> str:
        """Get the private identity of the agent."""
        if hasattr(self._runtime, "private_identity"):
            return self._runtime.private_identity(self)
        return super().private_identity

    @property
    def system_prompt(self) -> str:
        """Get the system prompt of the agent."""
        if hasattr(self._runtime, "system_prompt"):
            return self._runtime.system_prompt(self)
        return super().system_prompt

    # ============================================================================
    # PUBLIC API - STATE & CONTEXT MANAGEMENT
    # ============================================================================

    def get_state(self) -> dict[str, Any]:
        """Get current agent state as dictionary."""
        return self._state.get_state()

    # ============================================================================
    # PUBLIC API - TIMELINE & CONVERSATION
    # ============================================================================

    def get_timeline_summary(self) -> str:
        """Get a summary of the agent's timeline."""
        return self._timeline.get_timeline_summary()

    def query(self, **kwargs) -> DictParams:
        # Generate session_id if not provided
        new_session_id = kwargs.get("session_id")
        if new_session_id is not None:
            self.set_session_id(new_session_id)
        session_id = self._session_id

        # Set session_id for EventLog if it exists
        if hasattr(self, "_event_log") and self._event_log is not None:
            self._event_log._current_session_id = session_id

        try:
            result = super().query(**kwargs)
            return result
        finally:
            # Save events if EventLog exists
            if hasattr(self, "_event_log") and self._event_log is not None:
                self._event_log.save(session_id)

            # Save timeline (agent, codec, storage_config already set in __init__)
            if hasattr(self, "_timeline") and self._timeline is not None:
                self._timeline.save(session_id)

    async def aquery(self, **kwargs) -> DictParams:
        # Generate session_id if not provided
        new_session_id = kwargs.get("session_id")
        if new_session_id is not None:
            self.set_session_id(new_session_id)
        session_id = self._session_id

        # Set session_id for EventLog if it exists
        if hasattr(self, "_event_log") and self._event_log is not None:
            self._event_log._current_session_id = session_id

        try:
            result = await super().aquery(**kwargs)
            return result
        finally:
            # Save events if EventLog exists
            if hasattr(self, "_event_log") and self._event_log is not None:
                self._event_log.save(session_id)

            # Save timeline (agent, codec, storage_config already set in __init__)
            if hasattr(self, "_timeline") and self._timeline is not None:
                self._timeline.save(session_id)

    def converse(self, initial_message: str | None = None, session_id: str | None = None) -> None:
        """Interactive conversation loop with a human user.

        Args:
            initial_message: Optional initial message to start the conversation
            session_id: Optional session identifier. If None, generates UUID.
        """
        self._communicator.converse(initial_message=initial_message, session_id=session_id)

    async def aconverse(
        self,
        initial_message: str | None = None,
        session_id: str | None = None,
        input_handler: Callable[[], Awaitable[str]] | None = None,
    ) -> None:
        """Async interactive conversation loop with pluggable input handler.

        Args:
            initial_message: Optional initial message to start the conversation
            session_id: Optional session identifier. If None, generates UUID.
            input_handler: Async callable that returns user input string.
                          If None, uses default blocking input() wrapped in executor.
        """
        await self._communicator.aconverse(
            initial_message=initial_message,
            session_id=session_id,
            input_handler=input_handler,
        )

    def __getattr__(self, name: str):
        """
        Magic function: Convert unknown method calls to natural language and call converse.

        Examples:
            agent.hi_how_are_you() -> converse("hi how are you")
            agent.research_coffee_companies() -> converse("research coffee companies")
            agent.find_exporters_in_dak_lak() -> converse("find exporters in dak lak")
        """

        def magic_method(*args, **kwargs):
            # Convert method name to natural language
            # Replace underscores with spaces and clean up
            natural_language = name.replace("_", " ").strip()

            # Add any positional arguments as additional context
            if args:
                args_str = " ".join(str(arg) for arg in args)
                natural_language += f" {args_str}"

            # Add any keyword arguments as additional context
            if kwargs:
                kwargs_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
                natural_language += f" {kwargs_str}"

            # Call converse with the natural language message (starts interactive conversation)
            return self.converse(initial_message=natural_language)

        return magic_method

    # ============================================================================
    # TIMELINE COMPRESSION
    # ============================================================================

    def _maybe_compress_timeline(self, timeline: Timeline) -> None:
        """
        Compress timeline if it exceeds the configured threshold.

        Uses the LLM to summarize old entries, preserving recent context.
        This prevents unbounded context growth in long conversations.
        """
        if not timeline.needs_compression():
            return

        compression_prompt = timeline.build_compression_prompt()
        if not compression_prompt:
            return

        try:
            # Use a quick LLM call to summarize old entries
            from dana.common.llm.types import LLMMessage

            summary_response = self.llm_client.chat_response_sync(
                [LLMMessage(role="user", content=compression_prompt)],
                agent_id=self.object_id,
                agent_type=self.agent_type,
                temperature=0,
            )

            raw_content = summary_response.content.strip() if summary_response.content else ""

            # Parse JSON response to extract summary
            summary = self._extract_compression_summary(raw_content)

            if summary:
                compressed_count = timeline.compress_old_entries(summary)
                logger.info(
                    "Timeline compressed",
                    agent_id=self.object_id,
                    compressed_entries=compressed_count,
                    summary_length=len(summary),
                )
        except Exception as e:
            # Don't fail the main operation if compression fails
            logger.warning("Timeline compression failed", error=str(e))

    async def _maybe_compress_timeline_async(self, timeline: Timeline) -> None:
        """Async version of _maybe_compress_timeline."""
        if not timeline.needs_compression():
            return

        compression_prompt = timeline.build_compression_prompt()
        if not compression_prompt:
            return

        try:
            from dana.common.llm.types import LLMMessage

            summary_response = await self.llm_client.chat_response(
                [LLMMessage(role="user", content=compression_prompt)],
                agent_id=self.object_id,
                agent_type=self.agent_type,
                temperature=0,
            )

            raw_content = summary_response.content.strip() if summary_response.content else ""

            # Parse JSON response to extract summary
            summary = self._extract_compression_summary(raw_content)

            if summary:
                compressed_count = timeline.compress_old_entries(summary)
                logger.info(
                    "Timeline compressed",
                    agent_id=self.object_id,
                    compressed_entries=compressed_count,
                    summary_length=len(summary),
                )
        except Exception as e:
            logger.warning("Timeline compression failed", error=str(e))

    def _extract_compression_summary(self, content: str) -> str:
        """Extract summary from JSON compression response.

        Args:
            content: Raw LLM response (expected JSON with 'summary' field)

        Returns:
            Extracted summary text, or the raw content as fallback
        """
        import json

        if not content:
            return ""

        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "summary" in parsed:
                return parsed["summary"]
        except json.JSONDecodeError:
            pass

        # Fallback: return raw content if not valid JSON
        return content

    # ============================================================================
    # STAR PATTERN IMPLEMENTATION (BaseSTARAgent abstract methods)
    # ============================================================================

    @observable
    def _see(self, trace_inputs: DictParams) -> DictParams:
        """
        SEE: See the user/caller inputs and produce percepts.

        Args:
            trace_inputs (DictParams): any new user/agent inputs, plus trace_outputs from the previous loop (if any)
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.
              - response (str): Response from the previous loop (if any)
              - tool_calls (list[DictParams]): Tool calls from the previous loop (if any)
              - tool_results (list[DictParams]): Tool results from the previous loop (if any)

        Returns:
            - trace_percepts (DictParams): the percepts produced by this SEE phase.
              - timeline (Timeline): Timeline of the agent, appending any new entries from our perceptions
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.
        """

        # Input parameter checking
        trace_inputs = trace_inputs or {}
        if self._do_exit_star_loop(trace_inputs):
            return {"trace_percepts": self._mark_star_loop_exit(trace_inputs)}

        previous_tool_calls: list[DictParams] = trace_inputs.get("tool_calls", None)
        if previous_tool_calls:
            # This is a subsequent loop - perceiving tool results
            tool_results = trace_inputs.get("tool_results", [])
            num_results = len(tool_results) if isinstance(tool_results, list) else 0

            # Add perception message for notification visibility
            trace_inputs["perception"] = f"Perceived {num_results} tool result(s)"

            del trace_inputs["response"]
            del trace_inputs["tool_calls"]
            del trace_inputs["tool_results"]
        else:
            # This is the first loop
            caller_message: str = trace_inputs.get("caller_message", trace_inputs.get("message", None))
            if not caller_message:
                return {"trace_percepts": self._mark_star_loop_exit(trace_inputs)}

            # Add caller_message to timeline
            if isinstance(caller_message, str):
                # Note: is_latest_user_message is for legacy compatibility (LegacyRuntime)
                # The simplified build_prompt just outputs timeline in order
                new_entry = TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=caller_message, is_latest_user_message=True)
                self._timeline.add_entry(new_entry)

            # Preserve caller_message for notifications but remove original keys
            trace_inputs.pop("message", None)  # Remove 'message' alias
            # Keep caller_message in trace_inputs for notification
            if "caller_message" not in trace_inputs:
                trace_inputs["caller_message"] = caller_message

        trace_inputs |= {"timeline": self._timeline}

        return super()._see(trace_inputs)

    def _format_tool_call_as_xml(self, tool_call: DictParams) -> str:
        """Format a tool call dict as XML for consistent LLM context.

        This ensures the LLM sees tool calls in the same XML format it should
        produce, rather than Python dict format which it might mimic.
        """
        func = tool_call.get("function", "unknown:unknown")
        args = tool_call.get("arguments", {})

        # Build XML parameters
        params_xml = ""
        for key, value in args.items():
            params_xml += f'<parameter name="{key}">{value}</parameter>'

        return f'<function_call><invoke name="{func}">{params_xml}</invoke></function_call>'

    @observable
    def _think(self, trace_percepts: DictParams) -> DictParams:
        """
        THINK: Think about the percepts and produce thoughts. This is where we make an LLM call.

        Args:
            trace_percepts (DictParams): the percepts produced by this SEE phase.
              - timeline (Timeline): Timeline of the agent.

        Returns:
            - trace_thoughts (DictParams): the thoughts produced by this THINK phase.
              - response (str): Response from the LLM
              - tool_calls (list[DictParams]): Tool calls from the LLM
        """

        # Input parameter checking
        trace_percepts = trace_percepts or {}
        if self._do_exit_star_loop(trace_percepts) or not trace_percepts:
            return {"trace_thoughts": self._mark_star_loop_exit(trace_percepts)}

        timeline: Timeline = trace_percepts.get("timeline", self._timeline)
        trace_percepts.pop("timeline", None)

        # Check if timeline needs compression before building messages
        self._maybe_compress_timeline(timeline)

        # Build LLM messages using runtime
        llm_messages = self._runtime.build_prompt(self, timeline)

        response, reasoning, tool_calls, done, todo_list = None, None, [], None, None
        output_state = "retry"
        for attempt in range(self.MAX_THINK_RETRIES):
            raw = self._runtime.call_llm(llm_messages)
            parsed = self._runtime.parse_response(raw)
            response, reasoning, tool_calls, done, todo_list = (
                parsed.response,
                parsed.reasoning,
                parsed.tool_calls,
                parsed.done,
                parsed.todo_list,
            )

            has_tool_calls = bool(tool_calls)
            has_response = bool(response and response.strip())
            output_state = self._runtime.validate_done_output(done, has_tool_calls, has_response)

            if output_state != "retry":
                break

            if attempt < self.MAX_THINK_RETRIES - 1:
                llm_messages.append(self._runtime.build_output_format_correction())
                logger.warning(
                    "Invalid output format, retrying",
                    attempt=attempt + 1,
                    done=done,
                    has_tool_calls=has_tool_calls,
                    has_response=has_response,
                )

        if output_state == "retry":
            response = "No response generated"
            tool_calls = []
            done = True
            output_state = "exit"

        if not tool_calls or len(tool_calls) == 0:
            response = response if (response and len(response) > 0) else "No response generated"
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.AGENT_RESPONSE,
                    content=response,
                )
            )
        else:
            if reasoning and len(reasoning) > 0:
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.AGENT_THOUGHTS,
                        content=reasoning,
                    )
                )

            if response and len(response) > 0:
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.AGENT_THOUGHTS,
                        content=response,
                    )
                )

            # Add todo_list BEFORE tool calls so it doesn't break the tool_call → tool_result sequence
            # (OpenAI requires tool results immediately after tool calls)
            if todo_list:
                in_progress = [t for t in todo_list if t.status == "in_progress"]
                pending = [t for t in todo_list if t.status == "pending"]
                completed = [t for t in todo_list if t.status == "completed"]
                logger.info(
                    "Todo list updated",
                    in_progress=len(in_progress),
                    pending=len(pending),
                    completed=len(completed),
                )
                # Format todo_list for timeline
                todo_lines = []
                for item in todo_list:
                    status_marker = {"in_progress": "[IN PROGRESS]", "pending": "[PENDING]", "completed": "[COMPLETED]"}.get(
                        item.status, "[?]"
                    )
                    todo_lines.append(f"{status_marker} {item.content}")
                # Remove any existing TODO_LIST entries to avoid accumulation
                timeline.timeline = [e for e in timeline.timeline if e.entry_type != TimelineEntryType.TODO_LIST]
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.TODO_LIST,
                        content="\n".join(todo_lines),
                    )
                )

            # Check if these are native tool calls (have tool_call_id)
            has_native_tool_calls = any(tc.get("tool_call_id") for tc in tool_calls)

            if has_native_tool_calls:
                # For native OpenAI tools, store all tool_calls in a single entry
                # The tool_calls will be converted to proper OpenAI format when building messages
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.TOOL_CALL,
                        content="",  # Content is empty for native tool calls
                        tool_calls=tool_calls,  # Store native tool_calls array
                    )
                )
            else:
                # Legacy XML format - store each tool call separately
                for tool_call in tool_calls:
                    timeline.add_entry(
                        TimelineEntry(
                            entry_type=TimelineEntryType.TOOL_CALL,
                            content=self._format_tool_call_as_xml(tool_call),
                        )
                    )

        # Output parameter checking
        response = response or ""
        assert isinstance(response, str)
        assert isinstance(tool_calls, list)
        trace_percepts |= {
            "response": response,
            "reasoning": reasoning,
            "tool_calls": tool_calls,
            "done": done,
            "todo_list": todo_list,
        }

        if output_state == "exit":
            trace_percepts = self._mark_star_loop_exit(trace_percepts)

        return super()._think(trace_percepts)

    @observable
    def _act(self, trace_thoughts: DictParams) -> DictParams:
        """
        ACT: Execute tool calls and return results.
        TODO: this is a good place to send interactive feedback to the user before making tool calls

        Args:
            trace_thoughts (DictParams): the thoughts produced by this THINK phase.
              - response (str): Response from the LLM from the THINK phase.
              - tool_calls (list[DictParams]): Tool calls from the THINK phase.
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.

        Returns:
            - trace_outputs (DictParams): the outputs produced by this ACT phase.
              - response (str): Response from the LLM from the THINK phase.
              - tool_calls (list[DictParams]): Tool calls from the THINK phase.
              - tool_results: list[DictParams]: Tool results from the ACT phase if there are tool calls
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.
        """

        # Input parameter checking
        trace_thoughts = trace_thoughts or {}
        if not trace_thoughts or self._do_exit_star_loop(trace_thoughts):
            return {"trace_outputs": self._mark_star_loop_exit(trace_thoughts)}

        tool_calls: list[DictParams] = trace_thoughts.get("tool_calls")

        # Execute tool calls using runtime
        tool_results = self._runtime.execute_tools(self, tool_calls)

        # Add tool results to timeline
        if isinstance(tool_results, list):
            for tool_result in tool_results:
                if isinstance(tool_result, dict):
                    # Determine entry type based on tool type
                    tool_type = tool_result.get("type")
                    if tool_type == "agent":
                        entry_type = TimelineEntryType.SUB_AGENT_RESPONSE
                    elif tool_type == "resource":
                        entry_type = TimelineEntryType.RESOURCE_RESULT
                    elif tool_type == "workflow":
                        entry_type = TimelineEntryType.WORKFLOW_RESULT
                    else:  # unknown
                        entry_type = TimelineEntryType.UNKNOWN_TOOL_CALL

                    # Include tool_call_id for OpenAI native tool support
                    self._timeline.add_entry(
                        TimelineEntry(
                            entry_type=entry_type,
                            content=tool_result.get("result", "Unknown tool result"),
                            tool_call_id=tool_result.get("tool_call_id"),
                        )
                    )

            # Add a system reminder to continue if task is not complete
            # Find original user request
            original_request = ""
            for entry in self._timeline.timeline:
                if entry.entry_type == TimelineEntryType.USER_MESSAGE:
                    original_request = entry.content
                    break

            # Count completed tool calls to estimate progress
            tool_call_count = sum(1 for entry in self._timeline.timeline if entry.entry_type == TimelineEntryType.TOOL_CALL)

            # Estimate expected steps based on sequential action patterns
            # "search then fetch" = 2 steps, "search, then process, then save" = 3 steps
            request_lower = original_request.lower()
            # Count occurrences of step separators (avoiding overlap)
            import re

            step_separators = re.findall(r"\bthen\b|\bafter that\b|\bnext\b|\bfinally\b", request_lower)
            expected_steps = 1 + len(step_separators)
            # Cap expected_steps at a reasonable maximum
            expected_steps = min(expected_steps, 5)

            # Only add reminder if we haven't completed all expected steps
            if tool_call_count < expected_steps:
                remaining = expected_steps - tool_call_count
                self._timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.AGENT_THOUGHTS,
                        content=f"[MULTI-STEP TASK - {remaining} STEP(S) REMAINING] "
                        f"Completed {tool_call_count}/{expected_steps} steps. "
                        "I MUST call the next tool using this EXACT XML format: "
                        '<function_call><invoke name="resource-id:method"><parameter name="param">value</parameter></invoke></function_call>',
                    )
                )

        # Output parameter checking
        assert isinstance(tool_results, list)
        trace_thoughts |= {"tool_results": tool_results}

        return super()._act(trace_thoughts)

    # @observable
    def _reflect(self, trace_outputs: DictParams) -> DictParams:
        """
        REFLECT: Reflect on the actions or episode, depending on the reflection phase.

        Args:
            trace_outputs (DictParams): the outputs produced by this ACT phase.
              - phase (LearningPhase): specifies which learning phase we are in
              - response (str): Response from the THINK phase.
              - tool_calls (list[DictParams]): Tool calls from the THINK phase.
              - tool_results (list[DictParams]): Tool results from the ACT phase.
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.

        Returns:
            - trace_learning (DictParams): the learning produced by this REFLECT phase.
        """

        # Input parameter checking
        trace_outputs = trace_outputs or {}
        if not trace_outputs or self._do_exit_star_loop(trace_outputs):
            return {"trace_learning": self._mark_star_loop_exit(trace_outputs)}
        phase: LearningPhase = trace_outputs.get("phase") or LearningPhase.ACQUISITIVE

        trace_learning = {}
        if self._learner is not None:
            match phase:
                case LearningPhase.ACQUISITIVE:
                    trace_learning |= self._learner._reflect_acquisitive(trace_outputs)
                    trace_learning["learning_note"] = "Initial learning and trial-level plasticity"

                case LearningPhase.EPISODIC:
                    trace_learning |= self._learner._reflect_episodic(trace_outputs)
                    trace_learning["learning_note"] = "Episodic binding of information"

                case LearningPhase.INTEGRATIVE:
                    trace_learning |= self._learner._reflect_integrative(trace_outputs)
                    trace_learning["learning_note"] = "Offline replay and integration"

                case LearningPhase.RETENTIVE:
                    trace_learning |= self._learner._reflect_retentive(trace_outputs)
                    trace_learning["learning_note"] = "Long-term maintenance and habit formation"

                case _:
                    raise ValueError(f"Unknown learning phase {phase}")

            trace_learning |= {
                "timestamp": datetime.now().isoformat(),
                "phase": phase.value,
            }

            # Add to timeline for persistence
            self._timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.AGENT_LEARNING,
                    content=f"Learning ({phase.value}): {trace_learning.get('learning_note', 'No learning note')}",
                )
            )

        return super()._reflect(trace_learning)

    # ============================================================================
    # ASYNC STAR METHODS
    # ============================================================================

    @observable
    async def _think_async(self, trace_percepts: DictParams) -> DictParams:
        """
        THINK (async): Async version of _think with native async LLM calls.

        Args:
            trace_percepts (DictParams): the percepts produced by this SEE phase.
              - timeline (Timeline): Timeline of the agent.

        Returns:
            - trace_thoughts (DictParams): the thoughts produced by this THINK phase.
              - response (str): Response from the LLM
              - tool_calls (list[DictParams]): Tool calls from the LLM
        """

        # Input parameter checking
        trace_percepts = trace_percepts or {}
        if self._do_exit_star_loop(trace_percepts) or not trace_percepts:
            return {"trace_thoughts": self._mark_star_loop_exit(trace_percepts)}

        timeline: Timeline = trace_percepts.get("timeline", self._timeline)
        trace_percepts.pop("timeline", None)

        # Check if timeline needs compression before building messages
        await self._maybe_compress_timeline_async(timeline)

        # Build LLM messages using runtime
        llm_messages = self._runtime.build_prompt(self, timeline)

        response, reasoning, tool_calls, done, todo_list = None, None, [], None, None
        output_state = "retry"
        for attempt in range(self.MAX_THINK_RETRIES):
            if hasattr(self._runtime, "call_llm_async"):
                raw = await self._runtime.call_llm_async(llm_messages)
            else:
                import asyncio

                raw = await asyncio.to_thread(self._runtime.call_llm, llm_messages)
            parsed = self._runtime.parse_response(raw)
            response, reasoning, tool_calls, done, todo_list = (
                parsed.response,
                parsed.reasoning,
                parsed.tool_calls,
                parsed.done,
                parsed.todo_list,
            )

            has_tool_calls = bool(tool_calls)
            has_response = bool(response and response.strip())
            output_state = self._runtime.validate_done_output(done, has_tool_calls, has_response)

            if output_state != "retry":
                break

            if attempt < self.MAX_THINK_RETRIES - 1:
                llm_messages.append(self._runtime.build_output_format_correction())
                logger.warning(
                    "Invalid output format, retrying",
                    attempt=attempt + 1,
                    done=done,
                    has_tool_calls=has_tool_calls,
                    has_response=has_response,
                )

        if output_state == "retry":
            response = "No response generated"
            tool_calls = []
            done = True
            output_state = "exit"

        if not tool_calls or len(tool_calls) == 0:
            response = response if (response and len(response) > 0) else "No response generated"
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.AGENT_RESPONSE,
                    content=response,
                )
            )
        else:
            if reasoning and len(reasoning) > 0:
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.AGENT_THOUGHTS,
                        content=reasoning,
                    )
                )

            if response and len(response) > 0:
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.AGENT_THOUGHTS,
                        content=response,
                    )
                )

            # Add todo_list BEFORE tool calls so it doesn't break the tool_call → tool_result sequence
            # (OpenAI requires tool results immediately after tool calls)
            if todo_list:
                in_progress = [t for t in todo_list if t.status == "in_progress"]
                pending = [t for t in todo_list if t.status == "pending"]
                completed = [t for t in todo_list if t.status == "completed"]
                logger.info(
                    "Todo list updated",
                    in_progress=len(in_progress),
                    pending=len(pending),
                    completed=len(completed),
                )
                # Format todo_list for timeline
                todo_lines = []
                for item in todo_list:
                    status_marker = {"in_progress": "[IN PROGRESS]", "pending": "[PENDING]", "completed": "[COMPLETED]"}.get(
                        item.status, "[?]"
                    )
                    todo_lines.append(f"{status_marker} {item.content}")
                # Remove any existing TODO_LIST entries to avoid accumulation
                timeline.timeline = [e for e in timeline.timeline if e.entry_type != TimelineEntryType.TODO_LIST]
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.TODO_LIST,
                        content="\n".join(todo_lines),
                    )
                )

            # Check if these are native tool calls (have tool_call_id)
            has_native_tool_calls = any(tc.get("tool_call_id") for tc in tool_calls)

            if has_native_tool_calls:
                # For native OpenAI tools, store all tool_calls in a single entry
                # The tool_calls will be converted to proper OpenAI format when building messages
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.TOOL_CALL,
                        content="",  # Content is empty for native tool calls
                        tool_calls=tool_calls,  # Store native tool_calls array
                    )
                )
            else:
                # Legacy XML format - store each tool call separately
                for tool_call in tool_calls:
                    timeline.add_entry(
                        TimelineEntry(
                            entry_type=TimelineEntryType.TOOL_CALL,
                            content=self._format_tool_call_as_xml(tool_call),
                        )
                    )

        # Output parameter checking
        response = response or ""
        assert isinstance(response, str)
        assert isinstance(tool_calls, list)
        trace_percepts |= {
            "response": response,
            "reasoning": reasoning,
            "tool_calls": tool_calls,
            "done": done,
            "todo_list": todo_list,
        }

        if output_state == "exit":
            trace_percepts = self._mark_star_loop_exit(trace_percepts)

        # Call parent's base implementation (sync is fine, just data manipulation)
        result = {"trace_thoughts": trace_percepts}
        self.broadcast(result)
        return result

    @observable
    async def _act_async(self, trace_thoughts: DictParams) -> DictParams:
        """
        ACT (async): Async version of _act with native async tool execution.

        Args:
            trace_thoughts (DictParams): the thoughts produced by this THINK phase.
              - response (str): Response from the LLM from the THINK phase.
              - tool_calls (list[DictParams]): Tool calls from the THINK phase.
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.

        Returns:
            - trace_outputs (DictParams): the outputs produced by this ACT phase.
              - response (str): Response from the LLM from the THINK phase.
              - tool_calls (list[DictParams]): Tool calls from the THINK phase.
              - tool_results: list[DictParams]: Tool results from the ACT phase if there are tool calls
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.
        """

        # Input parameter checking
        trace_thoughts = trace_thoughts or {}
        if not trace_thoughts or self._do_exit_star_loop(trace_thoughts):
            return {"trace_outputs": self._mark_star_loop_exit(trace_thoughts)}

        tool_calls: list[DictParams] = trace_thoughts.get("tool_calls")

        # Execute tool calls using runtime
        if hasattr(self._runtime, "execute_tools_async"):
            tool_results = await self._runtime.execute_tools_async(self, tool_calls)
        else:
            import asyncio

            tool_results = await asyncio.to_thread(self._runtime.execute_tools, self, tool_calls)

        # Add tool results to timeline
        if isinstance(tool_results, list):
            for tool_result in tool_results:
                if isinstance(tool_result, dict):
                    # Determine entry type based on tool type
                    tool_type = tool_result.get("type")
                    if tool_type == "agent":
                        entry_type = TimelineEntryType.SUB_AGENT_RESPONSE
                    elif tool_type == "resource":
                        entry_type = TimelineEntryType.RESOURCE_RESULT
                    elif tool_type == "workflow":
                        entry_type = TimelineEntryType.WORKFLOW_RESULT
                    else:  # unknown
                        entry_type = TimelineEntryType.UNKNOWN_TOOL_CALL

                    # Include tool_call_id for OpenAI native tool support
                    self._timeline.add_entry(
                        TimelineEntry(
                            entry_type=entry_type,
                            content=tool_result.get("result", "Unknown tool result"),
                            tool_call_id=tool_result.get("tool_call_id"),
                        )
                    )

        # Output parameter checking
        assert isinstance(tool_results, list)
        trace_thoughts |= {"tool_results": tool_results}

        # Call parent's base implementation (sync is fine, just data manipulation)
        result = {"trace_outputs": trace_thoughts}
        self.broadcast(result)
        return result

    # ============================================================================
    # DISCOVERY INTERFACE (Override from BaseSTARAgent)
    # ============================================================================

    @property
    def _registry_available_agents(self) -> Sequence[AgentProtocol]:
        """List available agents (excluding self)."""
        if self._registry:
            all_agents = self._registry.list_agents()
            # Exclude self
            return [agent for agent in all_agents if agent.object_id != self.object_id]
        else:
            return []
