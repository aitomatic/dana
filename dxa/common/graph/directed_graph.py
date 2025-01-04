"""Base directed graph implementation."""

from typing import Dict, List, Optional, Iterator, Any, Union, TextIO, TYPE_CHECKING
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from ..utils import get_class_by_name
if TYPE_CHECKING:
    from .visualizer import GraphVisualizer
    from .serializer import GraphSerializer
    from .traversal import (
        Cursor,
        TraversalStrategy,
        TopologicalTraversal
    )
_CURSOR_CLASS_NAME = "dxa.common.graph.traversal.Cursor"

class NodeType(Enum):
    """Base node types for all graphs."""
    NODE = "NODE"
    START = "START" 
    END = "END"
    TASK = "TASK"
    CONDITION = "CONDITION"
    FORK = "FORK"
    JOIN = "JOIN"

@dataclass
class Node:
    """Base graph node."""
    node_id: str
    node_type: NodeType = NodeType.NODE
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Make node hashable by id."""
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        """Nodes are equal if they have the same id."""
        if not isinstance(other, Node):
            return NotImplemented
        return self.node_id == other.node_id

@dataclass
class Edge:
    """Base graph edge."""
    source: str  # Source node ID
    target: str  # Target node ID
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Make edge hashable by source/target pair."""
        return hash((self.source, self.target))

    def __eq__(self, other: object) -> bool:
        """Edges are equal if they have same source/target."""
        if not isinstance(other, Edge):
            return NotImplemented
        return self.source == other.source and self.target == other.target
    
class DirectedGraph:
    """Pure directed graph implementation."""
    def __init__(self):
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []
        self._outgoing: Dict[str, List[Edge]] = {}
        self._incoming: Dict[str, List[Edge]] = {}
        self._visualizer: Optional[GraphVisualizer] = None
        self._serializer: Optional[GraphSerializer] = None
        self._default_traversal: Optional[TopologicalTraversal] = None
        self._cursor = None
    
    @property
    def nodes(self) -> Dict[str, Node]:
        """Get all nodes in the graph."""
        return self._nodes
    
    @nodes.setter
    def nodes(self, nodes: Dict[str, Node]) -> None:
        """Set all nodes in the graph."""
        self._nodes = nodes
    
    @property
    def edges(self) -> List[Edge]:
        """Get all edges in the graph."""
        return self._edges
    
    @edges.setter
    def edges(self, edges: List[Edge]) -> None:
        """Set all edges in the graph."""
        self._edges = edges
    
    def has_node(self, node_id: str) -> bool:
        """Check if node exists in graph."""
        return node_id in self.nodes
    
    def has_edge(self, source_id: str, target_id: str) -> bool:
        """Check if edge exists in graph."""
        return any(edge.source == source_id and edge.target == target_id for edge in self.edges)

    @classmethod
    def from_yaml(cls, stream: Union[str, TextIO, Path]) -> 'DirectedGraph':
        """Create graph from YAML specification."""
        serializer: GraphSerializer = GraphSerializer()
        return serializer.from_yaml(stream, cls)

    def add_node(self, node: Node) -> None:
        """Add node to graph."""
        self.nodes[node.node_id] = node
        if node.node_id not in self._outgoing:
            self._outgoing[node.node_id] = []
        if node.node_id not in self._incoming:
            self._incoming[node.node_id] = []

    def add_edge(self, edge: Edge) -> None:
        """Add edge to graph."""
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError("Edge nodes must exist in graph")
        self.edges.append(edge)
        self._outgoing[edge.source].append(edge)
        self._incoming[edge.target].append(edge)

    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_edges_from(self, node_id: str) -> List[Edge]:
        """Get all edges from node."""
        return self._outgoing.get(node_id, [])

    def get_next_nodes(self, node_id: str) -> List[Node]:
        """Get nodes that can be reached directly from given node."""
        return [self.nodes[edge.target] for edge in self._outgoing[node_id]]

    def get_prev_nodes(self, node_id: str) -> List[Node]:
        """Get nodes that can reach given node directly."""
        return [self.nodes[edge.source] for edge in self._incoming[node_id]]

    def remove_node(self, node_id: str) -> None:
        """Remove node and its edges from graph."""
        if node_id in self.nodes:
            # Remove edges involving this node
            self.edges = [e for e in self.edges if e.source != node_id and e.target != node_id]
            # Clean up adjacency lists
            self._outgoing.pop(node_id, None)
            self._incoming.pop(node_id, None)
            # Remove node
            self.nodes.pop(node_id)

    def __iter__(self) -> Iterator[Node]:
        """Topological sort iterator."""
        visited = set()
        temp = set()

        def visit(node_id: str) -> Iterator[Node]:
            if node_id in temp:
                raise ValueError("Graph has cycles")
            if node_id not in visited:
                temp.add(node_id)
                for edge in self._outgoing[node_id]:
                    yield from visit(edge.target)
                temp.remove(node_id)
                visited.add(node_id)
                yield self.nodes[node_id]

        for node_id in self.nodes:
            if node_id not in visited:
                yield from visit(node_id)

    def to_ascii_art(self) -> str:
        """Generate ASCII visualization."""
        if self._visualizer is None:
            raise ValueError("Visualizer is not set")
        return self._visualizer.to_ascii_art(self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        if self._serializer is None:
            raise ValueError("Serializer is not set")
        return self._serializer.to_dict(self)

    def get_a_cursor(self, start_node: Node, strategy: Optional['TraversalStrategy'] = None) -> 'Cursor':
        """Get traversal cursor starting at given node."""
        if strategy is None:
            strategy = self._default_traversal
        cursor_class = get_class_by_name(_CURSOR_CLASS_NAME)
        return cursor_class(self, start_node, strategy)

    def get_current_node(self) -> Optional[Node]:
        """Get current node from cursor if it exists."""
        return self._cursor.current if self._cursor else None
    
    def start_cursor(self) -> 'Cursor':
        """Starting my cursor at the first START type node found."""
        start_node = self.get_start_node()
        if not start_node:
            raise ValueError("Graph has no START node")
        self._cursor = self.get_a_cursor(start_node)
        return self._cursor

    def get_start_node(self) -> Optional[Node]:
        """Get the first START type node found."""
        return next((node for node in self.nodes.values() 
                     if node.node_type == NodeType.START), None)

    def get_end_nodes(self) -> List[Node]:
        """Get all END type nodes."""
        return [node for node in self.nodes.values() 
                if node.node_type == NodeType.END]

    def update_cursor(self, node_id: str) -> None:
        """Update graph cursor to specified node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in graph")
        self._cursor = self.get_a_cursor(self.nodes[node_id])