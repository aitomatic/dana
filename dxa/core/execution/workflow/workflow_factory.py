"""Workflow factory for creating common workflow patterns."""

from pathlib import Path
from typing import List, Optional, Union, Dict
import yaml

from ..execution_types import Objective, ExecutionNode
from .workflow import Workflow
from ....common.graph import NodeType, Edge

class WorkflowFactory:
    """Factory for creating workflow patterns."""

    @classmethod
    def from_yaml(cls, yaml_data: Union[str, Dict, Path]) -> Workflow:
        """Create workflow from YAML data or file."""
        # Handle different input types
        if isinstance(yaml_data, (str, Path)):
            with open(yaml_data, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml_data

        # Create workflow
        workflow = Workflow(
            objective=Objective(data.get('description', '')),
            name=data.get('name', 'unnamed_workflow')
        )

        # Add nodes
        for node_data in data.get('nodes', []):
            node = ExecutionNode(
                node_id=node_data['id'],
                node_type=NodeType[node_data['type']],
                description=node_data.get('description', ''),
                metadata=node_data.get('metadata', {})
            )
            workflow.add_node(node)

        # Add edges
        for edge_data in data.get('edges', []):
            edge = Edge(
                source=edge_data['source'],
                target=edge_data['target'],
                metadata=edge_data.get('metadata', {})
            )
            workflow.add_edge(edge)

        return workflow

    @classmethod
    def _add_start_end_nodes(cls, workflow: Workflow) -> None:
        """Add START and END nodes to workflow."""
        workflow.add_node(ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description="Begin workflow"
        ))
        workflow.add_node(ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description="End workflow"
        ))

    @classmethod
    def create_sequential_workflow(cls, objective: Union[str, Objective], commands: List[str]) -> Workflow:
        """Create a sequential workflow from list of commands."""
        objective = Objective(objective) if isinstance(objective, str) else objective
        workflow = Workflow(objective)
        cls._add_start_end_nodes(workflow)

        # Create task nodes for each command
        prev_id = "START"
        for i, command in enumerate(commands):
            node_id = f"TASK_{i}"
            workflow.add_node(ExecutionNode(
                node_id=node_id,
                node_type=NodeType.TASK,
                description=str(command)
            ))
            workflow.add_transition(prev_id, node_id)
            prev_id = node_id

        workflow.add_transition(prev_id, "END")
        return workflow

    @classmethod
    def create_minimal_workflow(cls, objective: Optional[Union[str, Objective]] = None) -> Workflow:
        """Create minimal workflow with START -> TASK -> END.
        The task node will have the objective as its description.
        """
        objective = Objective(objective) if isinstance(objective, str) else objective
        workflow = Workflow(objective)
        cls._add_start_end_nodes(workflow)

        # Add task node
        workflow.add_node(ExecutionNode(
            node_id="PERFORM_TASK",
            node_type=NodeType.TASK,
            description=objective.original if objective else ""
        ))

        workflow.add_transition("START", "PERFORM_TASK")
        workflow.add_transition("PERFORM_TASK", "END")

        return workflow

    @classmethod
    def create_monitoring_workflow(cls,
                                   parameters: List[str],
                                   name: str = "monitoring",
                                   description: str = "") -> Workflow:
        """Create a monitoring workflow for given parameters."""
        workflow = Workflow(
            objective=Objective(description or f"Monitor {', '.join(parameters)}"),
            name=name
        )

        # Add standard monitoring nodes
        nodes = {
            "START": ExecutionNode(
                node_id="START",
                node_type=NodeType.START,
                description="Begin monitoring"
            ),
            "MONITOR": ExecutionNode(
                node_id="MONITOR",
                node_type=NodeType.TASK,
                description="Monitor parameters",
                metadata={"parameters": parameters}
            ),
            "CHECK": ExecutionNode(
                node_id="CHECK",
                node_type=NodeType.CONDITION,
                description="Check parameter values"
            ),
            "DIAGNOSE": ExecutionNode(
                node_id="DIAGNOSE",
                node_type=NodeType.TASK,
                description="Diagnose issues"
            ),
            "END": ExecutionNode(
                node_id="END",
                node_type=NodeType.END,
                description="End monitoring cycle"
            )
        }

        # Add all nodes
        for node in nodes.values():
            workflow.add_node(node)

        # Add edges with conditions
        edges = [
            Edge("START", "MONITOR"),
            Edge("MONITOR", "CHECK"),
            Edge("CHECK", "MONITOR", {"condition": "parameters_normal"}),
            Edge("CHECK", "DIAGNOSE", {"condition": "parameters_abnormal"}),
            Edge("DIAGNOSE", "END")
        ]

        for edge in edges:
            workflow.add_edge(edge)

        return workflow
