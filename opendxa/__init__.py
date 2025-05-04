"""Domain-Expert Agent (OpenDXA) Framework.

OpenDXA is an intelligent agent architecture that combines domain expertise with LLM-powered reasoning
through a unique three-layer graph architecture:

1. Planning Layer (WHAT) - Breaks down workflows into concrete, executable steps
2. Reasoning Layer (HOW) - Executes each step using appropriate thinking patterns

The framework enables building intelligent agents with domain expertise, powered by Large Language Models (LLMs).
It provides a clean separation of concerns and allows for progressive complexity, starting from simple
implementations and scaling to complex domain-specific tasks.

Documentation:
    For detailed documentation, installation instructions, and examples, see:
    - Project README: https://github.com/aitomatic/opendxa/blob/main/opendxa/README.md
    - Agent Documentation: https://github.com/aitomatic/opendxa/blob/main/opendxa/agent/README.md
    - Execution Documentation: https://github.com/aitomatic/opendxa/blob/main/opendxa/execution/README.md

Usage:
    The package is designed for simple, intuitive imports:
    >>> from opendxa import Agent, LLMResource, Pipeline  # etc.

    Each component can also be imported directly from its module:
    >>> from opendxa.agent import Agent
    >>> from opendxa.agent.resource import LLMResource

Import Pattern:
    This project uses a simple import pattern to make the package easy to use.
    The pattern follows these rules:

    1. Each module has an __init__.py that:
       - Imports symbols from its own files
       - Imports symbols from its submodules
       - Lists all symbols in __all__

    2. No cross-module imports - modules can only import from:
       - Their own files
       - Their submodules

    3. The top-level __init__.py is the only place where symbols from different
       modules are combined

    Implementation is done from the bottom up:
    1. Start with leaf modules (no submodules)
    2. Work up the tree, importing and re-exporting at each level
    3. Finally, combine everything at the top level
"""

from dotenv import load_dotenv

# Load environment variables when package is imported
load_dotenv()

from opendxa.common import (
    # Exceptions
    OpenDXAError,
    ConfigurationError,
    LLMError,
    NetworkError,
    WebSocketError,
    ReasoningError,
    AgentError,
    CommunicationError,
    ValidationError,
    StateError,
    # IO
    BaseIO,
    IOFactory,
    # Utils
    Misc,
    LLMInteractionAnalyzer,
    LLMInteractionVisualizer,
    DXALogger,
    DXA_LOGGER,
    # Mixins
    Loggable,
    ToolCallable,
    Configurable,
    Registerable,
    Identifiable,
    Queryable,
    # Graph
    Node,
    Edge,
    NodeType,
    DirectedGraph,
    Cursor,
    TraversalStrategy,
    BreadthFirstTraversal,
    DepthFirstTraversal, 
    TopologicalTraversal,
    GraphVisualizer,
    # Types
    BaseRequest,
    BaseResponse,

    # Capability
    BaseCapability,
    Capable,

    # Resource
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
)

"""
from opendxa.agent import (
    Agent,
    AgentFactory,
    AgentResource,
    AgentResponse,
    ExpertResource,
    ResourceFactory,
)
"""

from opendxa.config import (
    AgentConfig,
)

__all__ = [
    # Common
    'OpenDXAError',
    'ConfigurationError',
    'LLMError',
    'NetworkError',
    'WebSocketError',
    'ReasoningError',
    'AgentError',
    'CommunicationError',
    'ValidationError',
    'StateError',
    'BaseIO',
    'IOFactory',
    'LLMInteractionAnalyzer',
    'LLMInteractionVisualizer',
    'DXALogger',
    'DXA_LOGGER',
    'Misc',
    'Loggable',
    'ToolCallable',
    'Configurable',
    'Registerable',
    'Identifiable',
    'Queryable',
    'Node',
    'Edge',
    'NodeType',
    'DirectedGraph',
    'Cursor',
    'TraversalStrategy',
    'BreadthFirstTraversal',
    'DepthFirstTraversal', 
    'TopologicalTraversal',
    'GraphVisualizer',
    'BaseRequest',
    'BaseResponse',
    'McpEchoService',
    'WoTResource',

    # Capability
    'BaseCapability',
    'Capable',

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

    # Config
    'AgentConfig',
]