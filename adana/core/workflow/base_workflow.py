from collections.abc import Callable
from dataclasses import dataclass

from adana.common.base_wr import BaseWR
from adana.common.observable import observable
from adana.common.protocols import AgentProtocol, DictParams, WorkflowProtocol
from adana.core.global_registry import get_workflow_registry


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


class BaseWorkflow(BaseWR, WorkflowProtocol):
    """This docstring is the public description of the workflow.
    Here we place all the public descriptions an agent would need to know
    to use the workflow effectively. This will go into the WORKFLOW_DESCRIPTIONS
    section of the agent's system prompt.
    """

    def __init__(
        self,
        workflow_type: str | None = None,
        workflow_id: str | None = None,
        agent: AgentProtocol | None = None,
        auto_register: bool = True,
        registry=None,
        **kwargs,
    ):
        """
        Initialize the BaseWorkflow.

        Args:
            workflow_type: Type of workflow (e.g., 'research', 'data_processing')
            workflow_id: ID of the workflow (defaults to None)
            agent: The agent associated with this workflow
            auto_register: Whether to automatically register with the global registry
            registry: Specific registry to use (defaults to global registry)
            **kwargs: Additional arguments passed to parent classes
        """
        # Call super().__init__ to properly initialize all parent classes
        kwargs |= {
            "object_id": workflow_id,
            "agent": agent,
        }
        super().__init__(**kwargs)
        self.workflow_type = workflow_type or self.__class__.__name__

        # List of known resources that we can use or refer to in the workflow
        self._resources = kwargs.get("resources") or {}

        # Handle workflow registration
        self._registry = registry or get_workflow_registry()
        if auto_register:
            self._register_self()

    def execute(self, **kwargs) -> DictParams:
        """Invoke the workflow.
        Args:
            **kwargs: The arguments to the invoke method.

        Returns:
            A dictionary with the invoke results.
        """
        return {}

    def call_agent(self, message: str | None = None, **kwargs) -> DictParams:
        """Call our calling agent, while providing our full id and type.
        Args:
            message: The message to call the agent with.
            **kwargs: The arguments to the call_agent method.

        Returns:
            A dictionary with the call_agent results.
        """

        @observable(name=f"{self.__class__.__name__}.call_agent({self.agent.agent_type if self.agent else 'None'})")
        def _do_call_agent(message: str | None = None, **kwargs) -> DictParams:
            if self.agent:
                result = self.agent.query(caller_message=message, caller_id=self.object_id, caller_type=self.workflow_type, **kwargs)
            else:
                result = {"error": "Agent not found"}
            return result

        return _do_call_agent(message=message, **kwargs)

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

    def __repr__(self) -> str:
        """Get string representation of the workflow."""
        return f"<{self.__class__.__name__} workflow_type='{self.workflow_type}' workflow_id='{self.workflow_id}'>"
