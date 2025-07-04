<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../../README.md) | [Main Documentation](../../../docs/README.md) | [Graph Architecture](../../../docs/core-concepts/graphs.md)

# Graph Module Implementation (`dana.common.graph`)

This module provides the implementation of the directed graph data structures and algorithms used throughout the Dana framework.

> **Note:** For conceptual information about the graph architecture, design philosophy, and usage patterns, please see the [Graph Architecture Documentation](../../../docs/core-concepts/graphs.md).

## Implementation Details

### Core Classes

| Class | File | Purpose |
|-------|------|---------|
| `DirectedGraph` | `directed_graph.py` | Core graph data structure |
| `Node` | `directed_graph.py` | Graph node with metadata |
| `Edge` | `directed_graph.py` | Graph edge with conditions |
| `NodeType` | `directed_graph.py` | Enumeration of node types |
| `GraphCursor` | `directed_graph.py` | Position tracking in graphs |
| `GraphFactory` | `factory.py` | Creation of common graph patterns |
| `GraphSerializer` | `serializer.py` | Serialization/deserialization |
| `GraphTraversal` | `traversal.py` | Graph traversal algorithms |
| `GraphVisualizer` | `visualizer.py` | Visualization utilities |

## API Reference

### DirectedGraph

```python
class DirectedGraph:
    def __init__(self, id=None, name=None, description=None)
    def add_node(self, node)
    def add_edge(self, edge)
    def get_node(self, node_id)
    def get_edge(self, source_id, target_id)
    def get_nodes(self)
    def get_edges(self)
    def get_outgoing_edges(self, node_id)
    def get_incoming_edges(self, node_id)
    def remove_node(self, node_id)
    def remove_edge(self, source_id, target_id)
    def has_node(self, node_id)
    def has_edge(self, source_id, target_id)
    def to_dict(self)
    def from_dict(self, data)
    def copy(self)
    def merge(self, other_graph)
```

### Node

```python
class Node:
    def __init__(self, id, type, objective, metadata=None)
    def get_id(self)
    def get_type(self)
    def get_objective(self)
    def get_metadata(self)
    def set_metadata(self, key, value)
    def to_dict(self)
    @classmethod
    def from_dict(cls, data)
```

### Edge

```python
class Edge:
    def __init__(self, source_id, target_id, condition=None, metadata=None)
    def get_source_id(self)
    def get_target_id(self)
    def get_condition(self)
    def get_metadata(self)
    def set_metadata(self, key, value)
    def evaluate_condition(self, context)
    def to_dict(self)
    @classmethod
    def from_dict(cls, data)
```

### GraphCursor

```python
class GraphCursor:
    def __init__(self, graph, current_node_id=None)
    def get_current_node(self)
    def get_current_node_id(self)
    def move_to(self, node_id)
    def can_move_to(self, node_id)
    def get_possible_moves(self, context=None)
    def get_path_history(self)
    def reset(self)
    def copy(self)
```

### GraphFactory

```python
class GraphFactory:
    @staticmethod
    def create_linear(nodes, id=None, name=None, description=None)
    @staticmethod
    def create_branching(root_node, branches, id=None, name=None, description=None)
    @staticmethod
    def create_decision_tree(root_node, decisions, id=None, name=None, description=None)
    @staticmethod
    def create_state_machine(states, transitions, initial_state, id=None, name=None, description=None)
```

### GraphTraversal

```python
class GraphTraversal:
    @staticmethod
    def depth_first(graph, start_node_id, visitor_fn)
    @staticmethod
    def breadth_first(graph, start_node_id, visitor_fn)
    @staticmethod
    def topological_sort(graph)
    @staticmethod
    def find_path(graph, start_node_id, end_node_id)
    @staticmethod
    def find_all_paths(graph, start_node_id, end_node_id)
```

## Usage Examples

### Creating a Simple Graph

```python
from dana.common.graph import DirectedGraph, Node, Edge, NodeType

# Create a graph
graph = DirectedGraph(id="workflow", name="Simple Workflow", description="Example workflow")

# Add nodes
graph.add_node(Node("start", NodeType.START, "Begin workflow"))
graph.add_node(Node("process", NodeType.TASK, "Process data"))
graph.add_node(Node("decide", NodeType.DECISION, "Make decision"))
graph.add_node(Node("success", NodeType.END, "Success end"))
graph.add_node(Node("failure", NodeType.END, "Failure end"))

# Add edges
graph.add_edge(Edge("start", "process"))
graph.add_edge(Edge("process", "decide"))
graph.add_edge(Edge(
    "decide", "success", 
    condition=lambda ctx: ctx.get("process_result", {}).get("status") == "success"
))
graph.add_edge(Edge(
    "decide", "failure",
    condition=lambda ctx: ctx.get("process_result", {}).get("status") != "success"
))
```

### Using GraphCursor for Traversal

```python
from dana.common.graph import GraphCursor

# Create cursor
cursor = GraphCursor(graph, "start")

# Navigate through graph
context = {"process_result": {"status": "success"}}

# Move to next node
cursor.move_to("process")

# Get possible next moves based on context
next_moves = cursor.get_possible_moves(context)
for move in next_moves:
    print(f"Can move to: {move}")

# Move to decision node
cursor.move_to("decide")

# Get possible next moves with conditions evaluated
next_moves = cursor.get_possible_moves(context)
# Will only include "success" node due to the context
```

### Using Factory for Common Patterns

```python
from dana.common.graph import GraphFactory, NodeType, Node

# Create nodes
nodes = [
    Node("step1", NodeType.TASK, "Step 1"),
    Node("step2", NodeType.TASK, "Step 2"),
    Node("step3", NodeType.TASK, "Step 3")
]

# Create a linear graph
linear_graph = GraphFactory.create_linear(
    nodes,
    id="linear_workflow",
    name="Linear Workflow",
    description="Simple sequential workflow"
)

# Create a branching graph
root = Node("root", NodeType.START, "Start")
branches = {
    "branch1": [Node("b1_step1", NodeType.TASK, "Branch 1 Step 1"), 
                Node("b1_step2", NodeType.TASK, "Branch 1 Step 2")],
    "branch2": [Node("b2_step1", NodeType.TASK, "Branch 2 Step 1")]
}
branching_graph = GraphFactory.create_branching(
    root,
    branches,
    id="branching_workflow",
    name="Branching Workflow"
)
```

### Serialization and Deserialization

```python
from dana.common.graph import GraphSerializer

# Serialize graph to JSON
json_data = GraphSerializer.to_json(graph)

# Save graph to file
GraphSerializer.save_to_file(graph, "workflow.json")

# Load graph from file
loaded_graph = GraphSerializer.load_from_file("workflow.json")
```

## Integration with Other Components

### In the Planning Layer

```python
from dana.common.graph import DirectedGraph, Node, Edge, NodeType
from dana.core.runtime import PlanExecutor

# Create a plan graph
plan_graph = DirectedGraph(id="analysis_plan", name="Data Analysis Plan")
plan_graph.add_node(Node("collect", NodeType.TASK, "Collect data"))
plan_graph.add_node(Node("analyze", NodeType.TASK, "Analyze data"))
plan_graph.add_node(Node("report", NodeType.TASK, "Generate report"))
plan_graph.add_edge(Edge("collect", "analyze"))
plan_graph.add_edge(Edge("analyze", "report"))

# Use in plan executor
executor = PlanExecutor()
result = executor.execute(plan_graph, context={})
```

### In the State Management System

```python
from dana.common.graph import GraphFactory
from dana.common.graph import Node, NodeType

# Define a state machine
states = [
    Node("idle", NodeType.STATE, "Idle state"),
    Node("running", NodeType.STATE, "Running state"),
    Node("paused", NodeType.STATE, "Paused state"),
    Node("completed", NodeType.STATE, "Completed state")
]

transitions = [
    ("idle", "running", lambda ctx: ctx.get("command") == "start"),
    ("running", "paused", lambda ctx: ctx.get("command") == "pause"),
    ("paused", "running", lambda ctx: ctx.get("command") == "resume"),
    ("running", "completed", lambda ctx: ctx.get("progress") == 100),
    ("paused", "completed", lambda ctx: ctx.get("command") == "complete")
]

state_machine = GraphFactory.create_state_machine(
    states, transitions, "idle", 
    id="process_state", name="Process State Machine"
)
```

## TODO: Future Enhancements

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

For more advanced usage examples and integration patterns, please refer to the test files in `tests/common/graph/`.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>