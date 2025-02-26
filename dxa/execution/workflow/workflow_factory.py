"""Workflow factory for creating common workflow patterns."""

from typing import List, Optional, Union, Dict
from pathlib import Path
import yaml
from .workflow import Workflow
from ...common.graph import NodeType, Edge
from ..execution_types import Objective, ExecutionNode
from .workflow_config import WorkflowConfig

class WorkflowFactory:
    """Factory for creating workflow patterns."""

    @classmethod
    def from_yaml(cls, yaml_data: Union[str, Dict, Path], 
                  objective: Optional[Objective] = None,
                  custom_prompts: Optional[Dict[str, str]] = None) -> Workflow:
        """Create workflow from YAML data or file."""
        # Handle different input types
        config_path = None
        if isinstance(yaml_data, (str, Path)):
            if isinstance(yaml_data, str) and not Path(yaml_data).exists():
                # Assume it's a workflow name
                config_path = WorkflowConfig.get_config_path(yaml_data)
            else:
                config_path = str(yaml_data)

            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml_data

        print(f">>>>>>>>>>>>>>Path: {config_path}")

        # Create workflow
        workflow = Workflow(
            objective=objective or Objective(data.get('description', '')),
            name=data.get('name', 'unnamed_workflow')
        )
        
        # Process nodes
        nodes_data = data.get('nodes', [])
        node_ids = []
        
        # Check if START and END nodes exist
        has_start = any(node.get('id') == 'START' for node in nodes_data)
        has_end = any(node.get('id') == 'END' for node in nodes_data)
        
        # Add START node if it doesn't exist
        if not has_start:
            start_node = ExecutionNode(
                node_id="START",
                node_type=NodeType.START,
                description="Begin workflow"
            )
            workflow.add_node(start_node)
            node_ids.append("START")
        
        # Process nodes from YAML
        for node_data in nodes_data:
            description = node_data.get('description', '')
            node_id = node_data['id']
            node_ids.append(node_id)
            
            # Determine node type
            if 'type' not in node_data:
                print(f"Warning: Node '{node_id}' is missing 'type' field, defaulting to TASK")
                node_type = NodeType.TASK
            else:
                node_type = NodeType[node_data['type']]

            # Prepare metadata
            metadata = node_data.get('metadata', {})

            # Ensure planning and reasoning strategies are included in metadata
            # Standardize on 'planning' and 'reasoning' field names
            if 'planning' in node_data:
                metadata['planning'] = node_data['planning']
            else:
                metadata['planning'] = 'DEFAULT'

            if 'reasoning' in node_data:
                metadata['reasoning'] = node_data['reasoning']
            else:
                metadata['reasoning'] = 'DEFAULT'

            # Handle prompt reference
            if 'prompt' in node_data:
                prompt_ref = node_data['prompt']
                prompt_text = WorkflowConfig.get_prompt(prompt_ref=prompt_ref, custom_prompts=custom_prompts)
            else:
                prompt_text = WorkflowConfig.get_prompt(config_path=config_path,
                                                        prompt_name=node_id,
                                                        custom_prompts=custom_prompts)

            metadata['prompt'] = prompt_text
                
            # If no description, use the prompt text as the description
            if not description:
                # Get the prompt text from the config
                description = prompt_text

            node = ExecutionNode(
                node_id=node_id,
                node_type=node_type,
                description=description,
                metadata=metadata
            )
            workflow.add_node(node)
        
        # Add END node if it doesn't exist
        if not has_end:
            end_node = ExecutionNode(
                node_id="END",
                node_type=NodeType.END,
                description="End workflow"
            )
            workflow.add_node(end_node)
            node_ids.append("END")

        # Add edges
        cls._add_edges_to_workflow(workflow, data, node_ids)
        
        # Add role if specified
        if 'role' in data:
            workflow.add_role(role=data['role'])

        return workflow

    @classmethod
    def _add_edges_to_workflow(cls, workflow: Workflow, data: Dict, node_ids: List[str]) -> None:
        """Add edges to the workflow based on the data and node IDs."""
        edges_data = data.get('edges', [])
        
        # If no edges are specified, create sequential edges
        if not edges_data and len(node_ids) > 1:
            # Find START and END nodes if they exist
            start_node = next((node_id for node_id in node_ids if node_id == "START"), None)
            end_node = next((node_id for node_id in node_ids if node_id == "END"), None)
            
            # If no START/END nodes, use first and last nodes
            if not start_node:
                start_node = node_ids[0]
            if not end_node:
                end_node = node_ids[-1]
            
            # Create sequential edges
            for i in range(len(node_ids) - 1):
                if node_ids[i] != end_node and node_ids[i + 1] != start_node:
                    workflow.add_edge(Edge(
                        source=node_ids[i],
                        target=node_ids[i + 1]
                    ))
        else:
            # Add specified edges
            for edge_data in edges_data:
                edge = Edge(
                    source=edge_data['source'],
                    target=edge_data['target'],
                    metadata=edge_data.get('metadata', {})
                )
                workflow.add_edge(edge)

    @classmethod
    def create_workflow_from_config(cls, workflow_name: str, 
                                    objective: Union[str, Objective], 
                                    agent_role: Optional[str] = None,
                                    custom_prompts: Optional[Dict[str, str]] = None) -> Workflow:
        """Create a workflow from named configuration."""
        # Get the config path
        config_path = WorkflowConfig.get_config_path(workflow_name)
        
        if not config_path.exists():
            raise ValueError(f"No configuration found for workflow: {workflow_name}")
            
        # Convert objective to Objective object if needed
        obj = Objective(objective) if isinstance(objective, str) else objective
            
        # Load workflow from YAML with objective
        workflow = cls.from_yaml(config_path, obj, custom_prompts)
        
        # Set agent role if provided
        if agent_role:
            workflow.add_role(role=agent_role)
        
        return workflow

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
        return cls.create_workflow_from_config(workflow_name, objective, agent_role, custom_prompts)

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
        return cls.create_workflow_from_config("default", objective, agent_role, custom_prompts)
