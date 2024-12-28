"""Base directed graph implementation."""

from typing import Dict, List, Optional, Iterator, Any, Union, TextIO
from pathlib import Path
from .node import Node
from .edge import Edge
from .visualizer import GraphVisualizer
from .serializer import GraphSerializer
from .traversal import (
    Cursor,
    TraversalStrategy,
    BreadthFirstTraversal,
    DepthFirstTraversal,
    TopologicalTraversal
)

class DirectedGraph:
    """Pure directed graph implementation."""
    def __init__(self):
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []
        self._outgoing: Dict[str, List[Edge]] = {}
        self._incoming: Dict[str, List[Edge]] = {}
        self._visualizer = GraphVisualizer()
        self._serializer = GraphSerializer()
        self._default_traversal = TopologicalTraversal()
    
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

    @classmethod
    def from_yaml(cls, stream: Union[str, TextIO, Path]) -> 'DirectedGraph':
        """Create graph from YAML specification."""
        serializer = GraphSerializer()
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
        return self._visualizer.to_ascii_art(self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self._serializer.to_dict(self)

    def cursor(self, start_node: str, 
               strategy: Optional[TraversalStrategy] = None) -> Cursor:
        """Get traversal cursor starting at given node."""
        if strategy is None:
            strategy = self._default_traversal
        return Cursor(self, start_node, strategy)

    def traverse_bfs(self, start_node: str) -> Cursor:
        """Get breadth-first traversal cursor."""
        return self.cursor(start_node, BreadthFirstTraversal())

    def traverse_dfs(self, start_node: str) -> Cursor:
        """Get depth-first traversal cursor."""
        return self.cursor(start_node, DepthFirstTraversal())
