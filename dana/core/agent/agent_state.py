"""
Agent state management.

This module defines the AgentState class that holds all key information
an agent needs to make decisions and take actions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .capabilities import CapabilityRegistry
from .context import ExecutionContext, ProblemContext
from .mind import AgentMind
from .timeline import Timeline


@dataclass
class AgentState:
    """Central state hub that coordinates all agent subsystems.

    This class serves as the single source of truth for all agent state,
    orchestrating:
    - Problem context and task management
    - Complete cognitive system (memory, learning, understanding) via AgentMind
    - Event timeline and audit trail
    - Execution state and resource management
    - Capability registry for available actions
    """

    # Core Components
    problem_context: ProblemContext | None = None
    """Current problem/task context."""

    mind: AgentMind = field(default_factory=lambda: AgentMind())
    """Complete cognitive system including all memory types."""

    timeline: Timeline = field(default_factory=Timeline)
    """Event timeline and audit trail."""

    execution: ExecutionContext = field(default_factory=ExecutionContext)
    """Runtime execution state and resource management."""

    capabilities: CapabilityRegistry = field(default_factory=CapabilityRegistry)
    """Registry of available tools, strategies, and skills."""

    # Metadata
    session_id: str | None = None
    """Current session identifier."""
    created_at: datetime = field(default_factory=datetime.now)
    """When this state was created."""
    last_updated: datetime = field(default_factory=datetime.now)
    """When this state was last updated."""

    def update_timestamp(self) -> None:
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now()

    def get_llm_context(self, depth: str = "standard") -> dict[str, Any]:
        """Build optimal context for LLM based on current state.

        Args:
            depth: Context depth ("minimal", "standard", "comprehensive")

        Returns:
            Dictionary with all context needed for LLM
        """
        context = {}

        # Problem context
        if self.problem_context:
            context.update(
                {
                    "query": self.problem_context.problem_statement,
                    "problem_statement": self.problem_context.problem_statement,
                    "objective": self.problem_context.objective if hasattr(self.problem_context, "objective") else None,
                    "constraints": getattr(self.problem_context, "constraints", {}),
                    "assumptions": getattr(self.problem_context, "assumptions", []),
                    "depth": getattr(self.problem_context, "depth", 0),
                }
            )

        # Memory context from mind
        if self.mind:
            # Conversation memory
            if depth != "minimal":
                n_turns = {"minimal": 1, "standard": 3, "comprehensive": 10}.get(depth, 3)
                context["conversation_history"] = self.mind.recall_conversation(n_turns)

            # Relevant memories
            if self.problem_context:
                context["relevant_memory"] = self.mind.recall_relevant(self.problem_context)

            # User context
            context["user_context"] = self.mind.get_user_context()

            # Assess what's important for current context
            priorities = self.mind.assess_context_needs(self.problem_context, depth)
            context["context_priorities"] = priorities

        # Timeline context
        if self.timeline and depth != "minimal":
            n_events = {"standard": 5, "comprehensive": 20}.get(depth, 5)
            if hasattr(self.timeline, "get_recent_events"):
                context["recent_events"] = self.timeline.get_recent_events(n_events)
            else:
                # Fallback to timeline events
                context["recent_events"] = self.timeline.events[-n_events:] if self.timeline.events else []

        # Capabilities context
        if self.capabilities:
            context["available_strategies"] = self.capabilities.get_available_strategies()
            context["available_tools"] = self.capabilities.get_available_tools()
            context["available_actions"] = self.capabilities.get_available_actions()

        # Execution context
        if self.execution:
            context["execution_state"] = {
                "workflow_id": self.execution.workflow_id,
                "recursion_depth": self.execution.recursion_depth,
                "can_proceed": self.execution.can_proceed(),
                "constraints": self.execution.get_constraints(),
            }

        return context

    def discover_resources_for_ctxeng(self) -> dict[str, Any]:
        """Discover all resources for ContextEngine integration.

        Returns:
            Dictionary of resource name to resource object
        """
        resources = {}

        # Core resources
        if self.timeline:
            resources["event_history"] = self.timeline
            resources["timeline"] = self.timeline

        if self.problem_context:
            resources["problem_context"] = self.problem_context

        if self.capabilities:
            resources["workflow_registry"] = self.capabilities
            resources["capabilities"] = self.capabilities

        # Mind resources
        if self.mind:
            resources["memory"] = self.mind.memory
            if self.mind.user_profile:
                resources["user_model"] = self.mind.user_profile
            resources["world_model"] = self.mind.world_model

        # Execution resources
        if self.execution:
            resources["execution_context"] = self.execution

        return resources

    def assemble_context_data(self, query: str, template: str = "general") -> Any:
        """Assemble structured ContextData from agent state.

        This method creates a comprehensive ContextData object by extracting
        relevant information from all agent state components.

        Args:
            query: The query string
            template: Template name to use

        Returns:
            ContextData populated with agent state information
        """
        from dana.frameworks.ctxeng import (
            ContextData,
            ConversationContextData,
            ExecutionContextData,
            MemoryContextData,
            ProblemContextData,
            ResourceContextData,
        )

        # Create base context data
        context_data = ContextData.create_for_agent(query=query, template=template)

        # Extract problem context
        if self.problem_context:
            context_data.problem = ProblemContextData(
                problem_statement=self.problem_context.problem_statement,
                objective=self.problem_context.objective,
                original_problem=self.problem_context.original_problem,
                depth=self.problem_context.depth,
                constraints=self.problem_context.constraints,
                assumptions=self.problem_context.assumptions,
            )

        # Extract conversation context
        if self.mind and self.mind.memory:
            conversation_history = self.mind.recall_conversation(3)
            # Ensure conversation_history is a string
            if isinstance(conversation_history, list):
                conversation_history = "\n".join(str(item) for item in conversation_history)
            elif not isinstance(conversation_history, str):
                conversation_history = str(conversation_history)

            context_data.conversation = ConversationContextData(
                conversation_history=conversation_history,
                recent_events=self._get_recent_events(),
                user_preferences=self.mind.get_user_context(),
                context_depth="standard",
            )

        # Extract memory context
        if self.mind:
            relevant_memories = self.mind.recall_relevant(self.problem_context) if self.problem_context else []
            # Ensure relevant_memories is a list of strings
            if not isinstance(relevant_memories, list):
                relevant_memories = [str(relevant_memories)] if relevant_memories else []
            else:
                relevant_memories = [str(memory) for memory in relevant_memories]

            context_priorities = self.mind.assess_context_needs(self.problem_context, "standard") if self.problem_context else []
            # Ensure context_priorities is a list of strings
            if not isinstance(context_priorities, list):
                context_priorities = [str(context_priorities)] if context_priorities else []
            else:
                context_priorities = [str(priority) for priority in context_priorities]

            context_data.memory = MemoryContextData(
                relevant_memories=relevant_memories,
                user_model=self.mind.get_user_context(),
                world_model=self.mind.world_model.to_dict() if self.mind.world_model else {},
                context_priorities=context_priorities,
            )

        # Extract execution context
        if self.execution:
            context_data.execution = ExecutionContextData(
                session_id=self.session_id,
                execution_constraints=self.execution.get_constraints(),
                environment_info={},
            )

        # Extract resource context
        if self.capabilities:
            context_data.resources = ResourceContextData(
                available_resources=list(self.capabilities.get_available_tools().keys()),
                resource_limits=self.execution.resource_limits.to_dict() if self.execution else {},
                resource_usage=self.execution.current_metrics.to_dict() if self.execution else {},
                resource_errors=[],
            )

        return context_data

    def _get_recent_events(self) -> list[str]:
        """Get recent events from timeline for context."""
        if not self.timeline or not self.timeline.events:
            return []

        try:
            events = self.timeline.events[-5:]  # Last 5 events
            return [f"{e.event_type}: {e.data.get('description', 'No description')}" for e in events]
        except Exception:
            return []

    def set_problem_context(self, problem: ProblemContext) -> None:
        """Set the current problem context.

        Args:
            problem: The problem context to set
        """
        self.problem_context = problem
        if self.execution and hasattr(problem, "depth"):
            self.execution.recursion_depth = problem.depth
        self.update_timestamp()

    def start_new_conversation_turn(self, user_request: str) -> None:
        """Start a new conversation turn.

        Args:
            user_request: The user's request
        """
        # Add conversation turn via mind's memory system
        if self.mind and self.mind.memory and self.mind.memory.conversation:
            self.mind.memory.conversation.add_turn("user", user_request)
        self.update_timestamp()

    def get_state_summary(self) -> dict[str, Any]:
        """Get a summary of the current agent state.

        Returns:
            Dictionary containing key state information
        """
        return {
            "session_id": self.session_id,
            "problem_statement": self.problem_context.problem_statement if self.problem_context else None,
            "workflow_id": self.execution.workflow_id if self.execution else None,
            "recursion_depth": self.execution.recursion_depth if self.execution else 0,
            "timeline_events_count": len(self.timeline.events) if self.timeline else 0,
            "can_proceed": self.execution.can_proceed() if self.execution else True,
            "available_strategies": len(self.capabilities.get_available_strategies()) if self.capabilities else 0,
            "available_tools": len(self.capabilities.get_available_tools()) if self.capabilities else 0,
            "memory_status": self.mind.memory.get_status() if self.mind and self.mind.memory else {},
            "last_updated": self.last_updated.isoformat(),
        }
