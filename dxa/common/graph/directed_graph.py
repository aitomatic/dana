"""Base directed graph implementation."""

from typing import Dict, List, Set, Any, Iterator, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from copy import deepcopy
from .node import Node
from .edge import Edge

@dataclass
class DirectedGraph:
    """Base class for directed graphs."""
    _nodes: Dict[str, Node] = field(default_factory=dict)
    _edges: List[Edge] = field(default_factory=list)
    _history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def nodes(self) -> Dict[str, Node]:
        """Get nodes."""
        return self._nodes
    
    @nodes.setter
    def nodes(self, nodes: Dict[str, Node]) -> None:
        """Set nodes."""
        self._nodes = nodes
    
    @property
    def edges(self) -> List[Edge]:
        """Get edges."""
        return self._edges
    
    @edges.setter
    def edges(self, edges: List[Edge]) -> None:
        """Set edges."""
        self._edges = edges

    def duplicate(self) -> 'DirectedGraph':
        """Duplicate the graph."""
        return deepcopy(self)
    
    @property
    def history(self) -> List[Dict[str, Any]]:
        """Get history."""
        if not self._history:
            return []
        return self._history
    
    def __post_init__(self):
        """Initialize adjacency lists."""
        self._outgoing = defaultdict(list)  # node_id -> List[Edge]
        self._incoming = defaultdict(list)  # node_id -> List[Edge]
        self._build_adjacency_lists()
    
    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        if node.node_id in self._nodes:
            raise ValueError(f"Node {node.node_id} already exists")
        self._nodes[node.node_id] = node
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        if edge.source not in self._nodes:
            raise ValueError(f"Source node {edge.source} does not exist")
        if edge.target not in self._nodes:
            raise ValueError(f"Target node {edge.target} does not exist")
        
        self._edges.append(edge)
        self._outgoing[edge.source].append(edge)
        self._incoming[edge.target].append(edge)
    
    def get_next_nodes(self, node_id: str) -> List[Node]:
        """Get nodes that can be reached directly from given node."""
        return [self._nodes[edge.target] for edge in self._outgoing[node_id]]
    
    def get_prev_nodes(self, node_id: str) -> List[Node]:
        """Get nodes that can reach the given node directly."""
        return [self._nodes[edge.source] for edge in self._incoming[node_id]]
    
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
            if node_id in self._nodes:
                subgraph.add_node(self._nodes[node_id])
                
        # Add edges between included nodes
        for edge in self._edges:
            if edge.source in nodes and edge.target in nodes:
                subgraph.add_edge(edge)
                
        return subgraph
    
    def _build_adjacency_lists(self) -> None:
        """Build adjacency lists from edges."""
        self._outgoing.clear()
        self._incoming.clear()
        for edge in self._edges:
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
            order.append(self._nodes[node_id])
            
        for node_id in self._nodes:
            if node_id not in visited:
                visit(node_id)
                
        return iter(reversed(order))
    
    def to_ascii_art(self) -> str:
        """Generate basic ASCII art representation of the directed graph."""
        processed = set()
        
        def _node_to_ascii(node_id: str, level: int = 0, offset: int = 0) -> tuple[list[str], int]:
            if node_id in processed:
                return ([f"{' ' * offset}({node_id})..."], len(node_id) + 5)
            
            processed.add(node_id)
            node_str = f"({node_id})"
            
            edges = [e for e in self._edges if e.source == node_id]
            if not edges:
                return ([f"{' ' * offset}{node_str}"], len(node_str))
            
            result = [f"{' ' * offset}{node_str}"]
            
            if len(edges) == 1:
                # Single path
                result.append(f"{' ' * offset} |")
                result.append(f"{' ' * offset} v")
                child_lines, width = _node_to_ascii(edges[0].target, level + 1, offset)
                result.extend(child_lines)
                return result, max(len(node_str), width)
            else:
                # Multiple paths
                branch_count = len(edges)
                path_width = 8  # Fixed width for simplicity
                
                # Draw branches
                branch_line = f"{' ' * offset} |"
                for _ in range(branch_count - 1):
                    branch_line += "-->"
                result.append(branch_line)
                
                # Draw arrows
                arrow_line = f"{' ' * offset} v"
                for _ in range(branch_count - 1):
                    arrow_line += "   v"
                result.append(arrow_line)
                
                # Process children
                child_results = []
                max_height = 0
                for i, edge in enumerate(edges):
                    child_offset = offset + i * path_width
                    child_lines, _ = _node_to_ascii(edge.target, level + 1, child_offset)
                    child_results.append(child_lines)
                    max_height = max(max_height, len(child_lines))
                
                # Combine results
                for i in range(max_height):
                    line_parts = []
                    for j, child_lines in enumerate(child_results):
                        if i < len(child_lines):
                            if j == 0:
                                line_parts.append(child_lines[i])
                            else:
                                padding = " " * (offset + j * path_width - len("".join(line_parts)))
                                line_parts.append(padding + child_lines[i].lstrip())
                    result.append("".join(line_parts))
                
                return result, offset + path_width * branch_count
        
        # Find root nodes (nodes with no incoming edges)
        root_nodes = [
            node_id for node_id in self._nodes
            if not any(e.target == node_id for e in self._edges)
        ]
        
        if not root_nodes:
            return "(empty graph)"
        
        # Start from first root node
        lines, _ = _node_to_ascii(root_nodes[0])
        return "\n".join(lines)
    
    def to_mermaid(self) -> str:
        """Generate Mermaid flowchart representation of the directed graph.
        
        Example:
        ```mermaid
        graph TD
            A --> B
            B --> C
            B --> D
            C --> E
            D --> E
        ```
        """
        lines = ["graph TD"]
        
        # Add edges with arrow syntax
        for edge in self._edges:
            lines.append(f"    {edge.source} --> {edge.target}")
        
        return "\n".join(lines)

    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID."""
        for node in self.nodes.values():
            if node.node_id == node_id:
                return node
        return None
