"""
Workflow System for Dana

Simplified workflow system that compiles to ComposedFunction for seamless integration
with Dana's function composition system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from typing import Any

from dana.core.builtins.struct_system import StructInstance, StructType
from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction
from dana.core.lang.sandbox_context import SandboxContext

ProblemContext = dict[str, Any]


@dataclass
class WorkflowType(StructType):
    """Workflow struct type with minimal workflow capabilities.

    Inherits from StructType and adds basic workflow functionality.
    """

    @staticmethod
    def get_default_workflow_fields() -> dict[str, dict[str, Any]]:
        """Get the default fields that all workflows should have."""
        return {
            "name": {
                "type": "str",
                "default": "A Workflow",
                "comment": "Name of the workflow",
            },
            "composed_function": {
                "type": "ComposedFunction | None",
                "default": None,
                "comment": "The composed function that implements the workflow",
            },
            "metadata": {
                "type": "dict",
                "default": {},
                "comment": "Additional workflow metadata",
            },
        }

    @classmethod
    def create_for_problem(cls, problem: str, strategy_name: str = "Agent", custom_fields: dict[str, str] | None = None) -> "WorkflowType":
        """Create a workflow type for a specific problem.

        Args:
            problem: The problem statement
            strategy_name: Name of the strategy creating the workflow (e.g., "Agent", "Recursive", "Iterative")
            custom_fields: Optional custom fields to add to the workflow type

        Returns:
            WorkflowType instance configured for the problem
        """
        # Generate unique name based on problem hash
        name = f"{strategy_name}Workflow_{hash(problem) % 10000}"

        # Default custom fields for agent workflows
        if custom_fields is None and strategy_name == "Agent":
            custom_fields = {"problem_statement": "str", "objective": "str", "problem_context": "Any", "action_history": "Any"}
        elif custom_fields is None:
            custom_fields = {}

        # Create field order and defaults
        field_order = list(custom_fields.keys())
        field_defaults = (
            {
                "problem_statement": problem,
                "objective": "Solve the problem",
                "problem_context": None,
                "action_history": None,
            }
            if strategy_name == "Agent"
            else {}
        )

        # Create field comments
        field_comments = (
            {
                "problem_statement": "The problem to solve",
                "objective": "The objective of the workflow",
                "problem_context": "Problem-specific context",
                "action_history": "Global action history",
            }
            if strategy_name == "Agent"
            else {}
        )

        return cls(
            name=name,
            fields=custom_fields,
            field_order=field_order,
            field_comments=field_comments,
            field_defaults=field_defaults,
            docstring=f"{strategy_name} workflow for solving: {problem}",
        )

    def __init__(
        self,
        name: str,
        fields: dict[str, str],
        field_order: list[str],
        field_comments: dict[str, str] | None = None,
        field_defaults: dict[str, Any] | None = None,
        docstring: str | None = None,
    ):
        """Initialize WorkflowType with default workflow fields."""
        # Add default workflow fields automatically
        additional_fields = self.get_default_workflow_fields()

        # Merge additional fields into the provided fields
        merged_fields = fields.copy()
        merged_field_order = field_order.copy()
        merged_field_defaults = field_defaults.copy() if field_defaults else {}
        merged_field_comments = field_comments.copy() if field_comments else {}

        for field_name, field_info in additional_fields.items():
            if field_name not in merged_fields:
                merged_fields[field_name] = field_info["type"]
                merged_field_order.append(field_name)
                merged_field_defaults[field_name] = field_info["default"]
                merged_field_comments[field_name] = field_info["comment"]

        # Initialize as a regular StructType
        super().__init__(
            name=name,
            fields=merged_fields,
            field_order=merged_field_order,
            field_comments=merged_field_comments,
            field_defaults=merged_field_defaults,
            docstring=docstring,
        )


class WorkflowInstance(StructInstance):
    """Workflow struct instance that wraps a ComposedFunction.

    This simplified workflow system directly uses Dana's function composition
    system for execution.
    """

    def __init__(self, struct_type: WorkflowType, values: dict[str, Any], parent_workflow: "WorkflowInstance | None" = None):
        """Create a new workflow struct instance.

        Args:
            struct_type: The workflow struct type definition
            values: Field values (must match struct type requirements)
            parent_workflow: Parent workflow instance for recursive calls
        """
        # Ensure we have a WorkflowType
        if not isinstance(struct_type, WorkflowType):
            raise TypeError(f"WorkflowInstance requires WorkflowType, got {type(struct_type)}")

        # Initialize workflow-specific state
        self._execution_history = []
        self._composed_function = None
        self._parent_workflow = parent_workflow
        self._children = []

        # Initialize workflow-specific state
        self._execution_history = []
        self._composed_function = None
        self._parent_workflow = parent_workflow
        self._children = []

        # Initialize the base StructInstance
        super().__init__(struct_type, values, None)

        # Extract composed function from values if provided
        if "composed_function" in values:
            self._composed_function = values["composed_function"]

        # Link to parent if provided
        if parent_workflow:
            parent_workflow._children.append(self)

    def set_composed_function(self, composed_function: SandboxFunction) -> None:
        """Set the composed function for this workflow."""
        self._composed_function = composed_function

    def get_composed_function(self) -> SandboxFunction | None:
        """Get the composed function for this workflow."""
        return self._composed_function

    def get_root_workflow(self) -> "WorkflowInstance":
        """Navigate to root workflow."""
        current = self
        while current._parent_workflow:
            current = current._parent_workflow
        return current

    def get_sibling_workflows(self) -> list["WorkflowInstance"]:
        """Get workflows at same level."""
        if not self._parent_workflow:
            return []
        return [w for w in self._parent_workflow._children if w != self]

    def get_ancestor_context(self, levels_up: int) -> Any:
        """Get context from ancestor workflow (simplified version)."""
        current = self
        for _ in range(levels_up):
            if current._parent_workflow:
                current = current._parent_workflow
            else:
                break
        # In simplified design, no problem_context available
        return None

    def get_execution_history(self) -> list[dict[str, Any]]:
        """Get the execution history of the workflow."""
        return self._execution_history.copy()

    def add_execution_step(self, step: dict[str, Any]) -> None:
        """Add an execution step to the history."""
        self._execution_history.append(step)

    def execute(self, context: SandboxContext, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the workflow using the composed function.

        Args:
            context: The execution context
            *args: Positional arguments to pass to the workflow
            **kwargs: Keyword arguments to pass to the workflow

        Returns:
            The result of workflow execution

        Raises:
            RuntimeError: If no composed function set
        """
        print("[DEBUG] WorkflowInstance.execute() called")
        print(f"[DEBUG] context: {context}")
        print(f"[DEBUG] args: {args}")
        print(f"[DEBUG] kwargs: {kwargs}")
        print(f"[DEBUG] self._composed_function: {self._composed_function}")

        if not self._composed_function:
            print("[DEBUG] ERROR: No composed function set for this workflow")
            raise RuntimeError("No composed function set for this workflow")

        # Set up execution context
        print("[DEBUG] Setting up execution context...")
        context.workflow_instance = self

        # Record execution start
        import time

        start_time = time.time()

        # Add execution step to history
        self.add_execution_step({"step": "start", "timestamp": start_time, "status": "executing"})

        try:
            print("[DEBUG] Executing composed function...")
            # Execute the composed function - handle both ComposedFunction and regular callables
            if hasattr(self._composed_function, "execute"):
                # It's a ComposedFunction or similar object with execute method
                print("[DEBUG] Using execute() method")
                result = self._composed_function.execute(context, *args, **kwargs)
            else:
                # It's a regular callable function
                print("[DEBUG] Using direct call")
                result = self._composed_function(*args, **kwargs)

            print(f"[DEBUG] Function execution completed, result: {type(result)} = {result}")

            # Record successful completion
            execution_time = time.time() - start_time
            self.add_execution_step(
                {"step": "complete", "timestamp": time.time(), "status": "completed", "execution_time": execution_time, "result": result}
            )

            return result

        except Exception as e:
            print(f"[DEBUG] Function execution failed with error: {e}")
            # Record error
            execution_time = time.time() - start_time
            self.add_execution_step(
                {"step": "error", "timestamp": time.time(), "status": "error", "execution_time": execution_time, "error": str(e)}
            )
            raise e

    def get_status(self) -> str:
        """
        Get current execution status based on execution history.

        Returns:
            str: Current status ("ready", "executing", "completed", "error")
        """
        if not self._execution_history:
            return "ready"

        last_step = self._execution_history[-1]
        step_name = last_step.get("step", "")

        if step_name == "error":
            return "error"
        elif step_name == "complete":
            return "completed"
        elif step_name == "start":
            return "executing"
        else:
            return "ready"

    @property
    def name(self) -> str:
        """Get the name of the workflow."""
        return self.struct_type.name

    def get_history(self) -> list[dict[str, Any]]:
        """Get execution history."""
        return self.get_execution_history()

    def _get_timestamp(self) -> str:
        """Get current timestamp for execution history."""
        import datetime

        return datetime.datetime.now().isoformat()

    @classmethod
    def create_simple(cls, problem: str, agent_state=None, **kwargs) -> "WorkflowInstance":
        """Create a simple workflow for a problem without strategy selection.

        Args:
            problem: The problem statement to solve
            agent_state: Optional agent state for context (AgentState)
            **kwargs: Additional parameters including 'objective'

        Returns:
            A new WorkflowInstance configured for the problem
        """
        from dana.core.agent.context import ProblemContext

        # Create problem context with conversation context if agent state provided
        problem_context = ProblemContext(
            problem_statement=problem, objective=kwargs.get("objective", f"Solve: {problem}"), original_problem=problem, depth=0
        )

        # Add conversation history to constraints if agent state available
        if agent_state and hasattr(agent_state, "timeline"):
            from dana.core.agent.timeline.timeline_event import ConversationTurn

            conversation_context = ConversationTurn.get_conversation_context(agent_state.timeline)
            if conversation_context:
                problem_context.constraints["conversation_history"] = conversation_context

        # Create workflow instance
        workflow = cls(
            struct_type=WorkflowType.create_for_problem(problem, "Agent"),
            values={
                "problem_statement": problem,
                "objective": problem_context.objective,
                "problem_context": problem_context,
                "action_history": agent_state.timeline if agent_state else None,
            },
            parent_workflow=None,
        )

        return workflow

    @classmethod
    def create_with_strategy(
        cls, problem: str, strategy_type: str = "auto", agent_instance=None, sandbox_context=None, **kwargs
    ) -> "WorkflowInstance":
        """Create a workflow using a specific strategy or auto-selection.

        Args:
            problem: The problem statement to solve
            strategy_type: Strategy to use ("auto", "iterative", "recursive")
            agent_instance: AgentInstance (required for strategy execution)
            sandbox_context: Optional sandbox context for execution
            **kwargs: Additional parameters including 'objective'

        Returns:
            A new WorkflowInstance created using the specified strategy
        """
        from dana.core.agent.context import ProblemContext
        from dana.core.agent.strategy import BaseStrategy

        if not agent_instance:
            raise ValueError("agent_instance is required for strategy-based workflow creation")

        # Create problem context with conversation context from centralized state
        from dana.core.agent.timeline.timeline_event import ConversationTurn

        conversation_context = ConversationTurn.get_conversation_context(agent_instance.state.timeline)

        problem_context = ProblemContext(
            problem_statement=problem, objective=kwargs.get("objective", f"Solve: {problem}"), original_problem=problem, depth=0
        )

        # Add conversation history to constraints if available
        if conversation_context:
            problem_context.constraints["conversation_history"] = conversation_context

        # Select strategy
        if strategy_type == "auto":
            strategy = BaseStrategy.select_best_strategy(problem, problem_context)
        elif strategy_type == "iterative":
            from dana.core.agent.strategy.iterative.iterative_strategy import IterativeStrategy

            strategy = IterativeStrategy()
        elif strategy_type == "recursive":
            from dana.core.agent.strategy.recursive.recursive_strategy import RecursiveStrategy

            strategy = RecursiveStrategy()
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        # Create workflow using strategy
        workflow = strategy.create_workflow(problem, problem_context, agent_instance, sandbox_context=sandbox_context)

        return workflow

    @classmethod
    def create_from_source(cls, name: str, source, agent_state=None, **kwargs) -> "WorkflowInstance":
        """Create a workflow from various sources (function, code string, etc.).

        Args:
            name: Name of the workflow
            source: Source to create workflow from (ComposedFunction, str, etc.)
            agent_state: Optional agent state for context
            **kwargs: Additional parameters including 'metadata'

        Returns:
            A new WorkflowInstance created from the source
        """
        from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction

        if isinstance(source, SandboxFunction):
            # Create from ComposedFunction
            return cls._create_from_composed_function(name, source, kwargs.get("metadata"))
        elif isinstance(source, str):
            # Create from Dana code string
            if not agent_state:
                raise ValueError("agent_state required when creating workflow from Dana code string")
            return cls._create_from_dana_code(name, source, agent_state, kwargs.get("metadata"))
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

    @classmethod
    def _create_from_composed_function(
        cls, name: str, composed_function: SandboxFunction, metadata: dict[str, Any] | None = None
    ) -> "WorkflowInstance":
        """Create a workflow from a ComposedFunction."""
        # Create workflow type with default fields
        workflow_type = WorkflowType(name=name, fields={}, field_order=[], docstring=f"Workflow: {name}")

        # Create workflow instance
        workflow = cls(
            workflow_type,
            {
                "name": name,
                "composed_function": composed_function,
                "metadata": metadata or {},
            },
        )

        return workflow

    @classmethod
    def _create_from_dana_code(cls, name: str, dana_code: str, agent_state, metadata: dict[str, Any] | None = None) -> "WorkflowInstance":
        """Create a workflow by parsing Dana code directly."""
        # Get sandbox context from agent state
        sandbox_context = agent_state.execution.sandbox_context
        if not sandbox_context:
            raise ValueError("No sandbox context available in agent state")

        # Parse Dana code using the context's parser
        ast = sandbox_context.parser.parse_expression(dana_code)

        # Execute AST to get ComposedFunction using the context's interpreter
        composed_function = sandbox_context.interpreter.evaluate_expression(ast, sandbox_context)

        # Create workflow instance
        workflow = cls._create_from_composed_function(
            name=name,
            composed_function=composed_function,
            metadata={"dana_code": dana_code, "source": "dana_code", **(metadata or {})},
        )

        return workflow

    # Legacy method for backward compatibility
    @classmethod
    def create_for_problem(cls, problem: str, agent_state=None, **kwargs) -> "WorkflowInstance":
        """Legacy method - use create_simple() instead."""
        return cls.create_simple(problem, agent_state, **kwargs)


# Legacy factory functions (deprecated - use WorkflowInstance.create_from_source() instead)


def create_workflow_from_composed_function(
    name: str, composed_function: SandboxFunction, metadata: dict[str, Any] | None = None
) -> WorkflowInstance:
    """
    DEPRECATED: Use WorkflowInstance.create_from_source() instead.

    Create a workflow from a ComposedFunction.

    Args:
        name: Name of the workflow
        composed_function: The composed function to execute
        metadata: Optional metadata for the workflow

    Returns:
        WorkflowInstance with the composed function
    """
    return WorkflowInstance._create_from_composed_function(name, composed_function, metadata)


def create_workflow_from_dana_code(
    name: str, dana_code: str, context: SandboxContext, metadata: dict[str, Any] | None = None
) -> WorkflowInstance:
    """
    DEPRECATED: Use WorkflowInstance.create_from_source() instead.

    Create a workflow by parsing Dana code directly.

    Args:
        name: Name of the workflow
        dana_code: Dana pipeline expression as a string
        context: SandboxContext with parser and interpreter
        metadata: Optional metadata for the workflow

    Returns:
        WorkflowInstance with parsed ComposedFunction
    """
    # Create a mock agent state with the sandbox context for the new method
    from dana.core.agent.agent_state import AgentState
    from dana.core.agent.context import ExecutionContext

    # Create minimal agent state with sandbox context
    execution = ExecutionContext()
    execution.sandbox_context = context
    agent_state = AgentState(execution=execution)

    return WorkflowInstance.create_from_source(name, dana_code, agent_state, metadata=metadata)
