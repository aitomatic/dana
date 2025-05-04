"""Common Utilities and Shared Functionality for OpenDXA.

This module aggregates common components used across the OpenDXA framework,
including:

- Exceptions: Custom error types for DXA.
- Types: Core data structures like BaseRequest, BaseResponse.
- Capability: Base classes for agent capabilities (BaseCapability, Capable).
- Config: Configuration loading (ConfigLoader).
- DB: Database models and storage abstractions (BaseDBModel, BaseDBStorage, etc.).
- Graph: Graph data structures and algorithms (DirectedGraph, TraversalStrategy).
- IO: Input/Output handling (BaseIO, ConsoleIO, WebSocketIO).
- Mixins: Reusable functionality (Loggable, ToolCallable, Configurable, etc.).
- Resource: Base classes and implementations for resources (BaseResource, LLMResource, etc.).
- Utils: Logging, analysis, visualization, and miscellaneous utilities.

Symbols listed in `__all__` are considered the public API of this common module.

For detailed documentation on specific components, refer to the README files
within the respective subdirectories (e.g., `opendxa/common/graph/README.md`).

Example:
    >>> from opendxa.common import DXA_LOGGER, ConfigManager
    >>> DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG, console=True)
    >>> config = ConfigManager().load_config("agent_config.yaml")
"""

from opendxa.common.capability import (
    BaseCapability,
    Capable,
)
from opendxa.common.config import (
    ConfigLoader,
)
from opendxa.common.db import (
    BaseDBModel,
    BaseDBStorage,
    KnowledgeDBModel,
    KnowledgeDBStorage,
    MemoryDBModel,
    MemoryDBStorage,
)
from opendxa.common.exceptions import (
    AgentError,
    CommunicationError,
    ConfigurationError,
    DXAContextError,
    DXAMemoryError,
    LLMError,
    NetworkError,
    OpenDXAError,
    ReasoningError,
    ResourceError,
    StateError,
    ValidationError,
    WebSocketError,
)
from opendxa.common.graph import (
    BreadthFirstTraversal,
    Cursor,
    DepthFirstTraversal,
    DirectedGraph,
    Edge,
    GraphFactory,
    GraphSerializer,
    GraphVisualizer,
    Node,
    NodeType,
    TopologicalTraversal,
    TraversalStrategy,
)
from opendxa.common.io import (
    BaseIO,
    ConsoleIO,
    IOFactory,
    WebSocketIO,
)
from opendxa.common.mixins import (
    Configurable,
    Identifiable,
    Loggable,
    McpToolFormat,
    OpenAIFunctionCall,
    OpenAIToolFormat,
    Queryable,
    Registerable,
    ToolCallable,
    ToolFormat,
)
from opendxa.common.resource import (
    BaseMcpService,
    BaseResource,
    HttpTransportParams,
    HumanResource,
    KBResource,
    LLMResource,
    LTMemoryResource,
    McpEchoService,
    McpResource,
    MemoryResource,
    PermMemoryResource,
    ResourceUnavailableError,
    StdioTransportParams,
    STMemoryResource,
    WoTResource,
)
from opendxa.common.types import (
    BaseRequest,
    BaseResponse,
    JsonPrimitive,
    JsonType,
)
from opendxa.common.utils import (
    DXA_LOGGER,
    DXALogger,
    LLMInteractionAnalyzer,
    LLMInteractionVisualizer,
    Misc,
)

__all__ = [
    # Exceptions (from exceptions.py)
    "OpenDXAError",
    "ConfigurationError",
    "LLMError",
    "ResourceError",
    "NetworkError",
    "WebSocketError",
    "ReasoningError",
    "AgentError",
    "CommunicationError",
    "ValidationError",
    "StateError",
    "DXAMemoryError",
    "DXAContextError",
    # Types (from types.py)
    "JsonPrimitive",
    "JsonType",
    "BaseRequest",
    "BaseResponse",
    # Capability (from capability/)
    "BaseCapability",
    "Capable",
    # Config (from config/)
    "ConfigLoader",
    # DB (from db/)
    "BaseDBStorage",
    "BaseDBModel",
    "KnowledgeDBModel",
    "MemoryDBModel",
    "KnowledgeDBStorage",
    "MemoryDBStorage",
    # Graph (from graph/)
    "Node",
    "Edge",
    "NodeType",
    "DirectedGraph",
    "Cursor",
    "TraversalStrategy",
    "BreadthFirstTraversal",
    "DepthFirstTraversal",
    "TopologicalTraversal",
    "GraphVisualizer",
    "GraphSerializer",
    "GraphFactory",
    # IO (from io/)
    "BaseIO",
    "IOFactory",
    "ConsoleIO",
    "WebSocketIO",
    # Mixins (from mixins/)
    "Loggable",
    "ToolCallable",
    "OpenAIFunctionCall",
    "ToolFormat",
    "McpToolFormat",
    "OpenAIToolFormat",
    "Configurable",
    "Registerable",
    "Identifiable",
    "Queryable",
    # Resource (from resource/)
    "BaseResource",
    "ResourceUnavailableError",
    "LLMResource",
    "HumanResource",
    "McpResource",
    "StdioTransportParams",
    "HttpTransportParams",
    "BaseMcpService",
    "McpEchoService",
    "WoTResource",
    "KBResource",
    "MemoryResource",
    "LTMemoryResource",
    "STMemoryResource",
    "PermMemoryResource",
    # Utils (from utils/)
    "Misc",
    "LLMInteractionAnalyzer",
    "LLMInteractionVisualizer",
    "DXALogger",
    "DXA_LOGGER",
]
