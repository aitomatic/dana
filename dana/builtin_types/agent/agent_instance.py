"""
Agent Instance System

This module defines the AgentInstance class which extends StructInstance to provide
agent-specific state and methods. This is the main implementation file for agent instances.
"""

from typing import TYPE_CHECKING, Any

from dana.builtin_types.struct_system import StructInstance
from dana.common.mixins.loggable import Loggable
from dana.common.types import BaseRequest, BaseResponse

# Removed direct import of LegacyLLMResource - now using resource type system
from dana.core.concurrency.promise_factory import PromiseFactory
from dana.core.concurrency.promise_utils import resolve_if_promise
from dana.core.lang.sandbox_context import SandboxContext
from dana.frameworks.memory.conversation_memory import ConversationMemory

from .agent_type import AgentType
from .events import AgentEventMixin
from .implementations import AgentImplementationMixin

if TYPE_CHECKING:
    pass

from dana.builtin_types.workflow.workflow_system import WorkflowInstance, WorkflowType

from .context import ProblemContext


class AgentInstance(StructInstance, AgentImplementationMixin, AgentEventMixin):
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

    @property
    def agent_type(self) -> AgentType:
        """Get the agent type."""
        return self.__struct_type__  # type: ignore

    def answer(self, answer: str, sandbox_context: SandboxContext | None = None):
        """Execute agent answer method."""
        print(answer)

    def input(
        self,
        request: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: ProblemContext | None = None,
        is_sync: bool = False,
    ) -> Any:
        """Execute agent input method."""
        sandbox_context = sandbox_context or SandboxContext()

        # Prompt the user for input from the console
        response = input(request)

        # Return the response
        return response

    def llm(self, request: str | dict | BaseRequest, sandbox_context: SandboxContext | None = None, **kwargs) -> str | BaseResponse:
        """Execute agent LLM method using py_llm for proper Dana integration."""
        if not sandbox_context:
            return "Sandbox context required for LLM calls"

        # Get LLM resource
        llm_resource = self.get_llm_resource(sandbox_context)
        if llm_resource is None:
            return "LLM resource not available - please configure an LLM resource for this agent"

        try:
            # Import py_llm
            from dana.libs.corelib.py_wrappers.py_llm import py_llm

            # Prepare the prompt
            if isinstance(request, str):
                prompt = request
            elif isinstance(request, dict):
                if "prompt" in request:
                    prompt = request["prompt"]
                elif "messages" in request:
                    # Extract user message from messages
                    messages = request["messages"]
                    if messages and isinstance(messages, list):
                        # Find the last user message
                        for msg in reversed(messages):
                            if isinstance(msg, dict) and msg.get("role") == "user":
                                prompt = msg.get("content", "")
                                break
                        else:
                            prompt = str(messages[-1]) if messages else ""
                    else:
                        prompt = str(messages)
                else:
                    prompt = str(request)
            elif isinstance(request, BaseRequest):
                # Extract prompt from BaseRequest arguments
                args = request.arguments
                if isinstance(args, dict):
                    if "prompt" in args:
                        prompt = args["prompt"]
                    elif "messages" in args:
                        messages = args["messages"]
                        if messages and isinstance(messages, list):
                            for msg in reversed(messages):
                                if isinstance(msg, dict) and msg.get("role") == "user":
                                    prompt = msg.get("content", "")
                                    break
                            else:
                                prompt = str(messages[-1]) if messages else ""
                        else:
                            prompt = str(messages)
                    else:
                        prompt = str(args)
                else:
                    prompt = str(args)
            else:
                raise ValueError(f"Invalid request type: {type(request)}")

            # Prepare options
            options = {}
            if isinstance(request, dict) and "system" in request:
                options["system_message"] = request["system"]

            # Call py_llm with the agent's LLM resource directly, synchronously
            result = py_llm(context=sandbox_context, prompt=prompt, options=options, llm_resource=llm_resource, is_sync=True)

            # Return the result directly (no Promise handling needed)
            return result

        except Exception as e:
            return f"Error calling LLM: {str(e)}"

    def plan(
        self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext | None = None, **kwargs
    ) -> WorkflowInstance:
        """Create a plan (workflow) for solving the problem."""

        print(f"[DEBUG] agent.plan() called with: {type(problem_or_workflow)} = {problem_or_workflow}")
        print(f"[DEBUG] sandbox_context: {sandbox_context}")
        print(f"[DEBUG] kwargs: {kwargs}")

        if isinstance(problem_or_workflow, str):
            # Create new workflow for string problem
            print("[DEBUG] Creating new workflow for string problem...")
            workflow = self._create_new_workflow(problem_or_workflow, sandbox_context=sandbox_context, **kwargs)
            print(f"[DEBUG] New workflow created: {type(workflow)}")
        else:
            # Use existing workflow
            print(f"[DEBUG] Using existing workflow: {type(problem_or_workflow)}")
            workflow = problem_or_workflow

        print(f"[DEBUG] Plan returning workflow: {type(workflow)}")
        return workflow

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

    def solve(self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext | None = None, **kwargs) -> Any:
        """Solve a problem using the agent's problem-solving capabilities."""

        print(f"[DEBUG] agent.solve() called with: {type(problem_or_workflow)} = {problem_or_workflow}")
        print(f"[DEBUG] sandbox_context: {sandbox_context}")
        print(f"[DEBUG] kwargs: {kwargs}")

        # If this is a new user request (string), start a new conversation turn
        if isinstance(problem_or_workflow, str):
            print(f"[DEBUG] Starting new conversation turn for: {problem_or_workflow}")
            self._global_event_history.start_new_conversation_turn(problem_or_workflow)

        # Enhanced context assembly using Context Engineering Framework
        if isinstance(problem_or_workflow, str):
            try:
                from dana.frameworks.ctxeng import ContextEngine

                # Create context engine for this agent
                if self._context_engine is None:
                    self._context_engine = ContextEngine.from_agent(self)

                # Assemble rich context using ctxeng framework
                rich_prompt = self._context_engine.assemble(
                    problem_or_workflow,
                    template="problem_solving",  # Use problem-solving template
                )

                print(f"[DEBUG] Context Engine assembled rich prompt (length: {len(rich_prompt)})")
                print(f"[DEBUG] Rich prompt preview: {rich_prompt[:200]}...")

                # Use rich prompt instead of basic problem
                problem_or_workflow = rich_prompt

            except ImportError:
                print("[DEBUG] Context Engineering Framework not available, using basic problem")
            except Exception as e:
                print(f"[DEBUG] Context Engine failed: {e}, using basic problem")

        # Always create or reuse a workflow via plan(), then execute
        print("[DEBUG] Calling agent.plan()...")
        workflow = self.plan(problem_or_workflow, sandbox_context=sandbox_context, **kwargs)
        print(f"[DEBUG] Plan returned workflow: {type(workflow)}")
        print(f"[DEBUG] Workflow values: {getattr(workflow, '_values', 'No _values')}")

        print("[DEBUG] Executing workflow...")
        result = workflow.execute(sandbox_context or self._create_sandbox_context(), **kwargs)
        print(f"[DEBUG] Workflow execution result: {type(result)} = {result}")

        return result

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
        self,
        premise: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: dict | None = None,
        system_message: str | None = None,
        is_sync: bool = False,
    ) -> Any:
        """Execute agent reasoning method."""
        sandbox_context = sandbox_context or SandboxContext()
        return self._reason_impl(sandbox_context, premise, problem_context, system_message, is_sync=True)

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

    def _initialize_conversation_memory(self):
        """Initialize the conversation memory for this agent."""
        self._conversation_memory = ConversationMemory()

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

    def _initialize_llm_resource(self):
        """Initialize the LLM resource for this agent."""
        try:
            # Check if we're in a test environment by looking for DANA_MOCK_LLM
            import os

            if os.getenv("DANA_MOCK_LLM", "false").lower() == "true":
                # Create a mock LLM resource for testing
                from tests.conftest import create_mock_llm_resource

                self._llm_resource_instance = create_mock_llm_resource()
            else:
                # In a real implementation, this would be configured based on agent settings
                # For now, we'll return None to indicate no LLM resource is available
                self._llm_resource_instance = None

        except Exception as e:
            import logging

            logging.warning(f"Failed to initialize LLM resource for {self.name}: {e}")
            self._llm_resource_instance = None

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
