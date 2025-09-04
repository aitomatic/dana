"""
Agent Instance System

This module defines the AgentInstance class which extends StructInstance to provide
agent-specific state and methods. This is the main implementation file for agent instances.
"""

from typing import TYPE_CHECKING, Any

from dana.common.types import BaseRequest
from dana.core.builtins.struct_system import StructInstance

# Removed direct import of LegacyLLMResource - now using resource type system
from dana.core.concurrency.promise_factory import PromiseFactory
from dana.core.lang.sandbox_context import SandboxContext

from .agent_type import AgentType
from .events import AgentEventMixin
from .methods import (
    ChatMixin,
    InputMixin,
    LLMMixin,
    LoggingMixin,
    MemoryMixin,
    ReasonMixin,
    SolvingMixin,
)

if TYPE_CHECKING:
    pass

from dana.core.workflow.workflow_system import WorkflowInstance, WorkflowType

from .context import ProblemContext


class AgentInstance(
    StructInstance,
    AgentEventMixin,
    ChatMixin,
    InputMixin,
    LLMMixin,
    LoggingMixin,
    MemoryMixin,
    ReasonMixin,
    SolvingMixin,
):
    """Agent struct instance with built-in agent capabilities.

    Inherits from StructInstance and adds agent-specific state and methods.
    """

    # ============================================================================
    # CONSTRUCTOR AND CORE PROPERTIES
    # ============================================================================

    def __init__(self, struct_type: AgentType, values: dict[str, Any]):
        """Create a new agent struct instance.

        Args:
            struct_type: The agent struct type definition
            values: Field values (must match struct type requirements)
        """
        # Ensure we have an AgentStructType
        if not isinstance(struct_type, AgentType):
            raise TypeError(f"AgentStructInstance requires AgentStructType, got {type(struct_type)}")

        # Initialize agent-specific state
        self._memory = {}
        self._context = {}
        self._conversation_memory = None  # Lazy initialization
        self._llm_resource = None  # Lazy initialization - now handled by resource type system
        self._llm_resource_instance = None  # Lazy initialization

        # Initialize persistent event history for conversation continuity
        from .context import EventHistory

        self._global_event_history = EventHistory()

        # Initialize context engine (lazy initialization)
        self._context_engine = None

        # Initialize TUI metrics
        self._metrics = {
            "is_running": False,
            "current_step": "idle",
            "elapsed_time": 0.0,
            "tokens_per_sec": 0.0,
        }

        # Initialize the base StructInstance
        from dana.registry import AGENT_REGISTRY

        super().__init__(struct_type, values, AGENT_REGISTRY)
        AgentEventMixin.__init__(self)

    @property
    def name(self) -> str:
        """Get the agent's name for TUI compatibility."""
        # Return the instance name field value, not the struct type name
        return self._values.get("name", "unnamed_agent")

    @property
    def agent_type(self) -> AgentType:
        """Get the agent type."""
        return self.__struct_type__  # type: ignore

    # ============================================================================
    # STATIC/CLASS METHODS
    # ============================================================================

    @staticmethod
    def get_default_dana_methods() -> dict[str, Any]:
        """Get the default agent methods that all agents should have.

        This method defines what the standard agent methods are,
        keeping the definition close to where they're implemented.
        """

        return {
            "llm": AgentInstance.llm,
            "plan": AgentInstance.plan,
            "solve": AgentInstance.solve,
            "remember": AgentInstance.remember,
            "recall": AgentInstance.recall,
            "reason": AgentInstance.reason,
            "chat": AgentInstance.chat,
            "log": AgentInstance.log,
            "info": AgentInstance.info,
            "warning": AgentInstance.warning,
            "debug": AgentInstance.debug,
            "error": AgentInstance.error,
            "input": AgentInstance.input,
        }

    @staticmethod
    def get_default_agent_fields() -> dict[str, str | dict[str, Any]]:
        """Get the default fields that all agents should have.

        This method defines what the standard agent fields are,
        keeping the definition close to where they're used.
        """
        return {
            "state": {
                "type": "str",
                "default": "CREATED",
                "comment": "Current state of the agent",
            }
        }

    # ============================================================================
    # CORE AGENT METHODS (Main Public Interface)
    # ============================================================================

    def llm(self, request: str | dict | BaseRequest, sandbox_context: SandboxContext | None = None, **kwargs) -> Any:
        """Asynchronous agent LLM method."""
        return PromiseFactory.create_promise(computation=lambda: self.llm_sync(request, sandbox_context, **kwargs))

    def plan(self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext | None = None, **kwargs) -> Any:
        """Asynchronous agent plan method."""
        return PromiseFactory.create_promise(computation=lambda: self.plan_sync(problem_or_workflow, sandbox_context, **kwargs))

    def solve(self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext | None = None, **kwargs) -> Any:
        """Asynchronous agent solve method."""
        return PromiseFactory.create_promise(computation=lambda: self.solve_sync(problem_or_workflow, sandbox_context, **kwargs))

    # ============================================================================
    # PROBLEM SOLVING METHODS (Workflow Creation and Management)
    # ============================================================================

    def _create_top_level_workflow(self, problem: str, **kwargs) -> WorkflowInstance:
        """Create a new top-level workflow for a problem."""

        # Create problem context with conversation context
        conversation_context = self._global_event_history.get_conversation_context()
        problem_context = ProblemContext(
            problem_statement=problem, objective=kwargs.get("objective", f"Solve: {problem}"), original_problem=problem, depth=0
        )

        # Add conversation history to constraints if available
        if conversation_context:
            problem_context.constraints["conversation_history"] = conversation_context

        # Create workflow instance using the persistent event history
        workflow = WorkflowInstance(
            struct_type=self._create_workflow_type(problem),
            values={
                "problem_statement": problem,
                "objective": problem_context.objective,
                "problem_context": problem_context,
                "action_history": self._global_event_history,
            },
            parent_workflow=None,
        )

        return workflow

    def _create_new_workflow(self, problem: str, sandbox_context: SandboxContext | None = None, **kwargs) -> WorkflowInstance:
        """Create a new workflow for a string problem."""
        from .context import ProblemContext
        from .strategy import select_best_strategy

        print(f"[DEBUG] _create_new_workflow() called with problem: {problem}")
        print(f"[DEBUG] sandbox_context: {sandbox_context}")
        print(f"[DEBUG] kwargs: {kwargs}")

        # Create problem context with conversation context
        print("[DEBUG] Creating problem context...")
        conversation_context = self._global_event_history.get_conversation_context()
        print(f"[DEBUG] Conversation context: {conversation_context}")

        problem_context = ProblemContext(
            problem_statement=problem, objective=kwargs.get("objective", f"Solve: {problem}"), original_problem=problem, depth=0
        )
        print(f"[DEBUG] Problem context created: {problem_context}")

        # Add conversation history to constraints if available
        if conversation_context:
            print("[DEBUG] Adding conversation history to constraints")
            problem_context.constraints["conversation_history"] = conversation_context

        # Select best strategy
        print("[DEBUG] Selecting best strategy...")
        strategy = select_best_strategy(problem, problem_context)
        print(f"[DEBUG] Selected strategy: {type(strategy)}")

        # Create workflow using strategy
        print("[DEBUG] Creating workflow using strategy...")
        workflow = strategy.create_workflow(problem, problem_context, self, sandbox_context=sandbox_context)
        print(f"[DEBUG] Strategy created workflow: {type(workflow)}")

        return workflow

    def _create_workflow_type(self, problem: str) -> WorkflowType:
        """Create a workflow type for the problem."""

        return WorkflowType(
            name=f"AgentWorkflow_{hash(problem) % 10000}",
            fields={"problem_statement": "str", "objective": "str", "problem_context": "Any", "action_history": "Any"},
            field_order=["problem_statement", "objective", "problem_context", "action_history"],
            field_comments={
                "problem_statement": "The problem to solve",
                "objective": "The objective of the workflow",
                "problem_context": "Problem-specific context",
                "action_history": "Global action history",
            },
            field_defaults={
                "problem_statement": problem,
                "objective": "Solve the problem",
                "problem_context": None,
                "action_history": None,
            },
            docstring=f"Agent workflow for solving: {problem}",
        )

    def _create_sandbox_context(self) -> SandboxContext:
        """Create a sandbox context for workflow execution."""
        return SandboxContext()

    # ============================================================================
    # COMMUNICATION METHODS
    # ============================================================================

    def chat(
        self, message: str, context: dict | None = None, max_context_turns: int = 5, sandbox_context: SandboxContext | None = None
    ) -> Any:
        """Asynchronous agent chat method."""
        return PromiseFactory.create_promise(computation=lambda: self.chat_sync(message, context, max_context_turns, sandbox_context))

    def input(self, request: str, sandbox_context: SandboxContext | None = None, problem_context: ProblemContext | None = None) -> Any:
        """Asynchronous agent input method."""
        return PromiseFactory.create_promise(computation=lambda: self.input_sync(request, sandbox_context, problem_context))

    def answer(self, answer: str, sandbox_context: SandboxContext | None = None):
        """Execute agent answer method."""
        print(answer)

    # ============================================================================
    # MEMORY METHODS
    # ============================================================================

    def remember(self, key: str, value: Any, sandbox_context: SandboxContext | None = None) -> Any:
        """Asynchronous agent memory storage method."""
        return PromiseFactory.create_promise(computation=lambda: self.remember_sync(key, value, sandbox_context))

    def recall(self, key: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Asynchronous agent memory retrieval method."""
        return PromiseFactory.create_promise(computation=lambda: self.recall_sync(key, sandbox_context))

    # ============================================================================
    # REASONING METHODS
    # ============================================================================

    def reason(
        self,
        premise: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: dict | None = None,
        system_message: str | None = None,
    ) -> Any:
        """Asynchronous agent reasoning method."""
        return PromiseFactory.create_promise(
            computation=lambda: self.reason_sync(premise, sandbox_context, problem_context, system_message)
        )

    # ============================================================================
    # LOGGING METHODS
    # ============================================================================

    def log(self, message: str, level: str = "INFO", sandbox_context: SandboxContext | None = None) -> Any:
        """Asynchronous agent logging method."""
        return PromiseFactory.create_promise(computation=lambda: self.log_sync(message, level, sandbox_context))

    def info(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Asynchronous agent info logging method."""
        return PromiseFactory.create_promise(computation=lambda: self.info_sync(message, sandbox_context))

    def warning(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Asynchronous agent warning logging method."""
        return PromiseFactory.create_promise(computation=lambda: self.warning_sync(message, sandbox_context))

    def debug(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Asynchronous agent debug logging method."""
        return PromiseFactory.create_promise(computation=lambda: self.debug_sync(message, sandbox_context))

    def error(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Asynchronous agent error logging method."""
        return PromiseFactory.create_promise(computation=lambda: self.error_sync(message, sandbox_context))

    # ============================================================================
    # UTILITY METHODS (Metrics, Stats, Context Management)
    # ============================================================================

    def get_metrics(self) -> dict[str, Any]:
        """Get current agent metrics for TUI display.

        Returns:
            Dictionary containing:
            - is_running: bool - Whether agent is currently processing
            - current_step: str - Current processing step
            - elapsed_time: float - Time elapsed for current operation
            - tokens_per_sec: float - Token processing rate
        """
        return self._metrics.copy()

    def update_metric(self, key: str, value: Any) -> None:
        """Update a specific metric value.

        Args:
            key: The metric key to update
            value: The new value for the metric
        """
        if key in self._metrics:
            self._metrics[key] = value

    def get_conversation_stats(self) -> dict:
        """Get conversation statistics for this agent."""
        if self._conversation_memory is None:
            return {
                "error": "Conversation memory not initialized",
                "total_messages": 0,
                "total_turns": 0,
                "active_turns": 0,
                "summary_count": 0,
                "session_count": 0,
            }
        return self._conversation_memory.get_statistics()

    def clear_conversation_memory(self) -> bool:
        """Clear the conversation memory for this agent."""
        if self._conversation_memory is None:
            return False
        self._conversation_memory.clear()
        return True

    # ============================================================================
    # RESOURCE MANAGEMENT (LLM Resources, Initialization, Cleanup)
    # ============================================================================

    def _get_llm_resource(self):
        """Get the LLM resource for this agent.

        Returns:
            LLMResourceInstance or None if no LLM resource is available
        """
        if self._llm_resource_instance is None:
            self._initialize_llm_resource()
        return self._llm_resource_instance

    def get_llm_resource(self, sandbox_context: SandboxContext | None = None):
        """Public method to get the LLM resource for this agent.

        Args:
            sandbox_context: Optional sandbox context to get LLM resource from

        Returns:
            LLMResourceInstance or None if no LLM resource is available
        """
        # If sandbox context is provided, try to get LLM resource from there first
        if sandbox_context is not None:
            try:
                # First try to get the system LLM resource specifically
                system_llm = sandbox_context.get_system_llm_resource()
                if system_llm is not None:
                    return system_llm

                # Fall back to checking all resources for LLM kind
                resources = sandbox_context.get_resources()
                for resource in resources.values():
                    if hasattr(resource, "kind") and resource.kind == "llm":
                        return resource
            except Exception:
                pass

        # Fall back to agent's own LLM resource
        return self._get_llm_resource()

    def _initialize_conversation_memory(self):
        """Initialize conversation memory if not already done."""
        if self._conversation_memory is None:
            from pathlib import Path

            from dana.frameworks.memory.conversation_memory import ConversationMemory

            # Create memory file path under ~/.dana/chats/
            agent_name = getattr(self.agent_type, "name", "agent")
            home_dir = Path.home()
            dana_dir = home_dir / ".dana"
            memory_dir = dana_dir / "chats"
            memory_dir.mkdir(parents=True, exist_ok=True)
            memory_file = memory_dir / f"{agent_name}_conversation.json"

            self._conversation_memory = ConversationMemory(
                filepath=str(memory_file),
                max_turns=20,  # Keep last 20 turns in active memory
            )

    def _initialize_llm_resource(self):
        """Initialize LLM resource from agent's config if not already done."""
        if self._llm_resource_instance is None:
            # Check if we're in a test environment by looking for DANA_MOCK_LLM
            import os

            if os.getenv("DANA_MOCK_LLM", "false").lower() == "true":
                # Create a mock LLM resource for testing
                from tests.conftest import create_mock_llm_resource

                self._llm_resource_instance = create_mock_llm_resource()
                return

            from dana.core.resource.builtins.llm_resource_type import LLMResourceType

            # Get LLM parameters from agent's config field
            llm_params = {}
            if hasattr(self, "_values") and "config" in self._values:
                config = self._values["config"]
                if isinstance(config, dict):
                    # Extract LLM parameters from config
                    llm_params = {
                        "model": config.get("llm_model", config.get("model", "auto")),
                        "temperature": config.get("llm_temperature", config.get("temperature", 0.7)),
                        "max_tokens": config.get("llm_max_tokens", config.get("max_tokens", 2048)),
                        "provider": config.get("llm_provider", config.get("provider", "auto")),
                    }
                    # Add any other LLM-related config keys
                    for key, value in config.items():
                        if key.startswith("llm_") and key not in ["llm_model", "llm_temperature", "llm_max_tokens", "llm_provider"]:
                            llm_params[key[4:]] = value  # Remove "llm_" prefix

            # Create the LLM resource instance using the resource type system
            # This avoids direct dependency on LegacyLLMResource
            self._llm_resource_instance = LLMResourceType.create_instance_from_values(
                {
                    "name": f"{self.agent_type.name}_llm",
                    "model": llm_params.get("model", "auto"),
                    "provider": llm_params.get("provider", "auto"),
                    "temperature": llm_params.get("temperature", 0.7),
                    "max_tokens": llm_params.get("max_tokens", 2048),
                    **{k: v for k, v in llm_params.items() if k not in ["model", "temperature", "max_tokens", "provider"]},
                }
            )

            # Initialize the resource
            self._llm_resource_instance.initialize()
            self._llm_resource_instance.start()

    def _initialize_agent_resources(self):
        """Initialize all agent resources that need explicit initialization."""
        try:
            # Initialize conversation memory
            self._initialize_conversation_memory()

            # Initialize LLM resource
            self._initialize_llm_resource()

            # Update metrics to indicate agent is ready
            self.update_metric("is_running", False)
            self.update_metric("current_step", "initialized")

            # Log initialization
            self.log_sync("Agent resources initialized")

        except Exception as e:
            # Log initialization error but don't fail completely
            import logging

            logging.error(f"Failed to initialize agent resources for {self.name}: {e}")
            # Update metrics to indicate initialization failure
            self.update_metric("current_step", "initialization_failed")

    def _cleanup_agent_resources(self):
        """Cleanup all agent resources that need explicit cleanup."""
        try:
            # Stop LLM resource if it was initialized
            if self._llm_resource_instance is not None:
                try:
                    self._llm_resource_instance.stop()
                except Exception as e:
                    import logging

                    logging.warning(f"Failed to stop LLM resource for {self.name}: {e}")

                # Cleanup LLM resource
                try:
                    self._llm_resource_instance.cleanup()
                except Exception as e:
                    import logging

                    logging.warning(f"Failed to cleanup LLM resource for {self.name}: {e}")

                self._llm_resource_instance = None

            # Clear conversation memory
            if self._conversation_memory is not None:
                try:
                    self._conversation_memory.clear()
                except Exception as e:
                    import logging

                    logging.warning(f"Failed to clear conversation memory for {self.name}: {e}")

                self._conversation_memory = None

            # Clear agent memory and context
            self._memory.clear()
            self._context.clear()

            # Update metrics to indicate cleanup
            self.update_metric("is_running", False)
            self.update_metric("current_step", "cleaned_up")
            self.update_metric("elapsed_time", 0.0)
            self.update_metric("tokens_per_sec", 0.0)

            # Log cleanup
            self.log_sync("Agent resources cleaned up")

        except Exception as e:
            # Log cleanup error but don't fail completely
            import logging

            logging.error(f"Failed to cleanup agent resources for {self.name}: {e}")
            # Update metrics to indicate cleanup failure
            self.update_metric("current_step", "cleanup_failed")

    # ============================================================================
    # CONTEXT MANAGER METHODS
    # ============================================================================

    def __enter__(self):
        """Context manager entry - initialize agent resources.

        Returns:
            self: The agent instance for use in with statement
        """
        self._initialize_agent_resources()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup agent resources.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        self._cleanup_agent_resources()
        # Don't suppress exceptions - let them propagate
