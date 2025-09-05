"""
Agent state management.

This module defines the AgentState class that holds all key information
an agent needs to make decisions and take actions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .context import ProblemContext, ExecutionContext
from .timeline import Timeline
from .mind import AgentMind
from .capabilities import CapabilityRegistry


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
