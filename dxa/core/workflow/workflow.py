"""Base workflow implementation using directed graphs."""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union, cast, TextIO
from dataclasses import dataclass, field
import yaml
from ...common.graph import DirectedGraph, Node, Edge
from ..types import Objective
from .schema import validate_workflow_yaml
from .workflow_factory import text_to_yaml

@dataclass
class WorkflowNode(Node):
    """Workflow step node."""
    type: str  # START, END, TASK, DECISION, etc.
    description: str
    requires: Dict[str, Any] = field(default_factory=dict)  # Required resources/state
    provides: Dict[str, Any] = field(default_factory=dict)  # Produced outputs/state
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

@dataclass 
class WorkflowEdge(Edge):
    """Workflow transition edge."""
    condition: Optional[str] = None  # Condition for taking this path
    state_updates: Dict[str, Any] = field(default_factory=dict)  # State changes on transition
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowCursor:
    """Cursor for traversing workflow graphs."""
    workflow: 'Workflow'
    current: Optional[WorkflowNode] = None
    _visited: set = field(default_factory=set)
    _next_nodes: List[WorkflowNode] = field(default_factory=list)

    def __post_init__(self):
        """Initialize cursor at START node."""
        if not self.current:
            self.current = self.workflow.get_start()
        self._next_nodes = self._get_next_nodes()

    def _get_next_nodes(self) -> List[WorkflowNode]:
        """Get available next nodes from current position."""
        if not self.current:
            return []
        edges = self.workflow.get_edges_from(self.current.node_id)
        return [
            cast(WorkflowNode, self.workflow.nodes[edge.target])
            for edge in edges
        ]

    def has_next(self) -> bool:
        """Check if there are unvisited nodes ahead."""
        return bool(self._next_nodes)

    def next(self) -> Optional[WorkflowNode]:
        """Move to next node in workflow."""
        if not self.has_next():
            return None
        
        self.current = self._next_nodes.pop(0)
        self._visited.add(self.current.node_id)
        self._next_nodes = [
            node for node in self._get_next_nodes()
            if node.node_id not in self._visited
        ]
        return self.current

    def set_next(self, node: WorkflowNode) -> None:
        """Override next node (useful for decision points)."""
        if node.node_id not in self.workflow.nodes:
            raise ValueError(f"Node {node.node_id} not in workflow")
        self._next_nodes.insert(0, node)

class Workflow(DirectedGraph):
    """Workflow class for workflow patterns.
    
    A workflow is a directed graph where:
    - Nodes represent tasks, decisions, or control points
    - Edges represent valid transitions with conditions
    - The structure defines all possible execution paths
    - State changes are tracked through transitions
    """
    def __init__(self, objective: Optional[Union[str, Objective]] = None):
        super().__init__()
        if isinstance(objective, str):
            self._objective = Objective(objective)
        else:
            self._objective = objective
    
    @property
    def objective(self) -> Objective:
        """Get objective."""
        if not self._objective:
            raise ValueError("Objective not set")
        return self._objective
    
    @objective.setter
    def objective(self, objective: Union[str, Objective]) -> None:
        """Set objective."""
        if isinstance(objective, str):
            self._objective = Objective(objective)
        else:
            self._objective = objective

    # pylint: disable=redefined-builtin
    def add_task(self, id: str, description: str, **kwargs) -> WorkflowNode:
        """Add a task node to the workflow."""
        node = WorkflowNode(id, "TASK", description, **kwargs)
        self.add_node(node)
        return node

    def add_decision(self, id: str, description: str, **kwargs) -> WorkflowNode:
        """Add a decision point to the workflow."""
        node = WorkflowNode(id, "DECISION", description, **kwargs)
        self.add_node(node)
        return node

    def add_transition(
        self,
        from_id: str,
        to_id: str,
        condition: Optional[str] = None,
        **kwargs
    ) -> WorkflowEdge:
        """Add a conditional transition between nodes."""
        edge = WorkflowEdge(from_id, to_id, condition, **kwargs)
        self.add_edge(edge)
        return edge

    def get_start(self) -> WorkflowNode:
        """Get the workflow's start node."""
        node = next(
            node for node in self.nodes.values()
            if node.type == "START"
        )
        return cast(WorkflowNode, node)

    def get_ends(self) -> List[WorkflowNode]:
        """Get all possible end nodes."""
        nodes = [
            node for node in self.nodes.values()
            if node.type == "END"
        ]
        return cast(List[WorkflowNode], nodes)

    def cursor(self) -> WorkflowCursor:
        """Create a new cursor for traversing the workflow."""
        return WorkflowCursor(self)

    def from_text(self, text: str) -> None:
        """Parse workflow from natural language text using LLM."""
        yaml_data = text_to_yaml(text)
        temp_workflow = self.from_yaml(yaml_data)
        self.nodes = temp_workflow.nodes
        self.edges = temp_workflow.edges

    def to_yaml(self, stream: Optional[TextIO] = None) -> Optional[str]:
        """Export workflow to YAML format."""
        data = {
            'name': self._objective.original if self._objective else 'Untitled',
            'objective': str(self._objective) if self._objective else None,
            'version': '1.0',
            'nodes': {},
            'edges': [],
            'metadata': {}
        }

        # Export nodes
        for node_id, node in self.nodes.items():
            node = cast(WorkflowNode, node)
            data['nodes'][node_id] = {
                'type': node.type,
                'description': node.description,
                'requires': node.requires,
                'provides': node.provides,
                'metadata': node.metadata
            }

        # Export edges
        for edge in self.edges:
            edge = cast(WorkflowEdge, edge)
            edge_data: Dict[str, Any] = {
                'from': edge.source,
                'to': edge.target
            }
            if edge.condition:
                edge_data['condition'] = edge.condition
            if edge.state_updates:
                edge_data['state_updates'] = edge.state_updates
            if edge.metadata:
                edge_data['metadata'] = edge.metadata
            data['edges'].append(edge_data)

        if stream:
            yaml.dump(data, stream, default_flow_style=False)
            return None
        return yaml.dump(data, default_flow_style=False)

    @classmethod
    def from_yaml(cls, stream: Union[str, TextIO, Path]) -> 'Workflow':
        """Create workflow from YAML specification."""
        # Handle different input types
        if isinstance(stream, Path):
            data = yaml.safe_load(stream.read_text())
        elif isinstance(stream, str):
            # Try to parse as YAML string first
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError:
                # If parsing fails, try as file path
                data = yaml.safe_load(Path(stream).read_text(encoding='utf-8'))
        else:
            data = yaml.safe_load(stream)

        # Validate against schema
        validate_workflow_yaml(data)
        
        workflow = cls(objective=data.get('objective'))
        
        # Create nodes
        for node_id, node_data in data['nodes'].items():
            if node_data['type'] == 'TASK':
                workflow.add_task(
                    id=node_id,
                    description=node_data['description'],
                    requires=node_data.get('requires', {}),
                    provides=node_data.get('provides', {}),
                    metadata=node_data.get('metadata', {})
                )
            elif node_data['type'] == 'DECISION':
                workflow.add_decision(
                    id=node_id,
                    description=node_data['description'],
                    requires=node_data.get('requires', {}),
                    provides=node_data.get('provides', {}),
                    metadata=node_data.get('metadata', {})
                )
            else:  # START/END nodes
                node = WorkflowNode(
                    node_id=node_id,
                    type=node_data['type'],
                    description=node_data['description'],
                    requires=node_data.get('requires', {}),
                    provides=node_data.get('provides', {}),
                    metadata=node_data.get('metadata', {})
                )
                workflow.add_node(node)

        # Create edges
        for edge_data in data['edges']:
            workflow.add_transition(
                from_id=edge_data['from'],
                to_id=edge_data['to'],
                condition=edge_data.get('condition'),
                state_updates=edge_data.get('state_updates', {}),
                metadata=edge_data.get('metadata', {})
            )

        return workflow