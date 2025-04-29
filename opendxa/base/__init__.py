"""Base Components for OpenDXA.

This module provides the foundational components and interfaces for the OpenDXA framework:

1. Capability System
   - BaseCapability for defining agent capabilities
   - Extensible capability framework

2. Execution System
   - BaseExecutor for execution management
   - RuntimeContext for managing execution state
   - ExecutionGraph for workflow representation
   - ExecutionNode and ExecutionEdge for workflow components
   - ExecutionSignal for inter-component communication
   - Objective management for goal tracking

3. State Management
   - BaseState for state management
   - WorldState for global state

4. Resource System
   - BaseResource for resource management
   - LLMResource for LLM integration
   - BaseResponse for standardized responses

These base components provide the core abstractions and interfaces that other
components build upon, ensuring consistency and extensibility across the framework.

Example:
    >>> from opendxa.base import RuntimeContext
    >>> from opendxa.base.state import AgentState, WorldState, ExecutionState
    >>> # LLMs are now typically managed by AgentRuntime, not passed directly to context
    >>> agent_state = AgentState()
    >>> world_state = WorldState()
    >>> execution_state = ExecutionState()
    >>> context = RuntimeContext(
    ...     agent_state=agent_state,
    ...     world_state=world_state,
    ...     execution_state=execution_state
    ...     # Optional state_handlers can be added here
    ... )
"""

from opendxa.base.capability import BaseCapability
from opendxa.base.execution import (
    BaseExecutor,
    RuntimeContext,
    ExecutionGraph,
    ExecutionNode,
    ExecutionNodeStatus,
    ExecutionNodeType,
    ExecutionSignal,
    ExecutionSignalType,
    Objective,
    ExecutionEdge,
    ExecutionFactory,
)
from opendxa.base.state import (
    BaseState,
    StateManager,
    AgentState,
    WorldState,
    ExecutionState,
)
from opendxa.base.resource import (
    BaseResource,
    ResourceError,
    ResourceUnavailableError,
    LLMResource,
    HumanResource,
    McpResource,
    StdioTransportParams,
    HttpTransportParams,
    BaseMcpService,
    McpEchoService,
    WoTResource,
    KBResource,
    MemoryResource,
    LTMemoryResource,
    STMemoryResource,
    PermMemoryResource,
)

__all__ = [
    # Capability
    'BaseCapability',

    # Execution
    'BaseExecutor',
    'RuntimeContext',
    'ExecutionGraph',
    'ExecutionNode',
    'ExecutionNodeStatus',
    'ExecutionNodeType',
    'ExecutionSignal',
    'ExecutionSignalType',
    'Objective',
    'ExecutionEdge',
    'ExecutionFactory',
    'StateManager',
    'BaseState',

    # Resource
    'BaseResource',
    'ResourceError',
    'ResourceUnavailableError',
    'LLMResource',
    'HumanResource',
    'McpResource',
    'StdioTransportParams',
    'HttpTransportParams',
    'BaseMcpService',
    'McpEchoService',
    'WoTResource',
    'KBResource',
    'MemoryResource',
    'LTMemoryResource',
    'STMemoryResource',
    'PermMemoryResource',

    # State
    'BaseState',
    'StateManager',
    'AgentState',
    'WorldState',
    'ExecutionState',
]