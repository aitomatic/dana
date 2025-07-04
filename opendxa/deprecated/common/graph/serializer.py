"""Graph serialization strategies."""

from pathlib import Path
from typing import Any, TextIO

import yaml

from dana.common.graph.directed_graph import DirectedGraph, Edge, Node, NodeType
from dana.common.utils.misc import Misc


class GraphSerializer:
    """Base graph serialization."""

    def to_dict(self, graph: DirectedGraph) -> dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "nodes": {
                node_id: {"node_type": node.node_type, "description": node.description, "metadata": node.metadata}
                for node_id, node in graph.nodes.items()
            },
            "edges": [{"source": edge.source, "target": edge.target, "metadata": edge.metadata} for edge in graph.edges],
        }

    def from_dict(self, data: dict[str, Any], graph_cls: type[DirectedGraph]) -> DirectedGraph:
        """Create graph from dictionary."""
        graph = graph_cls()

        # Add nodes
        for node_id, node_data in data["nodes"].items():
            node = Node(
                node_id=node_id,
                node_type=node_data.get("node_type", NodeType.NODE),
                description=node_data.get("description", ""),
                metadata=node_data.get("metadata", {}),
            )
            graph.add_node(node)

        # Add edges
        for edge_data in data["edges"]:
            edge = Edge(source=edge_data["source"], target=edge_data["target"], metadata=edge_data.get("metadata", {}))
            graph.add_edge(edge)

        return graph

    def to_yaml(self, graph: DirectedGraph, stream: str | TextIO | Path) -> None:
        """Save graph to YAML."""
        data = self.to_dict(graph)
        if isinstance(stream, str | Path):
            with open(stream, "w", encoding="utf-8") as f:
                yaml.dump(data, f)
        else:
            yaml.dump(data, stream)

    def from_yaml(self, stream: str | TextIO | Path, graph_cls: type[DirectedGraph]) -> DirectedGraph:
        """Load graph from YAML."""
        if isinstance(stream, str | Path):
            data = Misc.load_yaml_config(stream)
        else:
            data = yaml.safe_load(stream)
        return self.from_dict(data, graph_cls)
