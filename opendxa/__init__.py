"""Domain-Expert Agent (OpenDXA) Framework.

OpenDXA is an intelligent agent architecture that combines domain expertise with LLM-powered reasoning
through a unique three-layer graph architecture:

1. Workflow Layer (WHY) - Defines what agents can do, from simple Q&A to complex research patterns
2. Planning Layer (WHAT) - Breaks down workflows into concrete, executable steps
3. Reasoning Layer (HOW) - Executes each step using appropriate thinking patterns

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
    ConfigManager,
    ConfigurationError,
    Cursor,
    DXA_LOGGER,
    DepthFirstTraversal,
    DirectedGraph,
    Edge,
    GraphVisualizer,
    IOFactory,
    LLMError,
    LLMInteractionAnalyzer,
    LLMInteractionVisualizer,
    Loggable,
    NetworkError,
    Node,
    NodeType,
    OpenDXAError,
    ReasoningError,
    StateError,
    TopologicalTraversal,
    TraversalStrategy,
    ToolCallable,
    ValidationError,
    WebSocketError,
    get_base_path,
    get_class_by_name,
    get_config_path,
    load_agent_config,
    load_yaml_config,
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

from opendxa.execution import (
    OptimalWorkflowExecutor,
    Pipeline,
    PipelineContext,
    PipelineExecutor,
    PipelineFactory,
    PipelineNode,
    PipelineStrategy,
    Plan,
    PlanExecutor,
    PlanFactory,
    PlanStrategy,
    Reasoning,
    ReasoningExecutor,
    ReasoningFactory,
    ReasoningStrategy,
    Workflow,
    WorkflowExecutor,
    WorkflowFactory,
    WorkflowStrategy,
)

from opendxa.agent import (
    Agent,
    AgentFactory,
    AgentResource,
    AgentResponse,
    AgentRuntime,
    AgentState,
    ExpertResource,
    ResourceFactory,
)

__all__ = [
    # Common
    'AgentError',
    'BaseIO',
    'BreadthFirstTraversal',
    'CommunicationError',
    'ConfigManager',
    'ConfigurationError',
    'Cursor',
    'DXA_LOGGER',
    'DepthFirstTraversal',
    'DirectedGraph',
    'Edge',
    'GraphVisualizer',
    'IOFactory',
    'LLMError',
    'LLMInteractionAnalyzer',
    'LLMInteractionVisualizer',
    'Loggable',
    'NetworkError',
    'Node',
    'NodeType',
    'OpenDXAError',
    'ReasoningError',
    'StateError',
    'TopologicalTraversal',
    'TraversalStrategy',
    'ToolCallable',
    'ValidationError',
    'WebSocketError',
    'get_base_path',
    'get_class_by_name',
    'get_config_path',
    'load_agent_config',
    'load_yaml_config',

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

    # Execution
    'OptimalWorkflowExecutor',
    'Pipeline',
    'PipelineContext',
    'PipelineExecutor',
    'PipelineFactory',
    'PipelineNode',
    'PipelineStrategy',
    'Plan',
    'PlanExecutor',
    'PlanFactory',
    'PlanStrategy',
    'Reasoning',
    'ReasoningExecutor',
    'ReasoningFactory',
    'ReasoningStrategy',
    'Workflow',
    'WorkflowExecutor',
    'WorkflowFactory',
    'WorkflowStrategy',

    # Agent
    'Agent',
    'AgentFactory',
    'AgentResource',
    'AgentResponse',
    'AgentRuntime',
    'AgentState',
    'ExpertResource',
    'ResourceFactory',
]