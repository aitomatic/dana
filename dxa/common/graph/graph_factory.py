"""Factory methods for common workflow patterns."""

from typing import List, Type, Callable, Union
from .directed_graph import DirectedGraph
from .node import Node
from .edge import Edge

GraphConstructor = Union[Type[DirectedGraph], Callable[[], DirectedGraph]]

class GraphFactory:
    """Factory methods for workflow patterns."""
    
    @staticmethod
    def create_sequence(nodes: List[Node], graph_constructor: GraphConstructor = DirectedGraph) -> DirectedGraph:
        """Create linear sequence of nodes."""
        graph = graph_constructor() if callable(graph_constructor) else graph_constructor()
        
        for node in nodes:
            graph.add_node(node)
            
        for i in range(len(nodes) - 1):
            graph.add_edge(Edge(nodes[i].id, nodes[i + 1].id))
            
        return graph

    @staticmethod 
    def loop(body: List[Node], condition: str) -> DirectedGraph:
        """Create loop with condition."""
        graph = DirectedGraph()
        
        for node in body:
            graph.add_node(node)
            
        # Connect in sequence
        for i in range(len(body) - 1):
            graph.add_edge(Edge(body[i].id, body[i+1].id))
            
        # Add loop back edge with condition
        graph.add_edge(Edge(body[-1].id, body[0].id, condition=condition))
        
        return graph

    @staticmethod
    def branch(condition_node: Node, true_path: List[Node], false_path: List[Node]) -> DirectedGraph:
        """Create conditional branch."""
        graph = DirectedGraph()
        graph.add_node(condition_node)
        
        for node in true_path + false_path:
            graph.add_node(node)
            
        graph.add_edge(Edge(condition_node.id, true_path[0].id, condition="result==true"))
        graph.add_edge(Edge(condition_node.id, false_path[0].id, condition="result==false"))
        
        return graph 