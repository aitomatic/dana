"""Cursor for tracking position and movement through a graph."""

from typing import List, Set, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
if TYPE_CHECKING:
    from .node import Node
    from .directed_graph import DirectedGraph

@dataclass
class GraphCursor:
    """Tracks current position and history in a graph.
    
    The cursor maintains:
    - Current position
    - Visit history
    - Path taken
    - Available moves
    """
    
    graph: 'DirectedGraph'
    current: str  # Current node ID
    visited: Set[str] = field(default_factory=set)
    path: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize cursor state."""
        if self.current not in self.graph.nodes:
            raise ValueError(f"Invalid starting node: {self.current}")
        self.visited.add(self.current)
        self.path.append(self.current)
    
    @property
    def current_node(self) -> 'Node':
        """Get current node."""
        return self.graph.nodes[self.current]
    
    @property
    def available_moves(self) -> List['Node']:
        """Get available next nodes."""
        return self.graph.get_next_nodes(self.current)
    
    def move_to(self, node_id: str) -> bool:
        """Move cursor to specified node if possible.
        
        Args:
            node_id: Target node ID
            
        Returns:
            True if move was valid and successful
        """
        next_nodes = self.graph.get_next_nodes(self.current)
        if not any(node.id == node_id for node in next_nodes):
            return False
            
        self.current = node_id
        self.visited.add(node_id)
        self.path.append(node_id)
        return True
    
    def can_move_to(self, node_id: str) -> bool:
        """Check if moving to node is valid."""
        next_nodes = self.graph.get_next_nodes(self.current)
        return any(node.id == node_id for node in next_nodes)
    
    def peek_forward(self, steps: int = 1) -> List[List['Node']]:
        """Look ahead possible paths.
        
        Args:
            steps: Number of steps to look ahead
            
        Returns:
            List of possible node paths of length 'steps'
        """
        paths = []

        def dfs(node_id: str, path: List['Node'], depth: int):
            if depth == steps:
                paths.append(path[:])
                return
            for next_node in self.graph.get_next_nodes(node_id):
                dfs(next_node.id, path + [next_node], depth + 1)
                
        dfs(self.current, [], 0)
        return paths
    
    def reset(self, node_id: Optional[str] = None) -> None:
        """Reset cursor to starting state or specified node."""
        self.current = node_id or self.path[0]
        self.visited.clear()
        self.path.clear()
        self.visited.add(self.current)
        self.path.append(self.current) 