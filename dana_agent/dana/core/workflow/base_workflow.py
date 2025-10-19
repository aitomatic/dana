from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dana.common.base_wa import BaseWA
from dana.common.observable import observable
from dana.common.protocols import AgentProtocol, DictParams, WorkflowProtocol
from dana.common.protocols.war import tool_use
from dana.core.global_registry import get_workflow_registry


if TYPE_CHECKING:
    from dana.lib.agents.workflow_step_agent import WorkflowStepAgent


@dataclass
class WorkflowStep:
    """A structured step definition for workflows."""

    name: str
    callable: Callable
    store_as: str | None = None
    required: bool = True
    validate: DictParams | None = None

    def __post_init__(self):
        """Post-initialization validation."""
        if not callable(self.callable):
            raise ValueError(f"Step '{self.name}' callable must be callable")

        # If no store_as specified, use the name
        if self.store_as is None:
            self.store_as = self.name


class BaseWorkflow(BaseWA, WorkflowProtocol):
    """This docstring is the public description of the workflow.
    Here we place all the public descriptions an agent would need to know
    to use the workflow effectively. This will go into the WORKFLOW_DESCRIPTIONS
    section of the agent's system prompt.
    """

    def __init__(
        self,
        args_transform: str | None = None,
        pre_callable: Callable[[DictParams], None] | None = None,
        post_callable: Callable[[DictParams], None] | None = None,
        workflow_type: str | None = None,
        workflow_id: str | None = None,
        auto_register: bool = True,
        registry=None,
        composite_left: BaseWorkflow | None = None,
        composite_right: BaseWorkflow | None = None,
        **kwargs,
    ):
        """
        Initialize the BaseWorkflow.

        Args:
            transform: Declarative transformation string combining input mappings and output name.
                Format: "input_mappings -> output_name" or just "input_mappings" (output defaults to "result")
                or just "-> output_name" (only rename output).
                Examples:
                    "url=result.results.0.url|url, purpose=query -> fetch_result"
                    "content=result.fact, metadata=fetch_result.metadata"
                    "-> search_result"
                Cannot be used with pre_callable or post_callable.
            pre_callable: The callable to update the arguments before executing the workflow.
                You can use pre_callable to map the arguments to the workflow to a different name.
            post_callable: The callable to update the result after executing the workflow.
                You can use post_callable to rename the "result" key to "some_named_result" if you want to.
            workflow_type: Type of workflow (e.g., 'research', 'data_processing')
            workflow_id: ID of the workflow (defaults to None)
            agent: The agent associated with this workflow
            auto_register: Whether to automatically register with the global registry
            registry: Specific registry to use (defaults to global registry)
            agent: The agent associated with this workflow
            **kwargs: Additional arguments passed to parent classes
        """
        # Call super().__init__ to properly initialize all parent classes
        super().__init__(object_id=workflow_id, **kwargs)
        self.workflow_type = workflow_type or self.__class__.__name__

        # Compile declarative transformation to callables
        self.output_key = None  # Key to namespace workflow output under
        if args_transform:
            if pre_callable or post_callable:
                raise ValueError("Cannot specify 'transform' with 'pre_callable' or 'post_callable'")

            # Parse the transform string: "input_mappings -> output_name"
            if "->" in args_transform:
                input_part, output_part = args_transform.split("->", 1)
                input_part = input_part.strip()
                output_part = output_part.strip()
                self.output_key = output_part if output_part else None
            else:
                input_part = args_transform.strip()

            # Compile input mappings if present
            if input_part:
                pre_callable = self._compile_input_mapping(input_part)

        self.pre_callable = pre_callable
        self.post_callable = post_callable

        # Handle workflow registration
        self._registry = registry or get_workflow_registry()
        if auto_register:
            self._register_self()

        self.composite_left = composite_left
        self.composite_right = composite_right

        self._workflow_step_agent = None

    @property
    def workflow_step_agent(self) -> WorkflowStepAgent:
        """Get the orchestrator agent for this workflow."""
        if self._workflow_step_agent is None:
            id = f"{self.workflow_id}-workflow-agent"

            from dana.lib.agents.workflow_step_agent import WorkflowStepAgent

            self._workflow_step_agent = WorkflowStepAgent(agent_id=id)
        return self._workflow_step_agent

    @staticmethod
    def _get_nested_value(data: DictParams, path: str) -> any:
        """
        Get a nested value from a dictionary using dot notation and array indexing.

        Args:
            data: The dictionary to extract from
            path: Dot-separated path (e.g., "result.results.0.url")

        Returns:
            The value at the path, or None if not found
        """
        parts = path.split(".")
        current = data

        for part in parts:
            if current is None:
                return None

            # Check if this is an array index
            if part.isdigit():
                index = int(part)
                try:
                    if isinstance(current, list):
                        current = current[index]  # type: ignore
                    elif isinstance(current, dict):
                        current = current.get(part)
                    else:
                        return None
                except (KeyError, IndexError, TypeError):
                    return None
            else:
                # Dictionary key access
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None

        return current

    @staticmethod
    def _compile_input_mapping(input_spec: str) -> Callable[[DictParams], None]:
        """
        Compile an input mapping specification to a callable.

        Args:
            input_spec: String like "url = result.results.0.url | url, purpose = query"

        Returns:
            A callable that updates the input dict in-place

        Resolution logic:
            - Simple keys (no dots): Check result.{key} first, then top-level
              Example: "url=url" tries kwargs["result"]["url"], then kwargs["url"]
            - Explicit paths (with dots): Use exact path only
              Example: "url=result.url" only tries kwargs["result"]["url"]
        """
        # Parse the spec: split by comma to get individual mappings
        mappings = []
        for mapping_str in input_spec.split(","):
            mapping_str = mapping_str.strip()
            if "=" not in mapping_str:
                continue

            target_key, source_spec = mapping_str.split("=", 1)
            target_key = target_key.strip()
            source_spec = source_spec.strip()

            # Parse fallback paths (separated by |)
            source_paths = [p.strip() for p in source_spec.split("|")]
            mappings.append((target_key, source_paths))

        def mapper(data: DictParams) -> None:
            """Update data dict with mapped values."""
            for target_key, source_paths in mappings:
                # Try each path until one succeeds
                value = None
                for path in source_paths:
                    # Simple key (no dots) - check result first, then top-level
                    if "." not in path:
                        # Try result.{key} first
                        if "result" in data and isinstance(data["result"], dict):
                            value = data["result"].get(path)
                            if value is not None:
                                break
                        # Fallback to top-level
                        if path in data:
                            value = data[path]
                            break
                    else:
                        # Explicit path - use exact nested lookup
                        value = BaseWorkflow._get_nested_value(data, path)
                        if value is not None:
                            break

                # Update with the found value (or None if all paths failed)
                data[target_key] = value if value is not None else ""

        return mapper

    @tool_use
    @observable
    def execute(self, **kwargs) -> DictParams:
        """Invoke the workflow with pre/post-processing.
        Args:
            **kwargs: Keyword arguments passed to the workflow

        Returns: A DictParams with the execution results merged with input kwargs.
        """
        # Check if this is a composite workflow
        if self.composite_left and self.composite_right:
            # Execute left workflow
            left_result: DictParams = self.composite_left.execute(**kwargs)

            # Merge left result into kwargs for right workflow
            combined_kwargs = {**kwargs, **left_result}

            # Execute right workflow with merged context
            result = self.composite_right.execute(**combined_kwargs)

            return result

        else:
            # Single workflow execution
            # Pre-processing
            if self.pre_callable and callable(self.pre_callable):
                self.pre_callable(kwargs)

            # Execute the workflow logic
            workflow_output = self._do_execute(**kwargs)

            # Handle output namespacing if specified
            if self.output_key:
                # Namespace workflow output under specified key
                result = {**kwargs, self.output_key: workflow_output}
            else:
                # Merge workflow output flat with input kwargs
                # If workflow_output is a dict, merge it; otherwise wrap in "result" key
                if isinstance(workflow_output, dict):
                    result = {**kwargs, **workflow_output}
                else:
                    result = {**kwargs, "result": workflow_output}

            # Post-processing
            if self.post_callable and callable(self.post_callable):
                self.post_callable(result)

            return result

    def _do_execute(self, **kwargs) -> DictParams:
        """Override this method to implement workflow logic.
        Args:
            **kwargs: Keyword arguments passed to the workflow

        Returns:
            A dictionary with the execution results.
        """
        return kwargs

    def call_agent(self, message: str | None = None, agent: AgentProtocol | None = None, **kwargs) -> DictParams:
        """Call the calling agent identified in the context, while providing our full id and type.
        Args:
            message: The message to call the calling agent with.
            **kwargs: The arguments to the call_agent method.

        Returns:
            A dictionary with the call_agent results.
        """

        @observable(name=f"{self.__class__.__name__}.call_agent({agent.agent_type if agent else 'None'})")
        def _do_call_agent(message: str | None = None, agent: AgentProtocol | None = None, **kwargs) -> DictParams:
            if agent:
                result = agent.query(caller_message=message, caller_id=self.object_id, caller_type=self.workflow_type, **kwargs)
            else:
                result = {"error": "Agent not found"}
            return result

        return _do_call_agent(message=message, agent=agent, **kwargs)

    # ============================================================================
    # WORKFLOW REGISTRY MANAGEMENT
    # ============================================================================

    def _get_registry(self):
        """Get the workflow registry."""
        return self._registry

    def _get_object_type(self) -> str:
        """Get the workflow type for registry."""
        return self.workflow_type

    def _get_capabilities(self) -> list[str]:
        """Get list of workflow capabilities."""
        capabilities = []
        # Add workflow type as capability
        capabilities.append(f"workflow_type_{self.workflow_type}")
        return capabilities

    def unregister_workflow(self) -> bool:
        """
        Unregister this workflow from the registry.

        Returns:
            True if successfully unregistered, False otherwise
        """
        return self._unregister_self()

    # ============================================================================
    # WORKFLOW IDENTITY
    # ============================================================================

    @property
    def workflow_id(self) -> str:
        """Get the workflow id."""
        return self._object_id

    @workflow_id.setter
    def workflow_id(self, value: str):
        """Set the workflow id."""
        self._object_id = value

    @property
    def public_description(self) -> str:
        """Get the public description of the workflow."""
        return super()._get_public_description()

    # ============================================================================
    # WORKFLOW COMPOSITION
    # ============================================================================

    def __or__(self, other: BaseWorkflow | Callable) -> BaseWorkflow:
        """Override the | operator to compose workflows.

        Allows composing workflows with other workflows or with callable functions.
        When a callable is provided, it is automatically wrapped in a CallableWorkflow
        that extracts parameters from the previous workflow's result.

        Args:
            other: Another workflow or a callable to compose with this one.
                  If a callable, its parameters will be extracted from the
                  "result" field of the previous workflow's output.

        Returns:
            A new composite workflow that executes both workflows in sequence

        Example:
            ```python
            # Compose workflows
            composed = workflow1 | workflow2

            # Compose workflow with callable
            def transform(data):
                return data.upper()

            composed = workflow | transform

            # Chain multiple compositions
            pipeline = workflow | process_data | format_output
            ```
        """
        # Import here to avoid circular dependency
        from dana.core.workflow.callable_workflow import CallableWorkflow

        # If other is a Callable (but not already a workflow), wrap it in CallableWorkflow
        if callable(other) and not isinstance(other, BaseWorkflow):
            other = CallableWorkflow(other)
        elif not isinstance(other, BaseWorkflow):
            raise TypeError(f"Can only compose workflows with other workflows or callables, got {type(other)}")

        # Create a composite workflow by setting left and right
        composite = BaseWorkflow(
            workflow_type=f"{self.workflow_type}|{other.workflow_type}", auto_register=False, composite_left=self, composite_right=other
        )
        return composite

    def __repr__(self) -> str:
        """Get string representation of the workflow."""
        if self.composite_left and self.composite_right:
            return f"<CompositeWorkflow '{self.workflow_type}'>"
        return f"<{self.__class__.__name__} workflow_type='{self.workflow_type}' workflow_id='{self.workflow_id}'>"
