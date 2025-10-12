from collections.abc import Callable
from dataclasses import dataclass

from dana_agent.common.base_wa import BaseWA
from dana_agent.common.observable import observable
from dana_agent.common.protocols import AgentProtocol, DictParams, WorkflowProtocol
from dana_agent.common.protocols.war import tool_use
from dana_agent.core.global_registry import get_workflow_registry


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
            **kwargs: Additional arguments passed to parent classes
        """
        # Call super().__init__ to properly initialize all parent classes
        super().__init__(object_id=workflow_id, **kwargs)
        self.workflow_type = workflow_type or self.__class__.__name__

        # Compile declarative transformation to callables
        if args_transform:
            if pre_callable or post_callable:
                raise ValueError("Cannot specify 'transform' with 'pre_callable' or 'post_callable'")

            # Parse the transform string: "input_mappings -> output_name"
            if "->" in args_transform:
                input_part, output_part = args_transform.split("->", 1)
                input_part = input_part.strip()
                output_part = output_part.strip()
            else:
                input_part = args_transform.strip()
                output_part = "result"

            # Compile input mappings if present
            if input_part:
                pre_callable = self._compile_input_mapping(input_part)

            # Compile output mapping if not default
            if output_part and output_part != "result":
                post_callable = self._compile_output_mapping(output_part)

        self.pre_callable = pre_callable
        self.post_callable = post_callable

        # Handle workflow registration
        self._registry = registry or get_workflow_registry()
        if auto_register:
            self._register_self()

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
                    value = BaseWorkflow._get_nested_value(data, path)
                    if value is not None:
                        break

                # Update with the found value (or None if all paths failed)
                data[target_key] = value if value is not None else ""

        return mapper

    @staticmethod
    def _compile_output_mapping(output_key: str) -> Callable[[DictParams], None]:
        """
        Compile an output mapping specification to a callable.

        Args:
            output_key: The key name to use for the output (e.g., "search_result")

        Returns:
            A callable that renames "result" to the specified key
        """

        def mapper(data: DictParams) -> None:
            """Rename 'result' key to output_key."""
            if "result" in data:
                data[output_key] = data.pop("result")

        return mapper

    @tool_use
    @observable
    def execute(self, **kwargs) -> DictParams:
        """Invoke the workflow with pre/post-processing.
        Args:
            **kwargs: Keyword arguments passed to the workflow

        Returns: A DictParams with the invoke results.
            result: The result (DictParams or str) of the workflow.
        """
        # Check if this is a composite workflow
        if hasattr(self, "left") and hasattr(self, "right"):
            # Execute left workflow
            left_result: DictParams = self.left.execute(**kwargs)

            # Merge results into kwargs for right workflow
            combined_kwargs = {**kwargs, **left_result}

            # Execute right workflow
            right_result: DictParams = self.right.execute(**combined_kwargs)

            # Return combined results
            result = {**left_result, **right_result}

        else:
            # Single workflow execution
            # Pre-processing
            if self.pre_callable and callable(self.pre_callable):
                self.pre_callable(kwargs)

            # Execute the workflow logic
            result = {"result": self._do_execute(**kwargs)}

            # Carry over any additional kwargs
            result = {**kwargs, **result}

            # Post-processing
            if self.post_callable and callable(self.post_callable):
                self.post_callable(result)

        # Always return a dictionary with the "result" key
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

    def __or__(self, other: "BaseWorkflow") -> "BaseWorkflow":
        """Override the | operator to compose workflows.

        Args:
            other: Another workflow to compose with this one

        Returns:
            A new composite workflow that executes both workflows in sequence
        """
        if not isinstance(other, BaseWorkflow):
            raise TypeError(f"Can only compose workflows with other workflows, got {type(other)}")

        # Create a composite workflow by setting left and right
        composite = BaseWorkflow(workflow_type=f"{self.workflow_type}|{other.workflow_type}", auto_register=False, agent=self.agent)
        composite.left = self
        composite.right = other
        return composite

    def __repr__(self) -> str:
        """Get string representation of the workflow."""
        if hasattr(self, "left") and hasattr(self, "right"):
            return f"<CompositeWorkflow '{self.workflow_type}'>"
        return f"<{self.__class__.__name__} workflow_type='{self.workflow_type}' workflow_id='{self.workflow_id}'>"
