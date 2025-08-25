"""
Agent Instance System

This module defines the AgentInstance class which extends StructInstance to provide
agent-specific state and methods. This is the main implementation file for agent instances.
"""

from typing import Any

from dana.builtin_types.struct_system import StructInstance
from dana.common.mixins.loggable import Loggable

# Removed direct import of LegacyLLMResource - now using resource type system
from dana.core.concurrency.promise_factory import PromiseFactory
from dana.core.concurrency.promise_utils import resolve_if_promise
from dana.core.lang.sandbox_context import SandboxContext

from .agent_type import AgentType
from .events import AgentEventMixin
from .implementations import AgentImplementationMixin
from .solving import AgentSolvingMixin


class AgentInstance(StructInstance, AgentSolvingMixin, AgentImplementationMixin, AgentEventMixin):
    """Agent struct instance with built-in agent capabilities.

    Inherits from StructInstance and adds agent-specific state and methods.
    """

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

    @property
    def name(self) -> str:
        """Get the agent's name for TUI compatibility."""
        # Return the instance name field value, not the struct type name
        return self._values.get("name", "unnamed_agent")

    @staticmethod
    def get_default_dana_methods() -> dict[str, Any]:
        """Get the default agent methods that all agents should have.

        This method defines what the standard agent methods are,
        keeping the definition close to where they're implemented.
        """

        return {
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

    @property
    def agent_type(self) -> AgentType:
        """Get the agent type."""
        return self.__struct_type__  # type: ignore

    def plan(self, task: str, context: dict | None = None, sandbox_context: SandboxContext | None = None, is_sync: bool = False) -> Any:
        """Execute agent planning method - analyzes problem and determines approach."""

        sandbox_context = sandbox_context or SandboxContext()

        def wrapper():
            return self._create_plan(task, context, sandbox_context)

        return wrapper() if is_sync else PromiseFactory.create_promise(computation=wrapper)

    def solve(self, problem: str, context: dict | None = None, sandbox_context: SandboxContext | None = None, is_sync: bool = False) -> Any:
        """Execute agent problem-solving method with enhanced approach routing.

        Implements the pseudocode pattern:
        agent.solve(problem) {
            approach = agent.plan(problem)
            return execute_approach(approach, problem)
        }
        """
        sandbox_context = sandbox_context or SandboxContext()

        self.debug(f"IN SOLVE: is_sync={is_sync}")

        def wrapper():
            try:
                return self._solve_problem(sandbox_context, problem, context)
            except Exception as e:
                import traceback

                traceback.print_exc()
                self.error(f"Error in solve: {e}")
                raise e

        # is_sync = True  # CTN
        return wrapper() if is_sync else PromiseFactory.create_promise(computation=wrapper)

    def remember(self, key: str, value: Any, sandbox_context: SandboxContext | None = None, is_sync: bool = False) -> Any:
        """Execute agent memory storage method."""

        sandbox_context = sandbox_context or SandboxContext()

        def wrapper():
            return self._remember_impl(sandbox_context, key, value)

        return wrapper() if is_sync else PromiseFactory.create_promise(computation=wrapper)

    def recall(self, key: str, sandbox_context: SandboxContext | None = None, is_sync: bool = False) -> Any:
        """Execute agent memory retrieval method."""

        sandbox_context = sandbox_context or SandboxContext()

        def wrapper():
            return self._recall_impl(sandbox_context, key)

        return wrapper() if is_sync else PromiseFactory.create_promise(computation=wrapper)

    def reason(
        self, premise: str, context: dict | None = None, sandbox_context: SandboxContext | None = None, is_sync: bool = False
    ) -> Any:
        """Execute agent reasoning method."""
        sandbox_context = sandbox_context or SandboxContext()
        return self._reason_impl(sandbox_context, premise, context, is_sync=True)

    def chat(
        self,
        message: str,
        context: dict | None = None,
        max_context_turns: int = 5,
        sandbox_context: SandboxContext | None = None,
        is_sync: bool = False,
    ) -> Any:
        """Execute agent chat method."""

        sandbox_context = sandbox_context or SandboxContext()

        def wrapper():
            return self._chat_impl(sandbox_context, message, context, max_context_turns)

        def save_conversation_callback(response):
            """Callback to save the conversation turn when the response is ready."""
            if self._conversation_memory:
                # Handle case where response might be an EagerPromise
                response = resolve_if_promise(response)
                self._conversation_memory.add_turn(message, response)

        if is_sync:
            result = wrapper()
            save_conversation_callback(result)
            return result
        else:
            return PromiseFactory.create_promise(computation=wrapper, on_delivery=save_conversation_callback)

    def log(self, message: str, level: str = "INFO", sandbox_context: SandboxContext | None = None, is_sync: bool = False) -> Any:
        """Execute agent logging method."""

        sandbox_context = sandbox_context or SandboxContext()

        def wrapper():
            self._notify_log_callbacks(message, level, sandbox_context)

            _message = f"[{self.name}] {message}"
            _level = level.upper()

            # Use both custom logging and standard Python logging
            import logging

            # Standard Python logging for test compatibility
            if _level == "INFO":
                logging.info(_message)
                Loggable.info(self, _message)
            elif _level == "WARNING":
                logging.warning(_message)
                Loggable.warning(self, _message)
            elif _level == "DEBUG":
                logging.debug(_message)
                Loggable.debug(self, _message)
            elif _level == "ERROR":
                logging.error(_message)
                Loggable.error(self, _message)
            else:
                logging.info(_message)
                Loggable.info(self, _message)

            return message

        # is_sync = True
        if is_sync:
            return wrapper()
        else:
            return PromiseFactory.create_promise(computation=wrapper)

    def info(self, message: str, sandbox_context: SandboxContext | None = None, is_sync: bool = False) -> Any:
        """Execute agent logging method. Override to notify log callbacks."""
        # _notify_log_callbacks(self.name, f"[INFO] {message}", sandbox_context)
        self.log(message, "INFO", sandbox_context, is_sync)

    def warning(self, message: str, sandbox_context: SandboxContext | None = None, is_sync: bool = False) -> Any:
        """Execute agent logging method. Override to notify log callbacks."""
        self.log(message, "WARNING", sandbox_context, is_sync)

    def debug(self, message: str, sandbox_context: SandboxContext | None = None, is_sync: bool = False) -> Any:
        """Execute agent logging method. Override to notify log callbacks."""
        self.log(message, "DEBUG", sandbox_context, is_sync)

    def error(self, message: str, sandbox_context: SandboxContext | None = None, is_sync: bool = False) -> Any:
        """Execute agent logging method. Override to notify log callbacks."""
        self.log(message, "ERROR", sandbox_context, is_sync)

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
            self.log("Agent resources initialized", is_sync=True)

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
            self.log("Agent resources cleaned up", is_sync=True)

        except Exception as e:
            # Log cleanup error but don't fail completely
            import logging

            logging.error(f"Failed to cleanup agent resources for {self.name}: {e}")
            # Update metrics to indicate cleanup failure
            self.update_metric("current_step", "cleanup_failed")
