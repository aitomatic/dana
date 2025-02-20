"""Workflow factory for creating common workflow patterns."""

from pathlib import Path
from typing import List, Optional, Union, Dict
import yaml

from ..execution_graph import ExecutionGraph
from ..execution_types import Objective, ExecutionNode
from .workflow import Workflow
from ...common.graph import NodeType, Edge

class WorkflowFactory:
    """Factory for creating workflow patterns."""

    @classmethod
    def from_yaml(cls, yaml_data: Union[str, Dict, Path], name: Optional[str] = None) -> Workflow:
        """Create workflow from YAML data or file.
        
        Args:
            yaml_data: YAML data as string, dictionary, or file path
            name: Optional workflow name
            
        Returns:
            Workflow: New workflow instance
        """
        # Convert YAML data to sequential workflow for now
        # TODO: support more complex workflow patterns
        yaml_data = cls._create_sequential_workflow_from_yaml_steps(yaml_data)

        # Handle different input types
        if isinstance(yaml_data, (str, Path)):
            with open(yaml_data, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml_data

        # Create workflow
        workflow = Workflow(
            objective=Objective(data.get('objective', '')),
            name=data.get('name', 'unnamed_workflow')
        )

        # pylint: disable=protected-access
        ExecutionGraph._add_start_end_nodes(graph=workflow)

        # Remove the edge from START to END
        workflow.remove_edge_between("START", "END")

        # Add nodes
        prev_id = "START"
        for node_data in data.get('nodes', []):
            node_id = node_data['id']
            workflow.add_node(ExecutionNode(
                node_id=node_data['id'],
                node_type=NodeType[node_data['type']],
                description=node_data.get('description', ''),
                metadata=node_data.get('metadata', {})
            ))
            workflow.add_transition(prev_id, node_id)
            prev_id = node_id

        workflow.add_transition(prev_id, "END")

        return workflow

    @classmethod
    def create_sequential_workflow(cls, objective: Union[str, Objective], commands: List[str]) -> Workflow:
        """Create a sequential workflow from list of commands."""
        objective = Objective(objective) if isinstance(objective, str) else objective
        workflow = Workflow(objective)
        # pylint: disable=protected-access
        ExecutionGraph._add_start_end_nodes(graph=workflow)

        # Remove the edge from START to END
        workflow.remove_edge_between("START", "END")

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
        # pylint: disable=protected-access
        ExecutionGraph._add_start_end_nodes(graph=workflow)

        # Remove the edge from START to END
        workflow.remove_edge_between("START", "END")

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

    @classmethod
    def _create_sequential_workflow_from_yaml_steps(cls, workflow_yaml: str) -> Dict:
        """Convert simple step-based workflow YAML into a sequential workflow structure.
        
        This method takes a simplified YAML format that describes workflow steps organized by process
        and converts it into the full workflow structure required by from_yaml().
        
        Args:
            workflow_yaml (str): YAML content as string containing workflow steps
                               in format:
                               workflow-name:
                                 process-name:
                                     - "Step 1"
                                     - "Step 2"
            
        Returns:
            dict: Workflow data with nodes and edges in the format:
            {
                'name': 'workflow_name',
                'description': 'workflow description',
                'nodes': [{id, type, description, metadata}],
                'edges': [{source, target, metadata}]
            }
            
        Raises:
            ValueError: If the input YAML is empty or has invalid structure
        """
        if not workflow_yaml or not workflow_yaml.strip():
            raise ValueError("Empty workflow YAML")
            
        raw_data = yaml.safe_load(workflow_yaml)
        if not raw_data or not isinstance(raw_data, dict):
            raise ValueError("Invalid workflow YAML structure")
        
        # Get the workflow name (first key in the YAML)
        try:
            workflow_name = next(iter(raw_data))
            processes = raw_data[workflow_name]
        except (StopIteration, KeyError):
            raise ValueError("Invalid workflow YAML structure")
        
        # Create nodes list starting with START
        nodes = [
            {"id": "START", "type": "START", "description": "Begin workflow"}
        ]
        
        # Extract all steps sequentially
        step_counter = 1
        for process_name, steps in processes.items():
            if isinstance(steps, list):
                for step in steps:
                    nodes.append({
                        "id": f"STEP_{step_counter}",
                        "type": "TASK",
                        "description": str(step),
                        "metadata": {"process": process_name}
                    })
                    step_counter += 1
        
        if len(nodes) == 1:  # Only START node exists
            raise ValueError("No valid steps found in workflow")
        
        # Add END node
        nodes.append({"id": "END", "type": "END", "description": "End workflow"})
        
        # Create sequential edges
        edges = []
        for i in range(len(nodes) - 1):
            edges.append({
                "source": nodes[i]["id"],
                "target": nodes[i + 1]["id"]
            })
        
        return {
            "name": workflow_name,
            "objective": f"Sequential workflow for {workflow_name}",
            "nodes": nodes,
            "edges": edges
        }
