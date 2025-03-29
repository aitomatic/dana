"""Base factory for creating execution graphs."""

from typing import Dict, Optional, Union, Type, TypeVar, Generic, cast, List
from pathlib import Path
from ..common.graph import NodeType
from .execution_types import Objective, ExecutionNode
from .execution_graph import ExecutionGraph

# Generic type for graph class
GraphT = TypeVar('GraphT', bound=ExecutionGraph)

class ExecutionFactory(Generic[GraphT]):
    """Base factory for creating execution graphs.
    
    This is the foundational factory class that provides core functionality for creating
    execution graphs. It handles:
    1. Basic graph structure creation
    2. Configuration loading
    3. Generic type safety
    
    To create a new factory:
    1. Define your graph class (e.g., Workflow, Plan, Reasoning)
    2. Create a factory subclass:
       class MyFactory(ExecutionFactory[MyGraph]):
           graph_class = MyGraph
    3. Implement any specialized creation methods
    """
    
    # Required class variable - must be set by subclasses
    graph_class: Type[GraphT]
    
    def __init_subclass__(cls):
        """Validate that subclasses properly set graph_class."""
        if not hasattr(cls, 'graph_class'):
            raise TypeError(f"{cls.__name__} must set graph_class to its specific graph type")
        if cls.graph_class == ExecutionGraph:
            msg = f"{cls.__name__} must set graph_class to a specific graph type, "
            msg += "not the base ExecutionGraph"
            raise TypeError(msg)
    
    @classmethod
    def create_basic_graph(
        cls,
        objective: Optional[Union[str, Objective]] = None,
        name: Optional[str] = None
    ) -> GraphT:
        """Create a minimal graph with START -> task -> END nodes.
        
        Args:
            objective: Graph objective
            name: Optional name for the graph
            
        Returns:
            GraphT: A minimal graph with START -> task -> END nodes
        """
        # Create a single task node
        task_node = ExecutionNode(
            node_id="TASK",
            node_type=NodeType.TASK,
            description="Basic task"
        )
        
        # Use create_sequential_graph with the single task node
        return cls.create_sequential_graph(nodes=[task_node], objective=objective, name=name)

    @classmethod
    def create_sequential_graph(
        cls,
        nodes: List[ExecutionNode],
        objective: Optional[Union[str, Objective]] = None,
        name: Optional[str] = None
    ) -> GraphT:
        """Create a graph with nodes connected sequentially.
        
        Args:
            nodes: List of nodes to connect sequentially
            objective: Graph objective
            name: Optional name for the graph
            
        Returns:
            GraphT: A graph with nodes connected sequentially between START and END
        """
        if not isinstance(objective, Objective):
            objective = Objective(objective) if objective else None
            
        # Create graph
        graph = cls.graph_class(objective=objective, name=name)
        
        # Add START node
        start_node = ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description="Start node"
        )
        graph.add_node(start_node)
        
        # Add task nodes and connect them sequentially
        prev_node_id = "START"
        for node in nodes:
            graph.add_node(node)
            graph.add_edge_between(prev_node_id, node.node_id)
            prev_node_id = node.node_id
            
        # Add END node and connect last task to it
        end_node = ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description="End node"
        )
        graph.add_node(end_node)
        graph.add_edge_between(prev_node_id, "END")
        
        return cast(GraphT, graph)

    @classmethod
    def create_from_config(
        cls,
        config_name: str,
        objective: Union[str, Objective],
        role: Optional[str] = None,
        custom_prompts: Optional[Dict[str, str]] = None,
        config_dir: Optional[Union[str, Path]] = None
    ) -> GraphT:
        """Create an execution graph from named configuration.
        
        This is a generic method for loading graph configurations. It supports:
        1. Direct file paths
        2. Named configurations
        3. Custom prompts and roles
        
        Args:
            config_name: Name of the configuration or path to config file
            objective: The objective for the graph
            role: Optional role for the graph
            custom_prompts: Optional custom prompts to override defaults
            config_dir: Optional directory containing configuration files
            
        Returns:
            An execution graph created from the configuration
            
        Raises:
            TypeError: If graph_class is not properly set
            ValueError: If objective is invalid or configuration is not found
        """
        if not isinstance(objective, Objective):
            try:
                objective = Objective(objective)
            except (TypeError, ValueError) as e:
                raise ValueError("Invalid objective") from e

        # If config_dir is provided, use it to find the configuration
        if config_dir:
            # Construct path to the config file
            config_dir = Path(config_dir)
            
            # Handle both direct file references and directory/name combinations
            if config_name.endswith(('.yaml', '.yml')):
                config_path = config_dir / config_name
            else:
                config_path = config_dir / f"{config_name}.yaml"
                if not config_path.exists():
                    config_path = config_dir / f"{config_name}.yml"
                    
            if not config_path.exists():
                raise ValueError(f"Configuration file not found: {config_path}")
            
            try:
                graph = cls.graph_class.from_execution_yaml(
                    config_path=config_path,
                    objective=objective,
                    custom_prompts=custom_prompts
                )
            except TypeError as e:
                raise TypeError(f"Failed to create graph: {str(e)}. Ensure graph_class is properly set.") from e
        else:
            # Use the standard path resolution
            try:
                graph = cls.graph_class.from_execution_yaml(
                    config_name=config_name,
                    objective=objective,
                    custom_prompts=custom_prompts
                )
            except TypeError as e:
                raise TypeError(f"Failed to create graph: {str(e)}. Ensure graph_class is properly set.") from e
        
        # Set role if provided
        if role:
            graph.metadata["role"] = role
        
        return cast(GraphT, graph)