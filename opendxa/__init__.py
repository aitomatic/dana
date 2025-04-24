"""Domain-Expert Agent (OpenDXA) Framework.

OpenDXA is an intelligent agent architecture that combines domain expertise with LLM-powered reasoning
through a unique three-layer graph architecture:

1. Planning Layer (WHAT) - Breaks down workflows into concrete, executable steps
2. Reasoning Layer (HOW) - Executes each step using appropriate thinking patterns

The framework enables building intelligent agents with domain expertise, powered by Large Language Models (LLMs).
It provides a clean separation of concerns and allows for progressive complexity, starting from simple
implementations and scaling to complex domain-specific tasks.

For detailed documentation, installation instructions, and examples, see:
- Project README: https://github.com/aitomatic/opendxa/blob/main/opendxa/README.md
- Agent Documentation: https://github.com/aitomatic/opendxa/blob/main/opendxa/agent/README.md
- Execution Documentation: https://github.com/aitomatic/opendxa/blob/main/opendxa/execution/README.md

Example:
    >>> from opendxa.agent import Agent
    >>> from opendxa.agent.resource import LLMResource
    >>> answer = Agent().ask("What is quantum computing?")
"""

from opendxa.common import (
    AgentError,
    BaseIO,
    BreadthFirstTraversal,
    CommunicationError,
    Configurable,
    ConfigurationError,
    Cursor,
    DXA_LOGGER,
    DepthFirstTraversal,
    DirectedGraph,
    Edge,
    GraphVisualizer,
    IOFactory,
    Identifiable,
    LLMError,
    LLMInteractionAnalyzer,
    LLMInteractionVisualizer,
    Loggable,
    NetworkError,
    Node,
    NodeType,
    OpenDXAError,
    QueryResponse,
    Queryable,
    ReasoningError,
    Registerable,
    StateError,
    ToolCallable,
    TopologicalTraversal,
    TraversalStrategy,
    ValidationError,
    WebSocketError,
    get_base_path,
    get_class_by_name,
    get_config_path,
    load_yaml_config,
    safe_asyncio_run,
)

from opendxa.base import (
    BaseCapability,
    BaseExecutor,
    BaseResource,
    BaseState,
    ExecutionContext,
    ExecutionGraph,
    ExecutionNode,
    ExecutionEdge,
    ExecutionSignal,
    ExecutionSignalType,
    ExecutionState,
    ExecutionFactory,
    ExecutionNodeStatus,
    Objective,
    ObjectiveStatus,
    LLMResource,
    ResourceResponse,
    WorldState,
)

from opendxa.base.resource import (
    KBResource,
    MemoryResource,
    LTMemoryResource,
    STMemoryResource,
    PermMemoryResource,
)

from opendxa.base.db import (
    BaseDBModel,
    KnowledgeDBModel,
    MemoryDBModel,
    BaseDBStorage,
    SqlDBStorage,
    VectorDBStorage,
)

from opendxa.execution import (
    AgentRuntime,
    AgentState,
    Pipeline,
    PipelineContext,
    PipelineExecutor,
    PipelineFactory,
    PipelineNode,
    PipelineStrategy,
    Plan,
    Planner,
    PlanFactory,
    PlanStrategy,
    Reasoning,
    Reasoner,
    ReasoningFactory,
    ReasoningStrategy,
)

from opendxa.agent import (
    Agent,
    AgentFactory,
    AgentResource,
    AgentResponse,
    ExpertResource,
    ResourceFactory,
)

__all__ = [
    # Common
    'AgentError',
    'BaseIO',
    'BreadthFirstTraversal',
    'CommunicationError',
    'Configurable',
    'ConfigurationError',
    'Cursor',
    'DXA_LOGGER',
    'DepthFirstTraversal',
    'DirectedGraph',
    'Edge',
    'GraphVisualizer',
    'IOFactory',
    'Identifiable',
    'LLMError',
    'LLMInteractionAnalyzer',
    'LLMInteractionVisualizer',
    'Loggable',
    'NetworkError',
    'Node',
    'NodeType',
    'OpenDXAError',
    'QueryResponse',
    'Queryable',
    'ReasoningError',
    'Registerable',
    'StateError',
    'ToolCallable',
    'TopologicalTraversal',
    'TraversalStrategy',
    'ValidationError',
    'WebSocketError',
    'get_base_path',
    'get_class_by_name',
    'get_config_path',
    'load_yaml_config',
    'safe_asyncio_run',
    # Base
    'BaseCapability',
    'BaseExecutor',
    'BaseResource',
    'BaseState',
    'ExecutionContext',
    'ExecutionGraph',
    'ExecutionNode',
    'ExecutionEdge',
    'ExecutionSignal',
    'ExecutionSignalType',
    'ExecutionState',
    'ExecutionFactory',
    'ExecutionNodeStatus',
    'Objective',
    'ObjectiveStatus',
    'LLMResource',
    'ResourceResponse',
    'WorldState',

    # Base Resource
    'KBResource',
    'MemoryResource',
    'LTMemoryResource',
    'STMemoryResource',
    'PermMemoryResource',

    # Base DB
    'BaseDBModel',
    'KnowledgeDBModel',
    'MemoryDBModel',
    'BaseDBStorage',
    'SqlDBStorage',
    'VectorDBStorage',

    # Execution
    'AgentRuntime',
    'AgentState',
    'Pipeline',
    'PipelineContext',
    'PipelineExecutor',
    'PipelineFactory',
    'PipelineNode',
    'PipelineStrategy',
    'Plan',
    'Planner',
    'PlanFactory',
    'PlanStrategy',
    'Reasoning',
    'Reasoner',
    'ReasoningFactory',
    'ReasoningStrategy',

    # Agent
    'Agent',
    'AgentFactory',
    'AgentResource',
    'AgentResponse',
    'ExpertResource',
    'ResourceFactory',
]
