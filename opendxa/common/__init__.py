"""Common Utilities and Shared Functionality for OpenDXA.

This module provides shared utilities and functionality used across the OpenDXA framework:

1. Configuration Management
   - ConfigManager for managing configuration
   - YAML configuration loading
   - Agent-specific configuration

2. Error Handling
   - Custom exceptions for different error types
   - Error hierarchy and categorization

3. Input/Output System
   - BaseIO for standardized I/O operations
   - IOFactory for creating I/O handlers

4. Utility Functions
   - LLM interaction analysis and visualization
   - Path and configuration utilities
   - Logging system

5. Mixins
   - Loggable for logging capabilities
   - ToolCallable for tool integration
   - Configurable for configuration support
   - Registerable for component registration

6. Graph Operations
   - Node and Edge data structures
   - Graph traversal strategies
   - Graph visualization

For detailed documentation, see:
- Common Utilities Documentation: https://github.com/aitomatic/opendxa/blob/main/opendxa/common/README.md

Example:
    >>> from opendxa.common import DXA_LOGGER, ConfigManager
    >>> DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG, console=True)
    >>> config = ConfigManager().load_config("agent_config.yaml")
"""

from opendxa.common.exceptions import (
    OpenDXAError,
    ConfigurationError,
    LLMError,
    NetworkError,
    WebSocketError,
    ReasoningError,
    AgentError,
    CommunicationError,
    ValidationError,
    StateError
)
from opendxa.common.io import (
    BaseIO,
    IOFactory
)
from opendxa.common.utils import (
    Misc,
    LLMInteractionAnalyzer,
    LLMInteractionVisualizer,
    DXALogger,
    DXA_LOGGER,
)
from opendxa.common.mixins import (
    Loggable,
    ToolCallable,
    Configurable,
    Registerable,
    Identifiable,
    Queryable,
)
from opendxa.common.graph import (
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
)
from opendxa.common.types import (
    BaseRequest,
    BaseResponse,
)

__all__ = [
    # Errors
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

    # IO
    'BaseIO',
    'IOFactory',

    # Utils
    'LLMInteractionAnalyzer',
    'LLMInteractionVisualizer',
    'DXALogger',
    'DXA_LOGGER',
    'Misc',

    # Mixins
    'Loggable',
    'ToolCallable',
    'Configurable',
    'Registerable',
    'Identifiable',
    'Queryable',

    # Graph
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

    # Types
    'BaseRequest',
    'BaseResponse',
]
