"""Factory for creating graphs from different sources."""

from pathlib import Path
from typing import Any, TextIO

from .directed_graph import DirectedGraph, Edge, Node
from .serializer import GraphSerializer


class GraphFactory:
    """Creates graphs from various sources."""

    _serializer = GraphSerializer()

    @classmethod
    def from_dict(cls, data: dict[str, Any], graph_cls: type[DirectedGraph] = DirectedGraph) -> DirectedGraph:
        """Create graph from dictionary data."""
        return cls._serializer.from_dict(data, graph_cls)

    @classmethod
    def from_yaml(cls, stream: str | TextIO | Path, graph_cls: type[DirectedGraph] = DirectedGraph) -> DirectedGraph:
        """Create graph from YAML file or stream."""
        return cls._serializer.from_yaml(stream, graph_cls)

    @classmethod
    def create_empty(cls, graph_cls: type[DirectedGraph] = DirectedGraph) -> DirectedGraph:
        """Create empty graph."""
        return graph_cls()

    @classmethod
    def create_linear(cls, nodes: list[str], graph_cls: type[DirectedGraph] = DirectedGraph) -> DirectedGraph:
        """Create linear graph from list of node IDs."""
        graph = graph_cls()

        # Add nodes
        for node_id in nodes:
            graph.add_node(Node(node_id=node_id))

        # Add edges
        for i in range(len(nodes) - 1):
            graph.add_edge(Edge(source=nodes[i], target=nodes[i + 1]))

        return graph
