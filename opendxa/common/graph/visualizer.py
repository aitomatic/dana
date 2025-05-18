"""Graph visualization strategies."""

from .directed_graph import DirectedGraph


class GraphVisualizer:
    """Base graph visualization."""

    def to_ascii_art(self, graph: DirectedGraph) -> str:
        """Generate ASCII art representation."""
        if not graph.nodes:
            return "(empty graph)"

        lines = []
        visited = set()

        def visit(node_id: str, depth: int = 0):
            if node_id in visited:
                return
            visited.add(node_id)

            node = graph.nodes[node_id]
            prefix = "  " * depth
            lines.append(f"{prefix}{node.node_id} [{node.node_type}]")

            for next_node in graph.get_next_nodes(node_id):
                visit(next_node.node_id, depth + 1)

        # Start from nodes with no incoming edges
        roots = [n.node_id for n in graph.nodes.values() if not graph.get_prev_nodes(n.node_id)]

        for root in roots:
            visit(root)

        return "\n".join(lines)
