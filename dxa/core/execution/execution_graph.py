"""Execution graph implementation."""

from typing import Dict, Any, Optional, Union, List, cast, TextIO, TYPE_CHECKING
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from ...common.graph import DirectedGraph, Node, Edge, NodeType
from .execution_types import (
    Objective, ExecutionNode,
    ExecutionNodeStatus, ExecutionSignal, ExecutionSignalType,
    ExecutionEdge
)
if TYPE_CHECKING:
    from .execution_context import ExecutionContext

# pylint: disable=too-many-public-methods
@dataclass
class ExecutionGraph(DirectedGraph):
    """Base graph for all execution layers (WHY/WHAT/HOW)."""
    
    def __init__(self, 
                 objective: Optional[Union[str, Objective]] = None, 
                 layer: str = "execution",
                 name: Optional[str] = None):
        super().__init__()
        if isinstance(objective, str):
            self._objective = Objective(objective)
        else:
            self._objective = objective
        self.name = name
        self._metadata = {"layer": layer}
        self.history: List[Dict] = []
        self._context: Optional['ExecutionContext'] = None
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, metadata: Dict[str, Any]) -> None:
        """Set metadata."""
        self._metadata = metadata

    @property
    def nodes(self) -> Dict[str, ExecutionNode]:
        """Get all nodes in the graph."""
        return cast(Dict[str, ExecutionNode], super().nodes)
    
    @nodes.setter
    def nodes(self, nodes: Dict[str, ExecutionNode]) -> None:
        """Set all nodes in the graph."""
        super().nodes = cast(Dict[str, Node], nodes)

    @property
    def edges(self) -> List[ExecutionEdge]:
        """Get all edges in the graph."""
        return cast(List[ExecutionEdge], super().edges)
    
    @edges.setter
    def edges(self, edges: List[ExecutionEdge]) -> None:
        """Set all edges in the graph."""
        super().edges = cast(List[Edge], edges)

    def get_start_node(self) -> Optional[ExecutionNode]:
        """Get the start node, meaning the node with type START."""
        return next((node for node in self.nodes.values() if node.node_type == NodeType.START), None)
    
    @classmethod
    def from_yaml(cls, stream: Union[str, TextIO, Path]) -> 'ExecutionGraph':
        """Create graph from YAML specification."""
        return cast(cls, DirectedGraph.from_yaml(stream))

    def add_step(self, step_id: str, description: str, **kwargs) -> ExecutionNode:
        """Add an execution step."""
        node = ExecutionNode(
            node_id=step_id,
            node_type=NodeType.TASK,
            description=description,
            status=ExecutionNodeStatus.PENDING,
            metadata=kwargs.get('metadata', {}),
            **kwargs
        )
        self.add_node(node)
        return node

    def get_step(self, step_id: str) -> Optional[ExecutionNode]:
        """Get step by ID."""
        return cast(ExecutionNode, self.get_node_by_id(step_id))

    def get_active_steps(self) -> List[ExecutionNode]:
        """Get all steps currently in progress."""
        return [
            cast(ExecutionNode, node) for node in self.nodes.values()
            if node.status == ExecutionNodeStatus.IN_PROGRESS
        ]

    @property
    def context(self) -> Optional['ExecutionContext']:
        """Get execution context."""
        return self._context

    @context.setter 
    def context(self, context: 'ExecutionContext') -> None:
        """Set execution context."""
        self._context = context

    def process_signal(self, signal: ExecutionSignal) -> List[ExecutionSignal]:
        """Process execution signals."""
        new_signals = []
        
        if signal.type == ExecutionSignalType.STATE_CHANGE:
            # Common state updates
            self.metadata.update(signal.content.get("metadata", {}))
            
        elif signal.type == ExecutionSignalType.COMPLETE:
            # Common step completion handling
            if node_id := signal.content.get("node"):
                self.update_node_status(node_id, ExecutionNodeStatus.COMPLETED)
                new_signals.append(ExecutionSignal(
                    type=ExecutionSignalType.STATE_CHANGE,
                    content={
                        "component": self.metadata.get("layer", "execution"),
                        "type": "step_completed",
                        "node": node_id
                    }
                ))
        
        return new_signals

    def to_ascii_art(self) -> str:
        """Generate ASCII art with execution status."""
        art = super().to_ascii_art()
        status_summary = "\nStatus:\n"
        for node in self.nodes.values():
            node = cast(ExecutionNode, node)
            status_summary += f"  {node.node_id}: {node.status.value}\n"
        return art + status_summary

    def update_node_status(self, node_id: str, status: ExecutionNodeStatus) -> None:
        """Update node status and record in history."""
        if node_id in self.nodes:
            node = cast(ExecutionNode, self.nodes[node_id])
            old_status = node.status
            node.status = status
            self.history.append({
                'timestamp': datetime.now(),
                'node': node_id,
                'status_change': {
                    'from': old_status,
                    'to': status
                }
            })

    # pylint: disable=unused-argument
    def get_valid_transitions(self, node_id: str, context: Optional['ExecutionContext'] = None) -> List[ExecutionNode]:
        """Get valid next nodes based on edge conditions."""
        valid_nodes = []
        outgoing = cast(List[ExecutionEdge], self._outgoing[node_id])
        for edge in outgoing:
            # For now, treat no condition as always valid
            if not edge.condition:
                target = cast(ExecutionNode, self.nodes[edge.target])
                valid_nodes.append(target)
        return valid_nodes

    @property
    def objective(self) -> Optional[Objective]:
        """Get the objective of the execution graph."""
        return self._objective

    @objective.setter
    def objective(self, value: Optional[Objective]) -> None:
        """Set the objective."""
        self._objective = value

    def get_terminal_nodes(self) -> List[ExecutionNode]:
        """Get all terminal (end) nodes."""
        return [
            cast(ExecutionNode, node) for node in self.nodes.values()
            if node.node_type == NodeType.END
        ]

    def is_complete(self) -> bool:
        """Check if execution is complete."""
        return all(
            cast(ExecutionNode, node).status == ExecutionNodeStatus.COMPLETED
            for node in self.nodes.values()
            if node.node_type != NodeType.END
        )

    def validate(self) -> None:
        """Validate execution graph structure."""
        # Check for single start node
        start_nodes = [
            node for node in self.nodes.values()
            if cast(ExecutionNode, node).node_type == NodeType.START
        ]
        if len(start_nodes) != 1:
            raise ValueError(f"Graph must have exactly one START node, found {len(start_nodes)}")
        
        # Check for at least one end node
        end_nodes = self.get_terminal_nodes()
        if not end_nodes:
            raise ValueError("Graph must have at least one END node")
        
        # Check for cycles (already handled by DirectedGraph.__iter__)
        try:
            list(iter(self))
        except ValueError as e:
            raise ValueError("Invalid graph structure: " + str(e)) from e

        # Add buffer validation
        for node in self.nodes.values():
            if node.buffer_config["enabled"]:
                if node.buffer_config["size"] <= 0:
                    raise ValueError(f"Invalid buffer size for node {node.node_id}")
                if node.buffer_config["mode"] not in ["streaming", "batch"]:
                    raise ValueError(f"Invalid buffer mode for node {node.node_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert execution graph to dictionary representation."""
        return {
            'objective': self._objective.current if self._objective else None,
            'metadata': self.metadata,
            'nodes': {
                node_id: {
                    'node_type': cast(ExecutionNode, node).node_type,
                    'status': cast(ExecutionNode, node).status.value,
                    'description': node.description,
                    'metadata': node.metadata
                }
                for node_id, node in self.nodes.items()
            },
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'condition': edge.condition,
                    'metadata': edge.metadata
                }
                for edge in self.edges
            ],
            'history': self.history
        }

    def update_graph(self, new_graph: 'ExecutionGraph', reason: str) -> None:
        """Update graph while preserving execution state."""
        self.history.append({
            'timestamp': datetime.now(),
            'reason': reason,
            'previous': self.to_dict()
        })
        self._merge_graph(new_graph)

    def _merge_graph(self, new_graph: 'ExecutionGraph') -> None:
        """Merge new graph while preserving node states."""
        self._objective = new_graph.objective
        self.metadata.update(new_graph.metadata)
        
        # Update nodes preserving states
        for node_id, new_node in new_graph.nodes.items():
            if node_id in self.nodes:
                # Preserve execution state
                current = cast(ExecutionNode, self.nodes[node_id])
                new = cast(ExecutionNode, new_node)
                new.status = current.status
                new.result = current.result
            self.nodes[node_id] = new_node
        
        self.edges = new_graph.edges
        
        # Preserve buffer configuration
        for node_id, new_node in new_graph.nodes.items():
            if node_id in self.nodes:
                current = cast(ExecutionNode, self.nodes[node_id])
                new = cast(ExecutionNode, new_node)
                new.buffer_config = current.buffer_config

    def create_signal(self, signal_type: str, content: Any) -> ExecutionSignal:
        """Create a signal with proper typing."""
        return ExecutionSignal(ExecutionSignalType[signal_type], content)

    async def validate_result(self, result: Any) -> bool:
        """Validate execution result. Override for specific validation."""
        return True

    def add_transition(self, source: str, target: str, condition: Optional[str] = None, **kwargs) -> ExecutionEdge:
        """Add a transition between steps."""
        edge = ExecutionEdge(
            source=source,
            target=target,
            condition=condition,
            **kwargs
        )
        self.add_edge(edge)
        return edge

    def add_dependency(self, source: str, target: str, **kwargs) -> ExecutionEdge:
        """Add dependency between nodes."""
        return self.add_transition(source, target, metadata={"type": "dependency", **kwargs})

    def get_dependencies(self, node_id: str) -> List[ExecutionNode]:
        """Get nodes that must complete before this one."""
        return [
            self.nodes[edge.source] for edge in self._incoming[node_id]
            if edge.metadata.get("type") == "dependency"
        ]

    def add_validation(self, node_id: str, validation_type: str) -> None:
        """Add validation requirement to node."""
        node = self.get_step(node_id)
        if node:
            node.metadata["validation"] = validation_type

    def update_pattern_state(self, state: Dict[str, Any]) -> None:
        """Update pattern-specific state."""
        self.metadata["pattern_state"] = state
        self.history.append({
            "timestamp": datetime.now(),
            "type": "pattern_update",
            "state": state
        })

    # def get_start_cursor(self) -> 'Cursor':
    #     """Get cursor starting at START type node."""
    #     start_node = next((node for node in self.nodes.values() 
    #                       if node.node_type == NodeType.START), None)
    #     if not start_node:
    #         raise ValueError("Graph has no START node")
    #     return self.cursor(start_node)

    # def get_end_nodes(self) -> List[ExecutionNode]:
    #     """Get all END type nodes."""
    #     return [node for node in self.nodes.values() 
    #             if node.node_type == NodeType.END]
