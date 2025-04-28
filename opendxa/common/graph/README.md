<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../../README.md) | [Main Documentation](../../../docs/README.md)

# DXA Graph Library

Core graph functionality used across DXA for representing and traversing directed graphs.

## Components

- `DirectedGraph`: Base graph implementation
- `Node`: Graph node with metadata
- `Edge`: Graph edge with optional conditions
- `GraphCursor`: Position tracking in graphs
- `GraphFactory`: Common graph pattern creation

## Usage

```python
from dxa.common.graph import DirectedGraph, Node, Edge, GraphCursor

# Create graph
graph = DirectedGraph()
graph.add_node(Node("start", "task", "Begin"))
graph.add_node(Node("end", "task", "Complete"))
graph.add_edge(Edge("start", "end"))

# Track position
cursor = GraphCursor(graph, "start")
cursor.move_to("end")
```

## TODO

### Visualization

- [ ] Add Graphviz export for static visualization
- [ ] Support Mermaid.js format for documentation
- [ ] Interactive visualization using d3.js or similar
- [ ] Real-time cursor position visualization
- [ ] Path highlighting and animation
- [ ] Subgraph visualization
- [ ] Export to common formats (DOT, JSON, YAML)

### Analysis

- [ ] Cycle detection
- [ ] Graph metrics (density, centrality, etc.)
- [ ] Path optimization
- [ ] Pattern matching
- [ ] Graph comparison tools

### Performance

- [ ] Optimize large graph operations
- [ ] Lazy loading for big graphs
- [ ] Caching for frequent traversals
- [ ] Parallel graph algorithms

## Integration Points

The graph library is used by:

- Workflows (execution flows)
- Plans (execution strategies)
- Decision trees
- State machines

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../../../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
