"""Graph traversal interface."""

from typing import Dict, Any, Optional, Iterator, List
from dataclasses import dataclass, field
from .directed_graph import DirectedGraph
from .node import Node
from .edge import Edge

@dataclass
class Traversal:
    """Manages traversal through a graph.
    
    Provides a consistent interface for:
    - Moving through nodes
    - Checking conditions
    - Tracking state
    - Looking ahead/behind
    """
    
    graph: DirectedGraph
    context: Dict[str, Any]
    current: str  # Current node ID
    path: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize traversal state."""
        if self.current not in self.graph.nodes:
            raise ValueError(f"Invalid start node: {self.current}")
        self.path.append(self.current)

    @property
    def node(self) -> Node:
        """Current node."""
        return self.graph.nodes[self.current]
        
    @property
    def edges(self) -> List[Edge]:
        """Available edges from current node."""
        return self.graph.edges[self.current]

    def next(self) -> Optional[Node]:
        """Move to next valid node.
        
        Returns:
            Next node if available, None if at end
        """
        valid_nodes = self.graph.get_next_nodes_by_context(self.current, self.context)
        if not valid_nodes:
            return None
            
        next_node = valid_nodes[0]  # Take first valid path
        self.current = next_node.id
        self.path.append(self.current)
        return next_node

    def peek(self) -> List[Node]:
        """Look at possible next nodes without moving."""
        return self.graph.get_next_nodes_by_context(self.current, self.context)

    def peek_path(self, steps: int = 1) -> List[List[Node]]:
        """Look ahead multiple steps."""
        return [
            [self.graph.nodes[node_id] for node_id in path]
            for path in self.graph.find_paths_by_context(
                self.current, 
                max_paths=steps, 
                context=self.context
            )
        ]

    def move_to(self, node_id: str) -> bool:
        """Try to move to specific node."""
        valid_nodes = self.graph.get_next_nodes_by_context(self.current, self.context)
        if not any(node.id == node_id for node in valid_nodes):
            return False
            
        self.current = node_id
        self.path.append(node_id)
        return True

    def reset(self, node_id: Optional[str] = None) -> None:
        """Reset traversal state."""
        self.current = node_id or self.path[0]
        self.path = [self.current]

    def __iter__(self) -> Iterator[Node]:
        """Iterate through valid nodes from current position."""
        while True:
            yield self.node
            if not self.next():
                break 