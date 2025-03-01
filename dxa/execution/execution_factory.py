"""Base factory for creating execution graphs."""

from typing import Dict, Any, Optional, Union, List, Type
from pathlib import Path
from ..common.graph import Edge
from .execution_types import Objective
from .execution_graph import ExecutionGraph

class ExecutionFactory:
    """Base factory for creating execution graphs."""
    
    # To keep track of which of the various graph classes we're operating on
    graph_class: Type[ExecutionGraph] = ExecutionGraph
    
    @classmethod
    def _add_edges_to_graph(cls, graph: ExecutionGraph, data: Dict[str, Any], node_ids: List[str]) -> None:
        """Add edges to the graph from YAML data."""
        # If edges are explicitly defined, use them
        if 'edges' in data:
            for edge_data in data['edges']:
                source = edge_data.get('source') or edge_data.get('from')
                target = edge_data.get('target') or edge_data.get('to')
                condition = edge_data.get('condition')
                
                if not source or not target:
                    continue
                    
                edge = Edge(source=source, target=target)
                if condition:
                    edge.metadata = {"condition": condition}
                    
                graph.add_edge(edge)
        else:
            # Otherwise, create a linear sequence
            for i in range(len(node_ids) - 1):
                graph.add_edge(Edge(source=node_ids[i], target=node_ids[i + 1]))

    @classmethod
    def create_from_config(cls,
                           config_name: str,
                           objective: Union[str, Objective],
                           role: Optional[str] = None,
                           custom_prompts: Optional[Dict[str, str]] = None,
                           config_dir: Optional[Union[str, Path]] = None) -> ExecutionGraph:
        """Create an execution graph from named configuration."""
        if not isinstance(objective, Objective):
            objective = Objective(objective)

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
            
            graph = cls.graph_class.from_execution_yaml(config_path=config_path,
                                                        objective=objective,
                                                        custom_prompts=custom_prompts)
        else:
            # Use the standard path resolution
            graph = cls.graph_class.from_execution_yaml(config_name=config_name,
                                                        objective=objective,
                                                        custom_prompts=custom_prompts)
        
        # Set role if provided
        if role:
            graph.metadata["role"] = role
        
        return graph