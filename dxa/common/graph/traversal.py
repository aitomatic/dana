"""Graph traversal implementations."""

from abc import ABC, abstractmethod
from typing import Iterator, Optional, Set, List
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

class ContinuousTraversal(TraversalStrategy):
    """Traversal strategy for continuous monitoring loops."""
    
    def __init__(self):
        self._visited: Set[str] = set()
        self._cycle_count = 0
        self._in_cycle = False

    def traverse(self, graph: DirectedGraph, start_node: Node) -> Iterator[Node]:
        """Traverse graph continuously, handling cycles and conditions."""
        while True:  # Continuous monitoring loop
            current = start_node
            self._in_cycle = True
            
            while self._in_cycle:
                yield current

                # Get next nodes based on conditions
                next_nodes = graph.get_next_nodes(current.node_id)
                
                # If no next nodes, end cycle
                if not next_nodes:
                    self._in_cycle = False
                    break

                # Handle conditional transitions
                next_node = self._select_next_node(graph, current, next_nodes)
                if not next_node:
                    self._in_cycle = False
                    break

                current = next_node
                
                # If we hit END, restart from START
                if current.node_type == NodeType.END:
                    self._cycle_count += 1
                    break

    def _select_next_node(self, graph: DirectedGraph, 
                         current: Node, 
                         next_nodes: List[Node]) -> Optional[Node]:
        """Select next node based on conditions in edge metadata."""
        for node in next_nodes:
            # Find edge between current and next node
            edge = next(
                (e for e in graph.edges 
                 if e.source == current.node_id 
                 and e.target == node.node_id),
                None
            )
            
            if not edge:
                continue

            # If no condition in metadata, or condition is met
            if (not edge.metadata.get('condition') or 
                self._check_condition(edge.metadata['condition'])):
                return node
                
        return None

    def _check_condition(self, condition: str) -> bool:
        """Check if condition is met.
        For now, return True for 'parameters_normal',
        False for 'parameters_abnormal'
        TODO: Implement actual condition checking
        """
        return condition == 'parameters_normal' 