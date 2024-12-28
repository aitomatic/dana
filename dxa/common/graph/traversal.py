"""Graph traversal implementations."""

from abc import ABC, abstractmethod
from typing import Iterator, Optional
from .directed_graph import DirectedGraph
from .node import Node

class TraversalStrategy(ABC):
    """Base class for graph traversal strategies."""
    
    @abstractmethod
    def traverse(self, graph: DirectedGraph, start_node: str) -> Iterator[Node]:
        """Traverse graph starting from given node."""
        pass

class BreadthFirstTraversal(TraversalStrategy):
    """Breadth-first traversal strategy."""
    
    def traverse(self, graph: DirectedGraph, start_node: str) -> Iterator[Node]:
        visited = set()
        queue = [start_node]
        
        while queue:
            node_id = queue.pop(0)
            if node_id not in visited:
                visited.add(node_id)
                node = graph.nodes[node_id]
                yield node
                queue.extend(n.node_id for n in graph.get_next_nodes(node_id))

class DepthFirstTraversal(TraversalStrategy):
    """Depth-first traversal strategy."""
    
    def traverse(self, graph: DirectedGraph, start_node: str) -> Iterator[Node]:
        visited = set()
        
        def visit(node_id: str) -> Iterator[Node]:
            if node_id not in visited:
                visited.add(node_id)
                node = graph.nodes[node_id]
                yield node
                for next_node in graph.get_next_nodes(node_id):
                    yield from visit(next_node.node_id)
                    
        yield from visit(start_node)

class TopologicalTraversal(TraversalStrategy):
    """Topological sort traversal."""
    
    def traverse(self, graph: DirectedGraph, start_node: str) -> Iterator[Node]:
        visited = set()
        temp = set()
        
        def visit(node_id: str) -> Iterator[Node]:
            if node_id in temp:
                raise ValueError("Graph has cycles")
            if node_id not in visited:
                temp.add(node_id)
                for next_node in graph.get_next_nodes(node_id):
                    yield from visit(next_node.node_id)
                temp.remove(node_id)
                visited.add(node_id)
                yield graph.nodes[node_id]
                
        yield from visit(start_node)

class Cursor:
    """Cursor for traversing a graph."""
    
    def __init__(self, graph: DirectedGraph, start_node: str, 
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
            return next(self._iterator)
        except StopIteration:
            return None 