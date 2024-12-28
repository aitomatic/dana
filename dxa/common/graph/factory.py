"""Factory for creating graphs from different sources."""

from typing import Dict, Any, Type, Union, TextIO
from pathlib import Path
from .directed_graph import DirectedGraph
from .node import Node
from .edge import Edge
from .serializer import GraphSerializer

class GraphFactory:
    """Creates graphs from various sources."""
    
    _serializer = GraphSerializer()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], graph_cls: Type[DirectedGraph] = DirectedGraph) -> DirectedGraph:
        """Create graph from dictionary data."""
        return cls._serializer.from_dict(data, graph_cls)
        
    @classmethod
    def from_yaml(cls, 
                  stream: Union[str, TextIO, Path], graph_cls: Type[DirectedGraph] = DirectedGraph) -> DirectedGraph:
        """Create graph from YAML file or stream."""
        return cls._serializer.from_yaml(stream, graph_cls)
        
    @classmethod
    def create_empty(cls, graph_cls: Type[DirectedGraph] = DirectedGraph) -> DirectedGraph:
        """Create empty graph."""
        return graph_cls()
        
    @classmethod
    def create_linear(cls, nodes: list[str], graph_cls: Type[DirectedGraph] = DirectedGraph) -> DirectedGraph:
        """Create linear graph from list of node IDs."""
        graph = graph_cls()
        
        # Add nodes
        for node_id in nodes:
            graph.add_node(Node(node_id=node_id))
            
        # Add edges
        for i in range(len(nodes) - 1):
            graph.add_edge(Edge(source=nodes[i], target=nodes[i + 1]))
            
        return graph 