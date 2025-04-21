"""Base Components for OpenDXA.

This module provides the foundational components and interfaces for the OpenDXA framework:

1. Capability System
   - BaseCapability for defining agent capabilities
   - Extensible capability framework

2. Execution System
   - BaseExecutor for execution management
   - ExecutionContext for managing execution state
   - ExecutionGraph for workflow representation
   - ExecutionNode and ExecutionEdge for workflow components
   - ExecutionSignal for inter-component communication
   - Objective management for goal tracking

3. State Management
   - BaseState for state management
   - WorldState for global state
   - ExecutionState for execution-specific state

4. Resource System
   - BaseResource for resource management
   - LLMResource for LLM integration
   - ResourceResponse for standardized responses

These base components provide the core abstractions and interfaces that other
components build upon, ensuring consistency and extensibility across the framework.

Example:
    >>> from opendxa.base import BaseCapability, ExecutionContext
    >>> from opendxa.base.resource import LLMResource
    >>> context = ExecutionContext(
    ...     reasoning_llm=LLMResource(),
    ...     planning_llm=LLMResource(),
    ...     workflow_llm=LLMResource()
    ... )
"""

from opendxa.base.capability import BaseCapability

from opendxa.base.execution import (
    BaseExecutor,
    ExecutionContext,
    ExecutionGraph,
    ExecutionNode,
    ExecutionEdge,
    ExecutionSignal,
    ExecutionSignalType,
    ExecutionFactory,
    ExecutionNodeStatus,
    Objective,
    ObjectiveStatus,
)

from opendxa.base.state import (
    BaseState,
    WorldState,
    ExecutionState,
)

from opendxa.base.resource import (
    BaseResource,
    LLMResource,
    ResourceResponse,
    QueryResponse,
)

from opendxa.base.db import (
    BaseDBModel,
    KnowledgeDBModel,
    MemoryDBModel,
    BaseDBStorage,
    SqlDBStorage,
    VectorDBStorage
)

__all__ = [
    "BaseCapability",
    "BaseExecutor",
    "BaseState",
    "WorldState",
    "ExecutionState",
    "ExecutionContext",
    "ExecutionGraph",
    "ExecutionNode",
    "ExecutionEdge",
    "ExecutionSignal",
    "ExecutionSignalType",
    "ExecutionFactory",
    "ExecutionNodeStatus",
    "Objective",
    "ObjectiveStatus",
    "BaseResource",
    "LLMResource",
    "ResourceResponse",
    "QueryResponse",
    # Database
    'BaseDBModel',
    'KnowledgeDBModel',
    'MemoryDBModel',
    'BaseDBStorage',
    'SqlDBStorage',
    'VectorDBStorage',
]