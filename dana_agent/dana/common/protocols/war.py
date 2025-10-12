"""
Protocols for WAR (Workflow, Agent, Resource) framework.
"""

from collections.abc import Sequence
from typing import Protocol

from .types import DictParams


CALL_RESOURCE = "call_resource"
CALL_AGENT = "call_agent"
EXECUTE_WORKFLOW = "execute_workflow"


class WARProtocol(Protocol):
    """Protocol for WAR objects."""

    def query(self, **kwargs) -> DictParams:
        """Query the data source."""
        ...

    @property
    def public_description(self) -> str:
        """Get the public description of the object."""
        ...


# Tool use decorator constant
IS_TOOL_USE = "_is_tool_use"


def tool_use(func):
    """@tool_use decorator to mark methods as tool-usable by agents."""
    func.__dict__[IS_TOOL_USE] = True
    return func


class WorkflowProtocol(WARProtocol):
    """Protocol for workflows."""

    @property
    def agent(self) -> "AgentProtocol | None":
        """Get the agent of the workflow."""
        ...

    @agent.setter
    def agent(self, value: "AgentProtocol | None"):
        """Set the agent of the workflow."""
        ...


class ResourceProtocol(WARProtocol):
    """Protocol for resources."""

    ...


class AgentProtocol(WARProtocol):
    """Protocol for agents."""

    @property
    def system_prompt(self) -> str:
        """Get the system prompt of the agent."""
        ...

    @property
    def private_identity(self) -> str:
        """Get the private identity of the agent."""
        ...

    @property
    def available_workflows(self) -> Sequence[WorkflowProtocol]:
        """Get the available workflows of the agent."""
        ...

    @property
    def available_agents(self) -> Sequence["AgentProtocol"]:
        """Get the available agents of the agent."""
        ...

    @property
    def available_resources(self) -> Sequence[ResourceProtocol]:
        """Get the available resources of the agent."""
        ...


class STARAgentProtococol(AgentProtocol):
    """Protocol for See-Think-Act-Reflect agents."""

    def _see(self, trace_inputs: DictParams) -> DictParams:
        """See the inputs and produce percepts.
        Args:
            trace_inputs (DictParams): INPUT: any new user/agent inputs

        Returns:
            - trace_percepts (DictParams): the percepts produced by this SEE phase.
        """
        ...

    def _think(self, trace_percepts: DictParams) -> DictParams:
        """Think about the percepts and produce thoughts.
        Args:
            trace_percepts (DictParams): INPUT: the percepts produced by this SEE phase.

        Returns:
            - trace_thoughts (DictParams): the thoughts produced by this THINK phase.
        """
        ...

    def _act(self, trace_thoughts: DictParams) -> DictParams:
        """Act on the thoughts and produce outputs.
        Args:
            trace_thoughts (DictParams): INPUT: the thoughts produced by this THINK phase.

        Returns:
            - trace_outputs (DictParams): the outputs produced by this ACT phase.
        """
        ...

    def _reflect(self, trace_outputs: DictParams) -> DictParams:
        """Reflect on the outputs for learning.
        Args:
            trace_outputs (DictParams): INPUT: the outputs produced by this ACT phase.

        Returns:
            - trace_learning (DictParams): the learning produced by this REFLECT phase.
        """
        ...
