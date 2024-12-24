"""Base directed graph implementation."""

from typing import Dict, List, Set, Any, Iterator
from dataclasses import dataclass, field
from collections import defaultdict
from .node import Node
from .edge import Edge

@dataclass
class DirectedGraph:
    """Base class for directed graphs."""
    
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize adjacency lists."""
        self._outgoing = defaultdict(list)  # node_id -> List[Edge]
        self._incoming = defaultdict(list)  # node_id -> List[Edge]
        self._build_adjacency_lists()
    
    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        if node.node_id in self.nodes:
            raise ValueError(f"Node {node.node_id} already exists")
        self.nodes[node.node_id] = node
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        if edge.source not in self.nodes:
            raise ValueError(f"Source node {edge.source} does not exist")
        if edge.target not in self.nodes:
            raise ValueError(f"Target node {edge.target} does not exist")
        
        self.edges.append(edge)
        self._outgoing[edge.source].append(edge)
        self._incoming[edge.target].append(edge)
    
    def get_next_nodes(self, node_id: str) -> List[Node]:
        """Get nodes that can be reached directly from given node."""
        return [self.nodes[edge.target] for edge in self._outgoing[node_id]]
    
    def get_prev_nodes(self, node_id: str) -> List[Node]:
        """Get nodes that can reach the given node directly."""
        return [self.nodes[edge.source] for edge in self._incoming[node_id]]
    
    def get_paths(self, start: str, end: str) -> List[List[str]]:
        """Find all paths between start and end nodes."""
        paths = []

        def dfs(current: str, path: List[str]):
            if current == end:
                paths.append(path[:])
                return
            for edge in self._outgoing[current]:
                if edge.target not in path:  # Avoid cycles
                    dfs(edge.target, path + [edge.target])
        dfs(start, [start])
        return paths
    
    def get_subgraph(self, nodes: Set[str]) -> 'DirectedGraph':
        """Extract a subgraph containing only specified nodes."""
        subgraph = DirectedGraph()
        
        # Add nodes
        for node_id in nodes:
            if node_id in self.nodes:
                subgraph.add_node(self.nodes[node_id])
                
        # Add edges between included nodes
        for edge in self.edges:
            if edge.source in nodes and edge.target in nodes:
                subgraph.add_edge(edge)
                
        return subgraph
    
    def _build_adjacency_lists(self) -> None:
        """Build adjacency lists from edges."""
        self._outgoing.clear()
        self._incoming.clear()
        for edge in self.edges:
            self._outgoing[edge.source].append(edge)
            self._incoming[edge.target].append(edge)
    
    def __iter__(self) -> Iterator[Node]:
        """Iterate over nodes in topological order."""
        visited = set()
        temp = set()
        order = []
        
        def visit(node_id: str):
            if node_id in temp:
                raise ValueError("Graph contains a cycle")
            if node_id in visited:
                return
            temp.add(node_id)
            for edge in self._outgoing[node_id]:
                visit(edge.target)
            temp.remove(node_id)
            visited.add(node_id)
            order.append(self.nodes[node_id])
            
        for node_id in self.nodes:
            if node_id not in visited:
                visit(node_id)
                
        return iter(reversed(order))