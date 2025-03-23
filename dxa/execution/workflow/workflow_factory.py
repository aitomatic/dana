"""Workflow factory for creating common workflow patterns."""

from pathlib import Path
from typing import List, Optional, Union, Dict, cast, Any
import re
import yaml
from io import StringIO

from ...execution import ExecutionGraph
from ..execution_factory import ExecutionFactory
from .workflow import Workflow
from ...common.graph import NodeType, Edge
from ..execution_types import Objective, ExecutionNode
from .workflow_strategy import WorkflowStrategy
from ..execution_config import ExecutionConfig

class WorkflowFactory(ExecutionFactory):
    """Factory for creating workflow patterns."""
    
    # Override class variables
    graph_class = Workflow
    strategy_class = WorkflowStrategy

    @classmethod
    def from_yaml(cls, yaml_data: Union[str, Dict, Path], name: Optional[str] = None) -> Workflow:
        """Create workflow from YAML data or file.
        
        Args:
            yaml_data: YAML data as string, dictionary, or file path
            name: Optional workflow name
            
        Returns:
            Workflow: New workflow instance
        """
        # If yaml_data is already a Workflow object, return it
        if isinstance(yaml_data, Workflow):
            return yaml_data
            
        # Handle different input types
        if isinstance(yaml_data, (str, Path)):
            if isinstance(yaml_data, Path) or (isinstance(yaml_data, str) and yaml_data.endswith(('.yaml', '.yml'))):
                with open(yaml_data, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            else:
                data = yaml.safe_load(yaml_data)
        else:
            data = yaml_data

        # Create workflow
        workflow = Workflow(
            objective=Objective(data.get('objective', '')),
            name=data.get('name', 'unnamed_workflow')
        )

        # Store prompts in metadata
        if 'prompts' in data:
            workflow.metadata['prompts'] = data['prompts']

        # pylint: disable=protected-access
        ExecutionGraph._add_start_end_nodes(graph=workflow)

        # Remove the edge from START to END
        workflow.remove_edge_between("START", "END")

        # Add nodes
        prev_id = "START"
        for node_data in data.get('nodes', []):
            node_id = node_data['id']
            # Default to TASK type if not specified
            node_type = NodeType[node_data.get('type', 'TASK')]
            workflow.add_node(ExecutionNode(
                node_id=node_data['id'],
                node_type=node_type,
                description=node_data.get('description', ''),
                metadata=node_data.get('metadata', {})
            ))
            workflow.add_transition(prev_id, node_id)
            prev_id = node_id

        workflow.add_transition(prev_id, "END")

        return workflow
    
    @classmethod
    def _create_sequential_workflow_from_yaml_steps(cls, workflow_yaml: Union[str, Dict, Path]) -> Workflow:
        # Handle different input types
        if isinstance(workflow_yaml, (str, Path)):
            if not str(workflow_yaml).strip():
                raise ValueError("Empty workflow YAML")
            try:
                if isinstance(workflow_yaml, Path):
                    with open(workflow_yaml, 'r', encoding='utf-8') as f:
                        raw_data = yaml.safe_load(f)
                else:
                    # Use StringIO for string input
                    raw_data = yaml.safe_load(StringIO(workflow_yaml))
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML syntax: {str(e)}") from e
        else:
            raw_data = workflow_yaml

        if not raw_data or not isinstance(raw_data, dict):
            raise ValueError("Invalid workflow YAML structure - must be a non-empty dictionary")

        # Get the workflow name (first key in the YAML)
        try:
            workflow_name = next(iter(raw_data))
            processes = raw_data[workflow_name]
            if not isinstance(processes, dict):
                raise ValueError("Processes must be a dictionary")
        except (StopIteration, KeyError, AttributeError) as e:
            raise ValueError("Invalid workflow YAML structure - missing workflow name or processes") from e

        workflow = Workflow()

        # Add START node
        start_node = ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description="Start workflow"
        )
        workflow.add_node(start_node)

        # Add all task nodes sequentially
        step_counter = 1
        for process_name, steps in processes.items():
            if not isinstance(steps, list):
                continue
                
            for step in steps:
                if not step:  # Skip empty steps
                    continue
                
                task_node = ExecutionNode(
                    node_id=f"STEP_{step_counter}",
                    node_type=NodeType.TASK,
                    description=str(step),
                    metadata={
                        "process": str(process_name),
                        "step_number": step_counter,
                        "instruction": str(step)
                    }
                )
                workflow.add_node(task_node)
                step_counter += 1

        if len(workflow.nodes) == 1:  # Only START node exists
            raise ValueError("No valid steps found in workflow")

        # Add END node
        end_node = ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description="End workflow"
        )
        workflow.add_node(end_node)

        # Add edges
        node_ids = list(workflow.nodes.keys())
        for i in range(len(node_ids) - 1):
            workflow.add_edge_between(node_ids[i], node_ids[i + 1])

        return workflow
    
    # Add workflow-specific methods
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
        """Create a minimal workflow with START, PERFORM_TASK, and END nodes."""
        if isinstance(objective, str):
            objective = Objective(objective)
            
        workflow = Workflow(objective=objective)
        
        # Add START node
        start_node = ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description="Start workflow"
        )
        workflow.add_node(start_node)
        
        # Add task node
        task_node = ExecutionNode(
            node_id="PERFORM_TASK",
            node_type=NodeType.TASK,
            description="{objective}"
        )
        workflow.add_node(task_node)
        
        # Add END node
        end_node = ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description="End workflow"
        )
        workflow.add_node(end_node)
        
        # Add edges
        workflow.add_edge_between("START", "PERFORM_TASK")
        workflow.add_edge_between("PERFORM_TASK", "END")
        
        return workflow
    
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
        graph = cls.create_from_config(workflow_name, objective, agent_role, custom_prompts)
        return cast(Workflow, graph)

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
        graph = cls.create_from_config("default", objective, agent_role, custom_prompts)
        return cast(Workflow, graph)

    @classmethod
    def create_workflow_strategy(cls, node: ExecutionNode, context: Any = None) -> WorkflowStrategy:
        """Select appropriate workflow strategy based on node metadata or context."""
        # Check if node has explicit workflow strategy in metadata
        if "workflow" in node.metadata:
            strategy_name = node.metadata["workflow"].upper()
            try:
                return WorkflowStrategy[strategy_name]
            except KeyError:
                pass  # Invalid strategy name, fallback to auto-selection
        
        return cls._select_auto_strategy(node, context)
    
    @classmethod
    def _select_auto_strategy(cls, node: ExecutionNode, context: Any = None) -> WorkflowStrategy:
        """Select appropriate workflow strategy based on node content and context."""
        return cls.select_strategy_from_description(
            node.description, 
            WorkflowStrategy.DEFAULT
        )

    @classmethod
    async def nl_to_onl(cls, natural_language: str) -> str:
        """Convert natural language to organized natural language.
        
        Args:
            natural_language: Unstructured natural language text
            
        Returns:
            str: Organized natural language text
        """
        # Import LLMResource here to avoid circular import
        from ...agent import LLMResource
        
        # Get the path to the YAML file
        yaml_path = Path(__file__).parent / "yaml" / "admin" / "nl_to_onl.yaml"
        
        # Load prompt from configuration
        prompt_template = ExecutionConfig.get_prompt(
            for_class=cls,
            config_path=str(yaml_path),
            prompt_ref="ORGANIZE"
        )
        
        # Create LLM resource
        resource = LLMResource(name="NL to ONL Resource")
        try:
            # Format prompt and query LLM
            prompt = prompt_template.format(input=natural_language)
            result = await resource.query({"prompt": prompt})
            
            if 'content' not in result:
                raise ValueError("Invalid LLM response: missing 'content' field")
                
            return result['content']
        finally:
            # Ensure resource is cleaned up
            await resource.cleanup()

    @classmethod
    async def onl_to_yaml(cls, organized_natural_language: str) -> str:
        """Convert organized natural language to YAML workflow.
        
        Args:
            organized_natural_language: Organized natural language text
            
        Returns:
            str: YAML formatted workflow
        """
        # Import LLMResource here to avoid circular import
        from ...agent import LLMResource
        
        # Get the path to the YAML file
        yaml_path = Path(__file__).parent / "yaml" / "admin" / "onl_to_yaml.yaml"
        
        # Load prompt from configuration
        prompt_template = ExecutionConfig.get_prompt(
            for_class=cls,
            config_path=str(yaml_path),
            prompt_ref="CONVERT"
        )
        
        # Create LLM resource
        resource = LLMResource(name="ONL to YAML Resource")
        try:
            # Format prompt and query LLM
            prompt = prompt_template.format(input=organized_natural_language)
            result = await resource.query({"prompt": prompt})
            
            if 'content' not in result:
                raise ValueError("Invalid LLM response: missing 'content' field")
                
            # Clean up the response
            content = result['content']
            
            # Extract YAML content between triple backticks if present
            yaml_match = re.search(r'```(?:yaml)?\s*([\s\S]*?)```', content)
            if yaml_match:
                workflow_yaml = yaml_match.group(1).strip()
            else:
                # If no backticks, use the whole content but remove any explanatory text
                # that might appear after the YAML content
                lines = content.split('\n')
                yaml_lines = []
                for line in lines:
                    if line.strip() and not line.startswith('This YAML') and not line.startswith('The workflow'):
                        yaml_lines.append(line)
                workflow_yaml = '\n'.join(yaml_lines)
            
            # Validate YAML
            try:
                yaml.safe_load(workflow_yaml)
            except yaml.YAMLError as e:
                raise ValueError(f"Generated YAML is invalid: {str(e)}") from e
                
            return workflow_yaml
        finally:
            # Ensure resource is cleaned up
            await resource.cleanup()

    @classmethod
    async def nl_to_workflow(cls, natural_language: str) -> Workflow:
        """Convert natural language directly to a workflow.
        
        This is a convenience method that combines nl_to_onl and onl_to_yaml.
        
        Args:
            natural_language: Unstructured natural language text
            
        Returns:
            Workflow: A workflow instance
        """
        onl = await cls.nl_to_onl(natural_language)
        yaml_str = await cls.onl_to_yaml(onl)
        return cls.from_yaml(yaml_str)
