"""Graph traversal implementations."""

from abc import ABC, abstractmethod
from typing import Iterator, Optional
from .directed_graph import DirectedGraph, Node, NodeType

class TraversalStrategy(ABC):
    """Base class for graph traversal strategies."""
    
    @abstractmethod
    def traverse(self, graph: DirectedGraph, start_node: Node) -> Iterator[Node]:
        """Traverse graph starting from given node."""
        pass

class BreadthFirstTraversal(TraversalStrategy):
    """Breadth-first traversal strategy."""
    
    def traverse(self, graph: DirectedGraph, start_node: Node) -> Iterator[Node]:
        """Traverse graph breadth-first."""
        visited = set()
        queue = [start_node]  # Now a Node
        
        while queue:
            node = queue.pop(0)  # Now a Node
            if node.node_id not in visited:
                visited.add(node.node_id)
                yield node
                queue.extend(graph.get_next_nodes(node.node_id))

class DepthFirstTraversal(TraversalStrategy):
    """Depth-first traversal strategy."""
    
    def traverse(self, graph: DirectedGraph, start_node: Node) -> Iterator[Node]:
        """Traverse graph depth-first."""
        visited = set()
        
        def visit(node: Node) -> Iterator[Node]:
            if node.node_id not in visited:
                visited.add(node.node_id)
                yield node
                for next_node in graph.get_next_nodes(node.node_id):
                    yield from visit(next_node)
                    
        yield from visit(start_node)

class TopologicalTraversal(TraversalStrategy):
    """Topological sort traversal that respects node types."""
    
    def traverse(self, graph: DirectedGraph, start_node: Node) -> Iterator[Node]:
        """Traverse graph in topological order respecting node types."""
        visited = set()
        temp = set()
        
        def visit(node: Node) -> Iterator[Node]:
            if node.node_id in temp:
                raise ValueError("Graph has cycles")
            if node.node_id not in visited:
                temp.add(node.node_id)
                visited.add(node.node_id)  # Mark visited immediately
                
                if node.node_type == NodeType.START:
                    yield node
                    next_nodes = graph.get_next_nodes(node.node_id)
                    for next_node in next_nodes:
                        if next_node.node_type != NodeType.END:
                            yield from visit(next_node)
                    for next_node in next_nodes:
                        if next_node.node_type == NodeType.END:
                            yield from visit(next_node)
                else:
                    yield node  # Yield non-START nodes immediately
                    for next_node in graph.get_next_nodes(node.node_id):
                        yield from visit(next_node)
                
                temp.remove(node.node_id)
        
        yield from visit(start_node)

class Cursor:
    """Cursor for traversing a graph."""
    
    def __init__(self, graph: DirectedGraph, start_node: Node,
                 strategy: Optional[TraversalStrategy] = None):
        self.graph = graph
        self.current = start_node
        self.strategy = strategy or TopologicalTraversal()
        self._iterator = self.strategy.traverse(graph, start_node)
        
    def __iter__(self) -> Iterator[Node]:
        return self._iterator
        
    def next(self) -> Optional[Node]:
        """Get next node in traversal."""
        try:
            self.current = next(self._iterator)  # Store the next node
            return self.current
        except StopIteration:
            return None 