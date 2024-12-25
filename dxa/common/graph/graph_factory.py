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
            graph.add_edge(Edge(nodes[i].node_id, nodes[i + 1].node_id))
            
        return graph

    @staticmethod 
    def loop(body: List[Node], condition: str) -> DirectedGraph:
        """Create loop with condition."""
        graph = DirectedGraph()
        
        for node in body:
            graph.add_node(node)
            
        # Connect in sequence
        for i in range(len(body) - 1):
            graph.add_edge(Edge(body[i].node_id, body[i + 1].node_id))
            
        # Add loop back edge with condition
        graph.add_edge(Edge(body[-1].node_id, body[0].node_id, condition=condition))
        
        return graph

    @staticmethod
    def branch(condition_node: Node, true_path: List[Node], false_path: List[Node]) -> DirectedGraph:
        """Create conditional branch."""
        graph = DirectedGraph()
        graph.add_node(condition_node)
        
        for node in true_path + false_path:
            graph.add_node(node)
            
        graph.add_edge(Edge(condition_node.node_id, true_path[0].node_id, condition="result==true"))
        graph.add_edge(Edge(condition_node.node_id, false_path[0].node_id, condition="result==false"))
        
        return graph 