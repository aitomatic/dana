"""
Agent Instance System

This module defines the AgentInstance class which extends StructInstance to provide
agent-specific state and methods. This is the main implementation file for agent instances.
"""

from pathlib import Path
from typing import Any

from dana.common.types import BaseRequest
from dana.core.builtins.struct_system import StructInstance
from dana.frameworks.corral import CORRALEngineer
from dana.frameworks.prteng import PromptEngineer
from dana.frameworks.ctxeng import ContextEngineer

# Removed direct import of LegacyLLMResource - now using resource type system
from dana.core.concurrency.promise_factory import PromiseFactory
from dana.core.lang.sandbox_context import SandboxContext

from .agent_state import AgentState
from .agent_type import AgentType
from .methods import (
    ChatMixin,
    ConverseMixin,
    InputMixin,
    LLMMixin,
    LoggingMixin,
    MemoryMixin,
    ReasonMixin,
)
from .utils import AgentCallbackMixin

from .solvers import (
    PlannerExecutorSolver,
    ReactiveSupportSolver,
    SimpleHelpfulSolver,
)

from dana.core.workflow.workflow_system import WorkflowInstance

from .context import ProblemContext

from .methods.converse import IOAdapter, CLIAdapter


class AgentInstance(
    StructInstance,
    AgentCallbackMixin,
    ChatMixin,
    InputMixin,
    LLMMixin,
    LoggingMixin,
    MemoryMixin,
    ReasonMixin,
    ConverseMixin,
):
    """Agent struct instance with built-in agent capabilities.

    Inherits from StructInstance and adds agent-specific state and methods.
    """

    # ============================================================================
    # CONSTRUCTOR AND INITIALIZATION
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

        # Initialize centralized agent state
        self.state = AgentState(session_id=f"agent_{id(self)}")

        # Legacy attributes now delegate to centralized state
        # These properties provide backward compatibility while using the new state system
        self._llm_resource = None  # Lazy initialization
        self._context_manager_initialized = False  # Track if context manager has been used

        # Timeline is now part of centralized state
        self._timeline = self.state.timeline

        # Initialize engineering resources (lazy initialization)
        self._context_engineer = None
        self._corral_engineer = None
        self._prompt_engineer = None

        # Initialize solvers
        self._planner_executor_solver = None
        self._reactive_support_solver = None
        self._simple_helpful_solver = None

        # Initialize TUI metrics
        self._metrics = {
            "is_running": False,
            "current_step": "initialized",
            "total_steps": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "conversation_turns": 0,
            "memory_usage": 0,
            "last_updated": None,
        }

        # Call parent constructor
        super().__init__(struct_type, values)

    def __post_init__(self):
        """Post-initialization setup."""
        # Initialize agent resources
        self._initialize_agent_resources()

    # ============================================================================
    # CORE PROPERTIES
    # ============================================================================

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self.agent_type.name

    @property
    def agent_type(self) -> AgentType:
        """Get the agent type."""
        return self._type

    @property
    def _memory(self):
        """Get the agent's memory system (backward compatibility)."""
        return self.state.mind.memory if self.state.mind else None

    @_memory.setter
    def _memory(self, value) -> None:
        """Set the agent's memory system (backward compatibility)."""
        if self.state.mind:
            self.state.mind.memory = value

    # ============================================================================
    # RESOURCE MANAGEMENT
    # ============================================================================

    @property
    def llm_resource(self):
        """Get the LLM resource for this agent."""
        if self._llm_resource is None:
            self._llm_resource = self._get_llm_resource()
        return self._llm_resource

    @property
    def prompt_engineer(self):
        """Get the prompt engineer for this agent."""
        if self._prompt_engineer is None:
            from dana.frameworks.prteng import PromptEngineer
            self._prompt_engineer = PromptEngineer(llm_resource=self._llm_resource)
        return self._prompt_engineer

    @property
    def context_engineer(self):
        """Get the context engineer for this agent."""
        if self._context_engineer is None:
            from dana.frameworks.ctxeng import ContextEngineer
            self._context_engineer = ContextEngineer.from_agent(self)
        return self._context_engineer

    def _get_llm_resource(self, sandbox_context: SandboxContext | None = None):
        """Get the LLM resource for this agent.

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
        if self._llm_resource is None:
            self._initialize_llm_resource()
        return self._llm_resource

    def _initialize_llm_resource(self):
        """Initialize LLM resource from agent's config if not already done."""
        if self._llm_resource is None:
            # Check if we're in a test environment by looking for DANA_MOCK_LLM
            import os

            if os.getenv("DANA_MOCK_LLM", "false").lower() == "true":
                # Create a mock LLM resource for testing
                from tests.conftest import create_mock_llm_resource

                self._llm_resource = create_mock_llm_resource()
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
            self._llm_resource = LLMResourceType.create_instance_from_values(
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
            self._llm_resource.initialize()
            self._llm_resource.start()

    def _initialize_agent_resources(self):
        """Initialize all agent resources."""
        # Initialize LLM resource
        self._initialize_llm_resource()

        # Initialize solvers
        self._initialize_solvers()

        # Initializing engineering resources
        self._corral_engineer = CORRALEngineer()
        self._prompt_engineer = PromptEngineer()
        self._context_engineer = ContextEngineer()

        # Update metrics to indicate agent is ready
        self.update_metric("is_running", False)
        self.update_metric("current_step", "initialized")

    def _initialize_solvers(self):
        """Initialize all available solvers."""
        print(f"Initializing solvers for {self.name}")
        self._planner_executor_solver = PlannerExecutorSolver(self)
        self._reactive_support_solver = ReactiveSupportSolver(self)
        self._simple_helpful_solver = SimpleHelpfulSolver(self)
        print(f"Solvers initialized for {self.name}")

    def _cleanup_agent_resources(self):
        """Clean up all agent resources."""
        # Clean up LLM resource
        if self._llm_resource is not None:
            try:
                if hasattr(self._llm_resource, "stop"):
                    self._llm_resource.stop()
            except Exception as e:
                print(f"Warning: Error stopping LLM resource: {e}")

            try:
                if hasattr(self._llm_resource, "cleanup"):
                    self._llm_resource.cleanup()
            except Exception as e:
                print(f"Warning: Error cleaning up LLM resource: {e}")

            try:
                self._llm_resource = None
            except Exception as e:
                print(f"Warning: Error setting LLM resource to None: {e}")

        # Clean up engineering resources
        self._context_engineer = None
        self._corral_engineer = None
        self._prompt_engineer = None

        # Clean up solvers
        self._planner_executor_solver = None
        self._reactive_support_solver = None
        self._simple_helpful_solver = None

        # Clear conversation memory
        self.clear_conversation_memory()

        # Update metrics
        self.update_metric("is_running", False)
        self.update_metric("current_step", "cleaned_up")

    # ============================================================================
    # CORE AGENT OPERATIONS
    # ============================================================================

    def llm(self, request: str | dict | BaseRequest, sandbox_context: SandboxContext | None = None, **kwargs) -> Any:
        """Call the LLM with a request."""
        return super().llm(request, sandbox_context, **kwargs)

    def converse(self, io: IOAdapter = CLIAdapter(), sandbox_context: SandboxContext | None = None) -> Any:
        """Start a conversation loop with the agent."""
        return super().converse(io, sandbox_context)

    def plan(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs,
    ) -> WorkflowInstance:
        """Plan a solution for the given problem."""
        return super().plan(problem_or_workflow, artifacts, sandbox_context, **kwargs)

    def solve(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs,
    ) -> Any:
        """Solve a problem or execute a workflow."""
        return super().solve(problem_or_workflow, artifacts, sandbox_context, **kwargs)

    def solve_sync(self, problem_or_workflow: str | WorkflowInstance, artifacts: dict[str, Any] | None = None, sandbox_context: SandboxContext | None = None, **kwargs) -> Any:
        """Synchronous solve method."""
        return super().solve_sync(problem_or_workflow, artifacts, sandbox_context, **kwargs)

    def chat(
        self,
        message: str,
        sandbox_context: SandboxContext | None = None,
        **kwargs,
    ) -> str:
        """Chat with the agent."""
        return super().chat(message, sandbox_context, **kwargs)

    def input(self, request: str, sandbox_context: SandboxContext | None = None, problem_context: ProblemContext | None = None) -> Any:
        """Process input from the user."""
        return super().input(request, sandbox_context, problem_context)

    def answer(self, answer: str, sandbox_context: SandboxContext | None = None):
        """Provide an answer to the user."""
        return super().answer(answer, sandbox_context)

    def reason(
        self,
        premise: str,
        options: list[str] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs,
    ) -> Any:
        """Reason about a premise with optional options."""
        return super().reason(premise, options, sandbox_context, **kwargs)

    # ============================================================================
    # MEMORY AND PERSISTENCE
    # ============================================================================

    def remember(self, key: str, value: Any, sandbox_context: SandboxContext | None = None) -> Any:
        """Remember a key-value pair."""
        return super().remember(key, value, sandbox_context)

    def recall(self, key: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Recall a value by key."""
        return super().recall(key, sandbox_context)

    def clear_conversation_memory(self) -> bool:
        """Clear the conversation memory."""
        try:
            # Clear the timeline
            if self.state.timeline:
                self.state.timeline.clear_events()

            # Clear other memory components
            if self.state.mind and self.state.mind.memory:
                self.state.mind.memory.clear()

            # Update metrics
            self.update_metric("conversation_turns", 0)
            self.update_metric("memory_usage", 0)

            return True
        except Exception as e:
            print(f"Error clearing conversation memory: {e}")
            return False

    def get_conversation_stats(self) -> dict:
        """Get conversation statistics."""
        stats = {
            "total_turns": 0,
            "user_messages": 0,
            "agent_responses": 0,
            "conversation_duration": 0,
            "average_response_time": 0,
            "memory_usage": 0,
        }

        try:
            if self.state.timeline:
                events = self.state.timeline.get_events()
                conversation_events = [e for e in events if e.event_type == "conversation_turn"]

                stats["total_turns"] = len(conversation_events)
                stats["user_messages"] = len([e for e in conversation_events if hasattr(e, "user_input")])
                stats["agent_responses"] = len([e for e in conversation_events if hasattr(e, "agent_response")])

                if conversation_events:
                    first_event = conversation_events[0]
                    last_event = conversation_events[-1]
                    duration = (last_event.timestamp - first_event.timestamp).total_seconds()
                    stats["conversation_duration"] = duration
                    stats["average_response_time"] = duration / len(conversation_events) if conversation_events else 0

            # Get memory usage from state
            if self.state.mind and self.state.mind.memory:
                memory_status = self.state.mind.memory.get_status()
                stats["memory_usage"] = memory_status.get("total_items", 0)

        except Exception as e:
            print(f"Error getting conversation stats: {e}")

        return stats

    def get_agent_id(self) -> str:
        """Get a unique identifier for this agent instance."""
        agent_name = self.name if hasattr(self, "name") else "unnamed_agent"
        safe_name = "".join(c for c in agent_name if c.isalnum() or c in ("-", "_")).rstrip()
        # Use a more stable ID based on agent type and name rather than object ID
        return f"{safe_name}_{hash(str(self.agent_type))}"

    def get_agent_base_path(self) -> Path:
        """Get the base path for this agent's persistence."""
        return Path(f"~/.dana/agents/{self.get_agent_id()}").expanduser()

    def enable_persistence(self, base_path: str | None = None) -> None:
        """Enable persistence for this agent."""
        if base_path:
            agent_path = Path(base_path)
        else:
            agent_path = self.get_agent_base_path()

        # Enable persistence in the centralized state
        self.state.enable_persistence(agent_path)

    def save_agent_metadata(self, agent_path: Path | None = None) -> None:
        """Save agent metadata to disk."""
        if agent_path is None:
            agent_path = self.get_agent_base_path()

        metadata = {
            "agent_type": self.agent_type.name,
            "agent_id": self.get_agent_id(),
            "created_at": self._metrics.get("created_at"),
            "last_updated": self._metrics.get("last_updated"),
            "version": "1.0",
        }

        metadata_path = agent_path / "metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def save_session(self, session_name: str) -> None:
        """Save the current session state."""
        try:
            agent_path = self.get_agent_base_path()
            sessions_path = agent_path / "sessions"
            sessions_path.mkdir(parents=True, exist_ok=True)

            session_data = {
                "session_name": session_name,
                "timestamp": self._metrics.get("last_updated"),
                "conversation_stats": self.get_conversation_stats(),
                "agent_state": self.state.get_state_summary(),
            }

            session_file = sessions_path / f"{session_name}.json"
            import json
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)

            print(f"Session '{session_name}' saved successfully")

        except Exception as e:
            print(f"Error saving session: {e}")

    def list_sessions(self) -> list[str]:
        """List all saved sessions."""
        try:
            agent_path = self.get_agent_base_path()
            sessions_path = agent_path / "sessions"

            if not sessions_path.exists():
                return []

            sessions = []
            for session_file in sessions_path.glob("*.json"):
                sessions.append(session_file.stem)

            return sorted(sessions)

        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []

    def restore_session(self, session_name: str) -> bool:
        """Restore a saved session."""
        try:
            agent_path = self.get_agent_base_path()
            sessions_path = agent_path / "sessions"
            session_file = sessions_path / f"{session_name}.json"

            if not session_file.exists():
                print(f"Session '{session_name}' not found")
                return False

            import json
            with open(session_file, "r") as f:
                session_data = json.load(f)

            # Restore conversation stats
            stats = session_data.get("conversation_stats", {})
            self.update_metric("conversation_turns", stats.get("total_turns", 0))
            self.update_metric("memory_usage", stats.get("memory_usage", 0))

            print(f"Session '{session_name}' restored successfully")
            return True

        except Exception as e:
            print(f"Error restoring session: {e}")
            return False

    # ============================================================================
    # SOLVER MANAGEMENT
    # ============================================================================

    def enable_planner_executor_solver(
        self,
        workflow_catalog: Any | None = None,
        resource_index: Any | None = None,
        **kwargs,
    ) -> "AgentInstance":
        """Enable the planner-executor solver with optional dependencies."""
        if self._planner_executor_solver is None:
            self._planner_executor_solver = PlannerExecutorSolver(self)

        # Set dependencies if provided
        if workflow_catalog is not None:
            self._planner_executor_solver.workflow_catalog = workflow_catalog
        if resource_index is not None:
            self._planner_executor_solver.resource_index = resource_index

        # Set as the primary solver
        self._primary_solver = self._planner_executor_solver

        return self

    def enable_reactive_support_solver(
        self,
        signature_matcher: Any | None = None,
        workflow_catalog: Any | None = None,
        resource_index: Any | None = None,
        **kwargs,
    ) -> "AgentInstance":
        """Enable the reactive support solver with optional dependencies."""
        if self._reactive_support_solver is None:
            self._reactive_support_solver = ReactiveSupportSolver(self)

        # Set dependencies if provided
        if signature_matcher is not None:
            self._reactive_support_solver.signature_matcher = signature_matcher
        if workflow_catalog is not None:
            self._reactive_support_solver.workflow_catalog = workflow_catalog
        if resource_index is not None:
            self._reactive_support_solver.resource_index = resource_index

        # Set as the primary solver
        self._primary_solver = self._reactive_support_solver

        return self

    # ============================================================================
    # LOGGING AND METRICS
    # ============================================================================

    def log(self, message: str, level: str = "INFO", sandbox_context: SandboxContext | None = None) -> Any:
        """Log a message."""
        return super().log(message, level, sandbox_context)

    def info(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Log an info message."""
        return super().info(message, sandbox_context)

    def warning(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Log a warning message."""
        return super().warning(message, sandbox_context)

    def debug(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Log a debug message."""
        return super().debug(message, sandbox_context)

    def error(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Log an error message."""
        return super().error(message, sandbox_context)

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics."""
        # Update last_updated timestamp
        from datetime import datetime
        self._metrics["last_updated"] = datetime.now().isoformat()

        # Get conversation stats
        conversation_stats = self.get_conversation_stats()
        self._metrics.update(conversation_stats)

        return self._metrics.copy()

    def update_metric(self, key: str, value: Any) -> None:
        """Update a metric value."""
        self._metrics[key] = value

    # ============================================================================
    # CONTEXT MANAGEMENT
    # ============================================================================

    def _create_sandbox_context(self) -> SandboxContext:
        """Create a sandbox context for this agent."""
        context = SandboxContext()
        if self._llm_resource is not None:
            context.set_system_llm_resource(self._llm_resource)
        return context

    # ============================================================================
    # CONTEXT MANAGER SUPPORT
    # ============================================================================

    def __enter__(self):
        """Enter the agent context manager."""
        if not self._context_manager_initialized:
            self._initialize_agent_resources()
            self._context_manager_initialized = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the agent context manager."""
        try:
            self._cleanup_agent_resources()
        except Exception as e:
            print(f"Warning: Error during agent cleanup: {e}")

    # ============================================================================
    # STATIC METHODS AND CLASS METHODS
    # ============================================================================

    @staticmethod
    def get_default_dana_methods() -> dict[str, Any]:
        """Get default Dana methods for agents."""
        return {
            "llm": lambda self, request, **kwargs: self.llm(request, **kwargs),
            "converse": lambda self, io=None, **kwargs: self.converse(io, **kwargs),
            "plan": lambda self, problem, **kwargs: self.plan(problem, **kwargs),
            "solve": lambda self, problem, **kwargs: self.solve(problem, **kwargs),
            "chat": lambda self, message, **kwargs: self.chat(message, **kwargs),
            "input": lambda self, request, **kwargs: self.input(request, **kwargs),
            "answer": lambda self, answer, **kwargs: self.answer(answer, **kwargs),
            "remember": lambda self, key, value, **kwargs: self.remember(key, value, **kwargs),
            "recall": lambda self, key, **kwargs: self.recall(key, **kwargs),
            "reason": lambda self, premise, **kwargs: self.reason(premise, **kwargs),
            "log": lambda self, message, **kwargs: self.log(message, **kwargs),
            "info": lambda self, message, **kwargs: self.info(message, **kwargs),
            "warning": lambda self, message, **kwargs: self.warning(message, **kwargs),
            "debug": lambda self, message, **kwargs: self.debug(message, **kwargs),
            "error": lambda self, message, **kwargs: self.error(message, **kwargs),
        }

    @staticmethod
    def get_default_agent_fields() -> dict[str, str | dict[str, Any]]:
        """Get default fields for agent struct types."""
        return {
            "name": "str",
            "description": "str",
            "config": {
                "type": "dict",
                "default": {},
                "description": "Agent configuration including LLM settings",
            },
            "capabilities": {
                "type": "list",
                "default": [],
                "description": "List of agent capabilities",
            },
            "memory_config": {
                "type": "dict",
                "default": {},
                "description": "Memory system configuration",
            },
        }
