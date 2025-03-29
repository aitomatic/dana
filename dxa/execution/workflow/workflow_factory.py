"""Factory for creating workflow graphs."""

from typing import Dict, Any, Optional, Union, cast, List
from pathlib import Path

from ..execution_types import Objective, ExecutionNode
from ..execution_factory import ExecutionFactory
from .workflow import Workflow
from ...common.graph import NodeType

class WorkflowFactory(ExecutionFactory[Workflow]):
    """Creates workflow graph instances."""
    
    # Override class variables
    graph_class = Workflow
    
    @classmethod
    def create_workflow(
        cls, 
        objective: Objective, 
        name: Optional[str] = None
    ) -> Workflow:
        """Create a workflow instance."""
        return cast(Workflow, cls.create_basic_graph(objective, name))
        
    @classmethod
    def create_workflow_by_name(
        cls,
        name: str,
        objective: Union[str, Objective],
        role: Optional[str] = None,
        custom_prompts: Optional[Dict[str, str]] = None,
        config_dir: Optional[Union[str, Path]] = None
    ) -> Workflow:
        """Create a workflow from a named configuration."""
        return cast(Workflow, cls.create_from_config(
            config_name=name,
            objective=objective,
            role=role,
            custom_prompts=custom_prompts,
            config_dir=config_dir
        ))
        
    @classmethod
    def create_default_workflow(cls, objective: Union[str, Objective]) -> Workflow:
        """Create a standard workflow with default structure."""
        if not isinstance(objective, Objective):
            objective = Objective(objective)
            
        workflow = cls.create_basic_graph(objective)
        
        # Add default nodes
        task_node = ExecutionNode(
            node_id="task",
            node_type=NodeType.TASK,
            description="Execute task"
        )
        workflow.add_node(task_node)
        
        # Connect START → task → END
        workflow.add_edge_between("start", task_node.node_id)
        workflow.add_edge_between(task_node.node_id, "end")
        
        return cast(Workflow, workflow)
        
    @classmethod
    def create_basic_workflow(
        cls,
        objective: Union[str, Objective],
        commands: List[str]
    ) -> Workflow:
        """Create a workflow with sequential tasks.
        
        Args:
            objective: Workflow objective
            commands: List of task descriptions
            
        Returns:
            Workflow: A workflow with sequential tasks
        """
        # Create task nodes from commands
        nodes = [
            ExecutionNode(
                node_id=f"TASK_{i}",
                node_type=NodeType.TASK,
                description=command
            )
            for i, command in enumerate(commands)
        ]
        
        # Use base class method to create sequential graph
        return cast(Workflow, cls.create_sequential_graph(
            nodes=nodes,
            objective=objective
        ))
        
    @classmethod
    def _add_edges_to_graph(
        cls,
        workflow: Workflow,
        data: Dict[str, Any],
        node_ids: List[str]
    ) -> None:
        """Add edges to workflow from YAML data.
        
        Args:
            workflow: The workflow to add edges to
            data: YAML data containing edge definitions
            node_ids: List of valid node IDs in the workflow
        """
        if "edges" not in data:
            return
            
        for edge_data in data["edges"]:
            source = edge_data.get("source")
            target = edge_data.get("target")
            
            if not source or not target:
                continue
                
            if source not in node_ids or target not in node_ids:
                continue
                
            workflow.add_edge_between(source, target)
            
    @classmethod
    def from_yaml(cls, data: Dict[str, Any], objective: Optional[Objective] = None) -> Workflow:
        """Create a workflow from YAML data."""
        if not objective and "objective" in data:
            objective = Objective(data["objective"])
        workflow = cls.create_basic_graph(objective)
        
        # Store prompts in metadata if present
        if "prompts" in data:
            workflow.metadata["prompts"] = data["prompts"]
            
        # Add nodes
        node_ids = []
        if "nodes" in data:
            for node_data in data["nodes"]:
                node = ExecutionNode(
                    node_id=node_data["id"],
                    node_type=NodeType[node_data["type"].upper()],
                    description=node_data.get("description", "")
                )
                workflow.add_node(node)
                node_ids.append(node.node_id)
                
        # Add edges
        cls._add_edges_to_graph(workflow, data, node_ids)
        
        return cast(Workflow, workflow)
