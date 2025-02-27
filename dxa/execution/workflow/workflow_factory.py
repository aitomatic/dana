"""Workflow factory for creating common workflow patterns."""

from typing import List, Optional, Union, Dict, cast
from pathlib import Path

from ..execution_factory import ExecutionFactory
from .workflow import Workflow
from ...common.graph import NodeType, Edge
from ..execution_types import Objective, ExecutionNode
from ..execution_config import ExecutionConfig

class WorkflowConfig(ExecutionConfig):
    """Workflow configuration for creating common workflow patterns."""

    @classmethod
    def get_base_path(cls) -> Path:
        """Get base path for configuration files."""
        return Path(__file__).parent

class WorkflowFactory(ExecutionFactory):
    """Factory for creating workflow patterns."""
    
    # Override class variables
    graph_class = Workflow
    config_class = WorkflowConfig
    
    # Add workflow-specific methods
    @classmethod
    def create_from_config(cls, name: str,
                           objective: Union[str, Objective],
                           role: Optional[str] = None,
                           custom_prompts: Optional[Dict[str, str]] = None) -> Workflow:
        """Create a workflow from named configuration."""
        graph = super().create_from_config(
            name=name,
            objective=objective,
            role=role,
            custom_prompts=custom_prompts
        )
        return cast(Workflow, graph)

    @classmethod
    def create_prosea_workflow(cls, objective: Union[str, Objective], 
                               agent_role: str = "ProSea Agent", 
                               custom_prompts: Optional[Dict[str, str]] = None) -> Workflow:
        """Create a Prosea workflow for given parameters."""
        return cls.create_workflow_by_name("basic.prosea", objective, agent_role, custom_prompts)

    @classmethod
    def create_sequential_workflow(cls, objective: Union[str, Objective], commands: List[str]) -> Workflow:
        """Create a sequential workflow from list of commands.  Sequential is treated special,
        in that the steps are passed in programmatically rather than hard-coded in the YAML file."""

        # First load the base sequential workflow
        workflow = cls.create_workflow_by_name("basic.sequential", objective)
        
        # Clear any existing edges (to ensure we don't have extras)
        workflow.edges = []
        
        # Create task nodes for each command
        prev_id = "START"
        for i, command in enumerate(commands):
            node_id = f"TASK_{i}"
            workflow.add_node(ExecutionNode(
                node_id=node_id,
                node_type=NodeType.TASK,
                description=str(command)
            ))
            workflow.add_edge(Edge(source=prev_id, target=node_id))
            prev_id = node_id

        workflow.add_edge(Edge(source=prev_id, target="END"))
        return workflow

    @classmethod
    def create_minimal_workflow(cls, objective: Optional[Union[str, Objective]] = None) -> Workflow:
        """Create minimal workflow with START -> TASK -> END.
        The task node will have the objective as its description.
        """
        return cls.create_workflow_by_name("basic.minimal", objective or "No objective provided")
    
    @classmethod
    def create_monitoring_workflow(cls,
                                   parameters: List[str],
                                   name: str = "monitoring",
                                   description: str = "") -> Workflow:
        """Create a monitoring workflow for given parameters."""
        # Create objective
        objective = Objective(description or f"Monitor {', '.join(parameters)}")
        
        # Load base monitoring workflow
        workflow = cls.create_workflow_by_name("automation/monitoring", objective)
        workflow.name = name
        
        # Update MONITOR node with parameters
        monitor_node = workflow.get_node_by_id("MONITOR")
        if monitor_node:
            monitor_node.metadata["parameters"] = parameters
        
        return workflow

    @classmethod
    def create_workflow_by_name(cls, workflow_name: str, 
                                objective: Union[str, Objective], 
                                agent_role: Optional[str] = None,
                                custom_prompts: Optional[Dict[str, str]] = None) -> Workflow:
        """Create a workflow by name."""
        # No need to normalize the name - just pass it through
        return cls.create_from_config(workflow_name, objective, agent_role, custom_prompts)

    @classmethod
    def create_default_workflow(cls, objective: Union[str, Objective], 
                                agent_role: str = "Default Workflow Agent", 
                                custom_prompts: Optional[Dict[str, str]] = None) -> Workflow:
        """Create a default workflow for given parameters.
        
        This workflow follows the standard problem-solving pattern:
        DEFINE -> RESEARCH -> STRATEGIZE -> EXECUTE -> EVALUATE
        
        Args:
            objective: The objective to accomplish
            agent_role: Optional role for the agent
            custom_prompts: Optional custom prompts to override defaults
            
        Returns:
            A configured default workflow
            
        Examples:
            >>> workflow = WorkflowFactory.create_default_workflow("Design a database schema")
            >>> workflow = WorkflowFactory.create_default_workflow(
            ...     "Create a marketing plan", 
            ...     agent_role="Marketing Specialist"
            ... )
        """
        return cls.create_from_config("default", objective, agent_role, custom_prompts)
