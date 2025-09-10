"""
Agent Instance System

This module defines the AgentInstance class which extends StructInstance to provide
agent-specific state and methods. This is the main implementation file for agent instances.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

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
    BaseSolverMixin,
    SimpleHelpfulSolverMixin,
    PlannerExecutorSolverMixin,
    ReactiveSupportSolverMixin,
)
from .utils import AgentCallbackMixin

if TYPE_CHECKING:
    pass

from dana.core.workflow.workflow_system import WorkflowInstance

from .context import ProblemContext


class AgentInstance(
    StructInstance,
    AgentCallbackMixin,
    ChatMixin,
    ConverseMixin,
    InputMixin,
    LLMMixin,
    LoggingMixin,
    MemoryMixin,
    ReasonMixin,
    PlannerExecutorSolverMixin,
    # ReactiveSupportSolverMixin,
    # SimpleHelpfulSolverMixin,
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

        # Initialize centralized agent state
        self.state = AgentState(session_id=f"agent_{id(self)}")

        # Legacy attributes now delegate to centralized state
        # These properties provide backward compatibility while using the new state system
        self._llm_resource = None  # Lazy initialization

        # Timeline is now part of centralized state
        self._timeline = self.state.timeline

        # Initialize engineering resources (lazy initialization)
        self._context_engineer = None
        self._corral_engineer = None
        self._prompt_engineer = None

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
        AgentCallbackMixin.__init__(self)
        PlannerExecutorSolverMixin.__init__(self)
        # ReactiveSupportSolverMixin.__init__(self)
        # SimpleHelpfulSolverMixin.__init__(self)

    def __post_init__(self):
        """Post-initialize the agent instance."""
        if isinstance(self, PlannerExecutorSolverMixin):
            PlannerExecutorSolverMixin.__init__(self)

        if isinstance(self, ReactiveSupportSolverMixin):
            ReactiveSupportSolverMixin.__init__(self)

        if isinstance(self, SimpleHelpfulSolverMixin):
            SimpleHelpfulSolverMixin.__init__(self)

        super().__post_init__()

    @property
    def name(self) -> str:
        """Get the agent's name for TUI compatibility."""
        # Return the instance name field value, not the struct type name
        return self._values.get("name", "unnamed_agent")

    @property
    def agent_type(self) -> AgentType:
        """Get the agent type."""
        return self.__struct_type__  # type: ignore

    @property
    def _memory(self):
        """Legacy memory access - delegates to centralized working memory object."""
        return self.state.mind.memory.working

    @_memory.setter
    def _memory(self, value) -> None:
        """Legacy memory setter - not supported, use centralized state directly."""
        raise NotImplementedError("Use self.state.mind.memory.working directly instead of setting _memory")

    @property
    def _conversation_memory(self):
        """Legacy conversation memory access - now delegates to enhanced timeline."""
        return self.state.timeline

    @_conversation_memory.setter
    def _conversation_memory(self, value) -> None:
        """Legacy conversation memory setter - not supported, use enhanced timeline directly."""
        raise NotImplementedError("Use self.state.timeline directly instead of setting _conversation_memory")

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

    def plan(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs,
    ) -> Any:
        """Asynchronous agent plan method."""
        return PromiseFactory.create_promise(computation=lambda: self.plan_sync(problem_or_workflow, artifacts, sandbox_context, **kwargs))

    def solve(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs,
    ) -> Any:
        """Asynchronous agent solve method."""
        return PromiseFactory.create_promise(computation=lambda: self.solve_sync(problem_or_workflow, artifacts, sandbox_context, **kwargs))

    # ============================================================================
    # PROBLEM SOLVING METHODS (Workflow Creation and Management)
    # ============================================================================

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
        try:
            return self.state.mind.memory.conversation.get_statistics()
        except Exception:
            return {
                "error": "Conversation memory not available",
                "total_messages": 0,
                "total_turns": 0,
                "active_turns": 0,
                "summary_count": 0,
                "session_count": 0,
            }

    def clear_conversation_memory(self) -> bool:
        """Clear the conversation memory for this agent."""
        try:
            self.state.mind.memory.conversation.clear()
            return True
        except Exception:
            return False

    # ============================================================================
    # RESOURCE MANAGEMENT (LLM Resources, Initialization, Cleanup)
    # ============================================================================

    def get_llm_resource(self, sandbox_context: SandboxContext | None = None):
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

    def _initialize_conversation_memory(self):
        """Initialize conversation memory if not already done.

        Note: Conversation memory is now managed by the centralized state system.
        This method is kept for backward compatibility but delegates to the state system.
        """
        # Conversation memory is automatically initialized as part of AgentState
        # No additional initialization needed
        pass

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
        """Initialize all agent resources that need explicit initialization."""
        try:
            # Initialize conversation memory (now handled by centralized state)
            self._initialize_conversation_memory()

            # Initialize LLM resource
            self._initialize_llm_resource()

            # Initializing engineering resources
            self._corral_engineer = CORRALEngineer()
            self._prompt_engineer = PromptEngineer()
            self._context_engineer = ContextEngineer()

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
            self.context_engineer = None
            self.corral_engineer = None
            self.prompt_engineer = None

            # Stop LLM resource if it was initialized
            if self._llm_resource is not None:
                try:
                    self._llm_resource.stop()
                except Exception as e:
                    import logging

                    logging.warning(f"Failed to stop LLM resource for {self.name}: {e}")

                # Cleanup LLM resource
                try:
                    self._llm_resource.cleanup()
                except Exception as e:
                    import logging

                    logging.warning(f"Failed to cleanup LLM resource for {self.name}: {e}")

                self._llm_resource = None

            # Clear conversation memory (now handled by centralized state)
            try:
                self.state.mind.memory.conversation.clear()
            except Exception as e:
                import logging

                logging.warning(f"Failed to clear conversation memory for {self.name}: {e}")

            # Clear working memory (now handled by centralized state)
            try:
                self.state.mind.memory.working.clear()
            except Exception as e:
                import logging

                logging.warning(f"Failed to clear working memory for {self.name}: {e}")

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

    # ---------------------------
    # Solver Integration Methods
    # ---------------------------
    def enable_planner_executor_solver(
        self,
        workflow_catalog: Any | None = None,
        resource_index: Any | None = None,
    ) -> "AgentInstance":
        """Enable planner-executor solver capabilities on this agent.

        Args:
            workflow_catalog: Optional workflow catalog for known workflow matching
            resource_index: Optional resource index for resource pack attachment

        Returns:
            Self for method chaining
        """
        # Dynamically add the solver mixin methods
        self._add_solver_methods(PlannerExecutorSolverMixin)

        # Set up dependencies
        if workflow_catalog:
            self.workflow_catalog = workflow_catalog
        if resource_index:
            self.resource_index = resource_index

        return self

    def enable_reactive_support_solver(
        self,
        signature_matcher: Any | None = None,
        workflow_catalog: Any | None = None,
        resource_index: Any | None = None,
    ) -> "AgentInstance":
        """Enable reactive support solver capabilities on this agent.

        Args:
            signature_matcher: Optional signature matcher for known issue patterns
            workflow_catalog: Optional workflow catalog for diagnostic workflows
            resource_index: Optional resource index for resource pack attachment

        Returns:
            Self for method chaining
        """
        # Dynamically add the solver mixin methods
        self._add_solver_methods(ReactiveSupportSolverMixin)

        # Set up dependencies
        if signature_matcher:
            self.signature_matcher = signature_matcher
        if workflow_catalog:
            self.workflow_catalog = workflow_catalog
        if resource_index:
            self.resource_index = resource_index

        return self

    def _add_solver_methods(self, solver_mixin_class: type[BaseSolverMixin]) -> None:
        """Dynamically add solver methods to this agent instance."""
        solver_instance = solver_mixin_class()

        # Copy all methods from the solver mixin to this instance
        for attr_name in dir(solver_instance):
            if (
                not attr_name.startswith("_")
                or attr_name.startswith("_solve")
                or attr_name.startswith("_run")
                or attr_name.startswith("_match")
                or attr_name.startswith("_create")
                or attr_name.startswith("_handle")
                or attr_name.startswith("_attach")
                or attr_name.startswith("_inject")
                or attr_name.startswith("_initialize")
                or attr_name.startswith("_extract")
            ):
                attr = getattr(solver_instance, attr_name)
                if callable(attr):
                    # Bind the method to this instance
                    bound_method = attr.__get__(self, type(self))
                    setattr(self, attr_name, bound_method)

        # Set the MIXIN_NAME attribute
        if hasattr(solver_instance, "MIXIN_NAME"):
            setattr(self, f"_active_solver_{solver_instance.MIXIN_NAME}", True)

    # ============================================================================
    # AGENT PERSISTENCE METHODS
    # ============================================================================

    def get_agent_id(self) -> str:
        """Get a unique identifier for this agent instance."""
        # Use the agent name if available, otherwise generate a unique ID
        agent_name = self.name if hasattr(self, "name") else "unnamed_agent"
        # Create a safe filename from the agent name
        safe_name = "".join(c for c in agent_name if c.isalnum() or c in ("-", "_")).rstrip()
        return f"{safe_name}_{id(self)}"

    def get_agent_base_path(self) -> Path:
        """Get the base persistence path for this agent."""
        agent_id = self.get_agent_id()
        return Path(f"~/.dana/agents/{agent_id}").expanduser()

    def enable_persistence(self, base_path: str | None = None) -> None:
        """Enable persistence for this agent and all its state components.

        Args:
            base_path: Custom base path for persistence (optional)
        """
        if base_path:
            agent_path = Path(base_path).expanduser()
        else:
            agent_path = self.get_agent_base_path()

        # Create agent directory structure
        agent_path.mkdir(parents=True, exist_ok=True)
        (agent_path / "state").mkdir(exist_ok=True)
        (agent_path / "sessions").mkdir(exist_ok=True)
        (agent_path / "logs").mkdir(exist_ok=True)

        # Enable state persistence
        self.state.enable_persistence(agent_path / "state")

        # Save agent metadata
        self.save_agent_metadata(agent_path)

    def save_agent_metadata(self, agent_path: Path | None = None) -> None:
        """Save agent metadata to the agent directory.

        Args:
            agent_path: Path to agent directory (optional)
        """
        import json
        from datetime import datetime

        if agent_path is None:
            agent_path = self.get_agent_base_path()

        metadata = {
            "agent_id": self.get_agent_id(),
            "agent_name": self.name if hasattr(self, "name") else "unnamed_agent",
            "agent_type": str(self.agent_type) if hasattr(self, "agent_type") else "unknown",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "state_summary": self.state.get_state_summary() if hasattr(self, "state") else {},
        }

        metadata_path = agent_path / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def save_session(self, session_name: str) -> None:
        """Save current agent state as a named session.

        Args:
            session_name: Name for the session
        """
        import json
        from datetime import datetime

        agent_path = self.get_agent_base_path()
        sessions_path = agent_path / "sessions" / "active"
        sessions_path.mkdir(parents=True, exist_ok=True)

        session_data = {
            "session_name": session_name,
            "created_at": datetime.now().isoformat(),
            "agent_metadata": {
                "agent_id": self.get_agent_id(),
                "agent_name": self.name if hasattr(self, "name") else "unnamed_agent",
            },
            "state_summary": self.state.get_state_summary() if hasattr(self, "state") else {},
        }

        session_path = sessions_path / f"{session_name}.json"
        with open(session_path, "w") as f:
            json.dump(session_data, f, indent=2)

    def list_sessions(self) -> list[str]:
        """List available sessions for this agent.

        Returns:
            List of session names
        """
        agent_path = self.get_agent_base_path()
        sessions_path = agent_path / "sessions" / "active"

        if not sessions_path.exists():
            return []

        sessions = []
        for session_file in sessions_path.glob("*.json"):
            sessions.append(session_file.stem)

        return sorted(sessions)

    def restore_session(self, session_name: str) -> bool:
        """Restore agent state from a named session.

        Args:
            session_name: Name of the session to restore

        Returns:
            True if restoration was successful, False otherwise
        """
        import json

        agent_path = self.get_agent_base_path()
        session_path = agent_path / "sessions" / "active" / f"{session_name}.json"

        if not session_path.exists():
            return False

        try:
            with open(session_path) as f:
                session_data = json.load(f)

            # Restore state if available
            if hasattr(self, "state") and "state_summary" in session_data:
                # Note: This is a basic restoration - full state restoration would need
                # more sophisticated serialization/deserialization
                pass

            return True
        except Exception:
            return False
