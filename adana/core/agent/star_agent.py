"""
STARAgent implementation using composition-based architecture.

This is the main STARAgent implementation using composition instead of mixin inheritance.
It provides a cleaner, more maintainable architecture for the STAR (See-Think-Act-Reflect) pattern
and conversational agent functionality using composable components.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from adana.common.llm.llm import LLM
from adana.common.observable import observable
from adana.common.protocols import AgentProtocol, DictParams, ResourceProtocol, WorkflowProtocol, Notifiable
from adana.common.protocols.types import LearningPhase
from adana.core.agent.base_agent import BaseAgent
from adana.core.resource.todo_resource import ToDoResource

from .base_star_agent import BaseSTARAgent
from .components import Communicator, Learner, PromptEngineer, State, ToolCaller
from .timeline import Timeline, TimelineEntry, TimelineEntryType

from adana.apps.dana.thought_logger import ThoughtLogger


class STARAgent(BaseSTARAgent):
    """STARAgent implementation using composition-based architecture."""

    def __init__(
        self,
        agent_type: str | None = None,
        agent_id: str | None = None,
        llm_provider: str | None = None,
        model: str | None = None,
        config: dict[str, Any] | None = None,
        max_context_tokens: int = 4000,
        auto_register: bool = True,
        registry=None,
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

        # Initialize LLM
        self._llm_config = {
            "provider": llm_provider,
            "model": model,
        }

        # Initialize components with composition
        self._prompt_engineer = PromptEngineer(self)
        self._communicator = Communicator(self)
        self._state = State(self)
        self._learner = Learner(self)
        self._tool_caller = ToolCaller(self)

        # Initialize timeline at agent level
        self._timeline = Timeline(max_context_tokens=max_context_tokens)

        self.with_resources(ToDoResource(resource_id="todo-resource"))

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

    # ============================================================================
    # PUBLIC API - AGENT IDENTITY & PROMPTS
    # ============================================================================

    def with_agents(self, *agents: AgentProtocol) -> BaseSTARAgent:
        """Add agents to the agent."""
        self._prompt_engineer.reset()
        super().with_agents(*agents)
        return self

    def with_resources(self, *resources: ResourceProtocol) -> BaseSTARAgent:
        """Add resources to the agent."""
        self._prompt_engineer.reset()
        super().with_resources(*resources)
        return self

    def with_workflows(self, *workflows: WorkflowProtocol) -> BaseSTARAgent:
        """Add workflows to the agent."""
        self._prompt_engineer.reset()
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
        return self._prompt_engineer.public_description

    @property
    def private_identity(self) -> str:
        """Get the private identity of the agent."""
        return self._prompt_engineer.identity

    @property
    def system_prompt(self) -> str:
        """Get the system prompt of the agent."""
        return self._prompt_engineer.system_prompt

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

    def converse(self, initial_message: str | None = None) -> None:
        """Interactive conversation loop with a human user."""
        self._communicator.converse(initial_message=initial_message)

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
            # This is a subsequent loop
            del trace_inputs["response"]
            del trace_inputs["tool_calls"]
            del trace_inputs["tool_results"]
        else:
            # This is the first loop
            caller_message: str = trace_inputs.get("caller_message", trace_inputs.get("message", None))
            if not caller_message:
                return {"trace_percepts": self._mark_star_loop_exit(trace_inputs)}

            # Add caller_message to timeline with caller tracking
            if isinstance(caller_message, str):
                # Create new entry and mark it as latest
                new_entry = TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content=caller_message, is_latest_user_message=True)
                self._timeline.add_entry(new_entry)

            # Do not leak message/caller_message to subsequent phases and loops
            trace_inputs.pop("caller_message", None)
            trace_inputs.pop("message", None)
            # trace_inputs |= {
            #    "caller_message": caller_message,
            #    "caller_type": caller_type,
            #    "caller_id": caller_id,
            # }

        trace_inputs |= {"timeline": self._timeline}

        return super()._see(trace_inputs)

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

        # Build LLM messages using PromptEngineer
        llm_messages = self._prompt_engineer.build_llm_request(timeline)

        # Query LLM with agent information for logging
        llm_response = self.llm_client.chat_response_sync(llm_messages, agent_id=self.object_id, agent_type=self.agent_type)
        response, reasoning, tool_calls = self._tool_caller.parse_llm_response(llm_response)

        if not tool_calls or len(tool_calls) == 0:
            response = response if (response and len(response) > 0) else "No response generated"
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.MY_RESPONSE,
                    content=response,
                )
            )
        else:
            if response and len(response) > 0:
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.MY_THOUGHTS,
                        content=response,
                    )
                )

            for tool_call in tool_calls:
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.TOOL_CALL,
                        content=str(tool_call),
                    )
                )

        # Output parameter checking
        assert isinstance(response, str)
        assert isinstance(tool_calls, list)
        trace_percepts |= {
            "response": response,
            "reasoning": reasoning,
            "tool_calls": tool_calls,
        }

        if tool_calls is None or len(tool_calls) == 0:
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

        # Execute tool calls using ToolCaller
        tool_results = self._tool_caller.execute_tool_calls(tool_calls)

        # Add tool results to timeline
        if isinstance(tool_results, list):
            for tool_result in tool_results:
                if isinstance(tool_result, dict):
                    # Determine entry type based on tool type
                    tool_type = tool_result.get("type")
                    if tool_type == "agent":
                        entry_type = TimelineEntryType.AGENT_RESPONSE
                    elif tool_type == "resource":
                        entry_type = TimelineEntryType.RESOURCE_RESULT
                    elif tool_type == "workflow":
                        entry_type = TimelineEntryType.WORKFLOW_RESULT
                    else:  # unknown
                        entry_type = TimelineEntryType.UNKNOWN_TOOL_CALL

                    self._timeline.add_entry(
                        TimelineEntry(
                            entry_type=entry_type,
                            content=tool_result.get("result", "Unknown tool result"),
                        )
                    )

        # Output parameter checking
        assert isinstance(tool_results, list)
        trace_thoughts |= {"tool_results": tool_results}

        return super()._act(trace_thoughts)

    @observable
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
                entry_type=TimelineEntryType.MY_LEARNING,
                content=f"Learning ({phase.value}): {trace_learning.get('learning_note', 'No learning note')}",
            )
        )

        return super()._reflect(trace_learning)

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
