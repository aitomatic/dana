"""Domain-Expert Agent (OpenDXA) Framework.

OpenDXA is an intelligent agent architecture that combines domain expertise with
LLM-powered reasoning. It provides core components for building agents, managing
resources, handling common tasks, and defining agent capabilities.

Key Modules:
- `opendxa.agent`: Core agent logic, factories, and agent-specific resources.
- `opendxa.common`: Shared utilities, types, exceptions, mixins, base classes,
  graph operations, I/O, and common resources.

Usage:
    The package exports key symbols from its submodules for convenient access:
    >>> from opendxa import Agent, LLMResource, BaseCapability, DirectedGraph, ConfigLoader # etc.

    Specific components can also be imported directly:
    >>> from opendxa.agent import Agent
    >>> from opendxa.common import ConfigLoader

Refer to the README files in the `agent` and `common` subdirectories for more
detailed documentation on specific components.
"""

from dotenv import load_dotenv

# Explicitly import all public symbols from submodules
# This makes them available in the top-level namespace
from opendxa.agent import (
    Agent,
    AgentFactory,
    AgentResource,
    AgentResponse,
    CapabilityFactory,
    DomainExpertise,
    ExpertResource,
    ExpertResponse,
    MemoryCapability,
    ResourceFactory,
)
from opendxa.common import (
    DXA_LOGGER,
    AgentError,
    # Capability
    BaseCapability,
    BaseDBModel,
    # DB
    BaseDBStorage,
    # IO
    BaseIO,
    BaseMcpService,
    BaseRequest,
    # Resource
    BaseResource,
    BaseResponse,
    BreadthFirstTraversal,
    Capable,
    CommunicationError,
    # Config
    ConfigLoader,
    Configurable,
    ConfigurationError,
    ConsoleIO,
    Cursor,
    DepthFirstTraversal,
    DirectedGraph,
    DXAContextError,
    DXALogger,
    DXAMemoryError,
    Edge,
    GraphFactory,
    GraphSerializer,
    GraphVisualizer,
    HttpTransportParams,
    HumanResource,
    Identifiable,
    IOFactory,
    # Types
    JsonPrimitive,
    JsonType,
    KBResource,
    KnowledgeDBModel,
    KnowledgeDBStorage,
    LLMError,
    LLMInteractionAnalyzer,
    LLMInteractionVisualizer,
    LLMResource,
    # Mixins
    Loggable,
    LTMemoryResource,
    McpEchoService,
    McpResource,
    McpToolFormat,
    MemoryDBModel,
    MemoryDBStorage,
    MemoryResource,
    # Utils
    Misc,
    NetworkError,
    # Graph
    Node,
    NodeType,
    OpenAIFunctionCall,
    OpenAIToolFormat,
    # Exceptions
    OpenDXAError,
    PermMemoryResource,
    Queryable,
    ReasoningError,
    Registerable,
    ResourceError,
    ResourceUnavailableError,
    StateError,
    StdioTransportParams,
    STMemoryResource,
    ToolCallable,
    ToolFormat,
    TopologicalTraversal,
    TraversalStrategy,
    ValidationError,
    WebSocketError,
    WebSocketIO,
    WoTResource,
)

# Load environment variables AFTER imports
load_dotenv()

# Define __all__ manually using string literals, pre-sorted
__all__ = [
    "Agent",
    "AgentError",
    "AgentFactory",
    "AgentResource",
    "AgentResponse",
    "BaseCapability",
    "BaseDBModel",
    "BaseDBStorage",
    "BaseIO",
    "BaseMcpService",
    "BaseRequest",
    "BaseResponse",
    "BaseResource",
    "BreadthFirstTraversal",
    "Capable",
    "CapabilityFactory",
    "CommunicationError",
    "ConfigLoader",
    "Configurable",
    "ConfigurationError",
    "ConsoleIO",
    "Cursor",
    "DXAContextError",
    "DXALogger",
    "DXAMemoryError",
    "DXA_LOGGER",
    "DepthFirstTraversal",
    "DirectedGraph",
    "DomainExpertise",
    "Edge",
    "ExpertResource",
    "ExpertResponse",
    "GraphFactory",
    "GraphSerializer",
    "GraphVisualizer",
    "HttpTransportParams",
    "HumanResource",
    "IOFactory",
    "Identifiable",
    "JsonPrimitive",
    "JsonType",
    "KBResource",
    "KnowledgeDBModel",
    "KnowledgeDBStorage",
    "LLMError",
    "LLMInteractionAnalyzer",
    "LLMInteractionVisualizer",
    "LLMResource",
    "LTMemoryResource",
    "Loggable",
    "McpEchoService",
    "McpResource",
    "McpToolFormat",
    "MemoryCapability",
    "MemoryDBModel",
    "MemoryDBStorage",
    "MemoryResource",
    "Misc",
    "NetworkError",
    "Node",
    "NodeType",
    "OpenAIFunctionCall",
    "OpenAIToolFormat",
    "OpenDXAError",
    "PermMemoryResource",
    "Queryable",
    "ReasoningError",
    "Registerable",
    "ResourceError",
    "ResourceFactory",
    "ResourceUnavailableError",
    "STMemoryResource",
    "StateError",
    "StdioTransportParams",
    "ToolCallable",
    "ToolFormat",
    "TopologicalTraversal",
    "TraversalStrategy",
    "ValidationError",
    "WebSocketError",
    "WebSocketIO",
    "WoTResource",
]

