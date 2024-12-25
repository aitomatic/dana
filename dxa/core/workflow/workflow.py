"""Base workflow implementation using directed graphs."""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union, cast, TextIO
from dataclasses import dataclass, field
import yaml
from ...common.graph import DirectedGraph, Node, Edge
from ..types import Objective
from ..resource import LLMResource

@dataclass
class WorkflowNode(Node):
    """Workflow step node."""
    requires: Optional[Dict[str, Any]] = field(default_factory=dict)  # Required resources/state
    provides: Optional[Dict[str, Any]] = field(default_factory=dict)  # Produced outputs/state
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)  # Additional metadata

@dataclass 
class WorkflowEdge(Edge):
    """Workflow transition edge."""
    condition: Optional[str] = None  # Condition for taking this path
    state_updates: Optional[Dict[str, Any]] = field(default_factory=dict)  # State changes on transition
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

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
    
    @property
    def nodes(self) -> Dict[str, WorkflowNode]:
        """Get nodes."""
        return cast(Dict[str, WorkflowNode], self._nodes)
    
    @nodes.setter
    def nodes(self, nodes: Dict[str, WorkflowNode]) -> None:
        """Set nodes."""
        self._nodes = cast(Dict[str, Node], nodes)
    
    @property
    def edges(self) -> List[WorkflowEdge]:
        """Get edges."""
        return cast(List[WorkflowEdge], self._edges)
    
    @edges.setter
    def edges(self, edges: List[WorkflowEdge]) -> None:
        """Set edges."""
        self._edges = cast(List[Edge], edges)

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
            node for node in self._nodes.values()
            if node.type == "START"
        )
        return cast(WorkflowNode, node)

    def get_ends(self) -> List[WorkflowNode]:
        """Get all possible end nodes."""
        nodes = [
            node for node in self._nodes.values()
            if node.type == "END"
        ]
        return cast(List[WorkflowNode], nodes)

    def cursor(self) -> WorkflowCursor:
        """Create a new cursor for traversing the workflow."""
        return WorkflowCursor(self)

    def from_text(self, text: str) -> None:
        """Parse workflow from natural language text using LLM."""
        yaml_data = Workflow.text_to_yaml(text)
        temp_workflow = Workflow.from_yaml(yaml_data)
        # pylint: disable=protected-access
        self._nodes = temp_workflow._nodes
        self._edges = temp_workflow._edges

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
        for node_id, node in self._nodes.items():
            node = cast(WorkflowNode, node)
            data['nodes'][node_id] = {
                'type': node.type,
                'description': node.description,
                'requires': node.requires,
                'provides': node.provides,
                'metadata': node.metadata
            }

        # Export edges
        for edge in self._edges:
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
        Workflow.validate_yaml(yaml_data=data)
        
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
                # pylint: disable=unexpected-keyword-arg
                node = WorkflowNode(node_id, node_data['type'], node_data['description'])
                node.requires = node_data.get('requires', {})
                node.provides = node_data.get('provides', {})
                node.metadata = node_data.get('metadata', {})
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

    def get_edges_from(self, node_id: str) -> List[WorkflowEdge]:
        """Get all edges from a node."""
        edges = [edge for edge in self._edges if edge.source == node_id]
        return cast(List[WorkflowEdge], edges)

    @classmethod
    def text_to_yaml(cls, text: str) -> str:
        """Convert natural language text to workflow YAML using LLM."""
        llm = LLMResource()
        
        prompt = f"""Convert the following natural language workflow description into YAML format.
The YAML should define nodes (tasks, decisions) and edges (transitions) in the workflow.
Include any implicit state requirements and effects.

Description:
{text}

Generate valid YAML that follows this structure:
    - nodes: dictionary of workflow nodes (START, END, TASK, DECISION)
    - edges: list of transitions between nodes
    - metadata: optional workflow metadata

Example format:
    ```yaml
    nodes:
    start:
        type: START
        description: "Begin workflow"
    task_1:
        type: TASK
        description: "First task"
        requires: {{input: str}}
        provides: {{output: str}}
    edges:
    - from: start
        to: task_1
    ```
"""

        # Get YAML from LLM
        response = llm.do_query({"prompt": prompt})
        
        # Extract YAML from response
        yaml_text = response["content"].strip()
        if "```yaml" in yaml_text:
            yaml_text = yaml_text.split("```yaml")[1].split("```")[0]
        
        # Validate YAML structure
        try:
            Workflow.validate_yaml(yaml_text)
            return yaml_text
        except Exception as e:
            raise ValueError(f"LLM generated invalid workflow YAML: {e}") from e

    def to_ascii_art(self) -> str:
        """Generate ASCII art representation of the workflow."""
        # pylint: disable=invalid-name
        TAB_SIZE = 8
        
        # pylint: disable=line-too-long
        # flake8: noqa: E501
        def _node_to_ascii(node_id: str, level: int = 0, offset: int = 0, branch_processed: set[str] | None = None) -> tuple[list[str], int]:

            """Process node to ASCII art, tracking processed nodes per branch."""
            if branch_processed is None:
                branch_processed = set()
            
            if node_id in branch_processed:
                return ([f"{' ' * offset}..."], 3)
            
            node = self._nodes[node_id]
            branch_processed.add(node_id)  # Only mark as processed for this branch
            
            # Format node
            if node.type == "START":
                node_str = "START"
            elif node.type == "END":
                node_str = "END"
            elif node.type == "DECISION":
                node_str = f"<{node.description}>"
            else:
                node_str = f"[{node.description}]"
                
            edges = self.get_edges_from(node_id)
            if not edges:
                return ([f"{' ' * offset}{node_str}"], len(node_str))
                
            result = [f"{' ' * offset}{node_str}"]
            
            if len(edges) == 1:
                # Single path
                edge = edges[0]
                result.append(f"{' ' * offset} |")
                if edge.condition or edge.state_updates:
                    details = []
                    if edge.condition:
                        details.append(edge.condition)
                    if edge.state_updates:
                        details.extend(f"{k}={v}" for k, v in edge.state_updates.items())
                    result.append(f"{' ' * offset} | [{', '.join(details)}]")
                result.append(f"{' ' * offset} v")
                child_lines, width = _node_to_ascii(edge.target, level + 1, offset, branch_processed.copy())
                result.extend(child_lines)
                return result, max(len(node_str), width)
            else:
                # Multiple paths
                branch_count = len(edges)
                path_width = TAB_SIZE * 4
                
                # Draw initial branches with proper spacing
                branch_line = f"{' ' * offset} |"
                for i in range(branch_count - 1):
                    branch_line += " " * (path_width - 1) + "\\"
                result.append(branch_line)
                
                # Draw conditions with proper alignment
                condition_line = ""
                for i, edge in enumerate(edges):
                    if edge.condition or edge.state_updates:
                        details = []
                        if edge.condition:
                            details.append(edge.condition)
                        if edge.state_updates:
                            details.extend(f"{k}={v}" for k, v in edge.state_updates.items())
                        condition_str = f"[{', '.join(details)}]"
                        
                        if i == 0:
                            condition_line = f"{' ' * offset} {condition_str}"
                        else:
                            padding = " " * (offset + i * path_width - len(condition_line))
                            condition_line += padding + condition_str
                if condition_line:
                    result.append(condition_line)
                
                # Draw arrows aligned with conditions
                arrow_line = f"{' ' * offset} v"
                for i in range(branch_count - 1):
                    arrow_padding = " " * (path_width - 1)
                    arrow_line += arrow_padding + "v"
                result.append(arrow_line)
                
                # Process children with separate branch_processed sets
                child_results = []
                max_height = 0
                for i, edge in enumerate(edges):
                    child_offset = offset + i * path_width
                    # Use a copy of branch_processed for each branch
                    child_lines, _ = _node_to_ascii(edge.target, level + 1, child_offset, branch_processed.copy())
                    child_results.append(child_lines)
                    max_height = max(max_height, len(child_lines))
                
                # Combine results remains the same
                for i in range(max_height):
                    line_parts = []
                    for j, child_lines in enumerate(child_results):
                        if i < len(child_lines):
                            if j == 0:
                                line_parts.append(child_lines[i])
                            else:
                                padding = " " * (offset + j * path_width - len("".join(line_parts)))
                                line_parts.append(padding + child_lines[i].lstrip())
                    result.append("".join(line_parts))
                
                return result, offset + path_width * branch_count
        
        lines, _ = _node_to_ascii(self.get_start().node_id)
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Generate Mermaid flowchart representation of the workflow.
        
        Example:
        ```mermaid
        graph TD
            start([START])
            task1["Download data"]
            decision1{"Check data"}
            task2["Process data"]
            end([END])
            
            start --> task1
            task1 --> decision1
            decision1 -->|"data valid"| task2
            decision1 -->|"data invalid"| task1
            task2 --> end
        ```
        """
        lines = ["graph TD"]
        
        # Add node definitions with proper shapes
        for node_id, node in self._nodes.items():
            if node.type == "START" or node.type == "END":
                lines.append(f"    {node_id}([{node.description}])")
            elif node.type == "DECISION":
                lines.append(f"    {node_id}{{\"{node.description}\"}}")
            else:  # TASK
                lines.append(f"    {node_id}[\"{node.description}\"]")
        
        # Add edges with conditions
        for edge in self._edges:
            if edge.condition:
                lines.append(f"    {edge.source} -->|\"{edge.condition}\"| {edge.target}")
            else:
                lines.append(f"    {edge.source} --> {edge.target}")
        
        return "\n".join(lines)

    @classmethod
    def validate_yaml(cls, yaml_text: str | None = None, yaml_data: dict | None = None) -> None:
        """Validate workflow YAML data structure.
        
        Args:
            data: Dictionary containing workflow YAML data
            
        Raises:
            ValueError: If validation fails
        """
        if yaml_data:
            data = yaml_data
        elif yaml_text:
            data = yaml.safe_load(yaml_text)
        else:
            raise ValueError("No YAML data provided")

        # Validate basic structure
        if not isinstance(data, dict):
            raise ValueError("Workflow YAML must be a dictionary")
        
        required_keys = {'nodes', 'edges'}
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        # Validate nodes
        if not isinstance(data['nodes'], dict):
            raise ValueError("Nodes must be a dictionary")
        
        valid_node_types = {'START', 'END', 'TASK', 'DECISION'}
        for node_id, node_data in data['nodes'].items():
            if not isinstance(node_data, dict):
                raise ValueError(f"Node {node_id} data must be a dictionary")
            
            # Required fields
            if 'type' not in node_data:
                raise ValueError(f"Node {node_id} missing required field 'type'")
            if node_data['type'] not in valid_node_types:
                raise ValueError(f"Node {node_id} has invalid type: {node_data['type']}")
            if 'description' not in node_data:
                raise ValueError(f"Node {node_id} missing required field 'description'")
            
            # Optional fields must be dictionaries if present
            for fld in ['requires', 'provides', 'metadata']:
                if fld in node_data and not isinstance(node_data[fld], dict):
                    raise ValueError(f"Node {node_id} field '{fld}' must be a dictionary")
                
        # Validate edges
        if not isinstance(data['edges'], list):
            raise ValueError("Edges must be a list")
        
        for i, edge in enumerate(data['edges']):
            if not isinstance(edge, dict):
                raise ValueError(f"Edge {i} must be a dictionary")
            
            # Required fields
            if 'from' not in edge:
                raise ValueError(f"Edge {i} missing required field 'from'")
            if 'to' not in edge:
                raise ValueError(f"Edge {i} missing required field 'to'")
            
            # Validate edge references existing nodes
            if edge['from'] not in data['nodes']:
                raise ValueError(f"Edge {i} references non-existent source node: {edge['from']}")
            if edge['to'] not in data['nodes']:
                raise ValueError(f"Edge {i} references non-existent target node: {edge['to']}")
            
            # Optional fields must be of correct type
            if 'condition' in edge and not isinstance(edge['condition'], str):
                raise ValueError(f"Edge {i} condition must be a string")
            if 'state_updates' in edge and not isinstance(edge['state_updates'], dict):
                raise ValueError(f"Edge {i} state_updates must be a dictionary")
            if 'metadata' in edge and not isinstance(edge['metadata'], dict):
                raise ValueError(f"Edge {i} metadata must be a dictionary")
            
        # Validate workflow has exactly one START and at least one END node
        start_nodes = [n for n in data['nodes'].values() if n['type'] == 'START']
        if len(start_nodes) != 1:
            raise ValueError(f"Workflow must have exactly one START node, found {len(start_nodes)}")
        
        end_nodes = [n for n in data['nodes'].values() if n['type'] == 'END']
        if not end_nodes:
            raise ValueError("Workflow must have at least one END node")
