"""Base factory for creating execution graphs."""

from typing import Dict, Any, Optional, Union, List, Type
from pathlib import Path

from ..common.utils.config import load_yaml_config
from ..common.graph import NodeType, Edge
from .execution_types import Objective, ExecutionNode
from .execution_graph import ExecutionGraph
from .execution_config import ExecutionConfig

class ExecutionFactory:
    """Base factory for creating execution graphs."""
    
    # Class variables to be overridden by subclasses
    graph_class: Type[ExecutionGraph] = ExecutionGraph
    config_class: Type[ExecutionConfig] = ExecutionConfig
    
    @classmethod
    def from_yaml(cls, yaml_data: Union[str, Dict, Path], 
                  objective: Optional[Objective] = None,
                  custom_prompts: Optional[Dict[str, str]] = None) -> ExecutionGraph:
        """Create execution graph from YAML data or file."""
        # Handle different input types
        config_path = None
        if isinstance(yaml_data, (str, Path)):
            if isinstance(yaml_data, str) and not Path(yaml_data).exists():
                # Assume it's a config name
                config_path = cls.config_class.get_config_path(yaml_data)
            else:
                config_path = str(yaml_data)

            data = load_yaml_config(config_path)
        else:
            data = yaml_data

        # Create graph
        graph = cls.graph_class(
            objective=objective or Objective(data.get('description', '')),
            name=data.get('name', f'unnamed_{cls.graph_class.__name__.lower()}')
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
                description="Begin execution"
            )
            graph.add_node(start_node)
            node_ids.append("START")
        
        # Process nodes from YAML
        for node_data in nodes_data:
            description = node_data.get('description', '')
            if 'id' not in node_data:
                continue
            node_id = node_data['id']
            node_ids.append(node_id)
            
            # Determine node type
            if 'type' not in node_data:
                node_type = NodeType.TASK
            else:
                node_type = NodeType[node_data['type']]

            # Prepare metadata
            metadata = node_data.get('metadata', {})

            # Ensure planning and reasoning strategies are included in metadata
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
                prompt_text = cls.config_class.get_prompt(prompt_ref=prompt_ref, custom_prompts=custom_prompts)
            else:
                prompt_text = cls.config_class.get_prompt(config_path=config_path,
                                                          prompt_name=node_id,
                                                          custom_prompts=custom_prompts)

            metadata['prompt'] = prompt_text
                
            # If no description, use the prompt text as the description
            if not description:
                description = prompt_text

            node = ExecutionNode(
                node_id=node_id,
                node_type=node_type,
                description=description,
                metadata=metadata
            )
            graph.add_node(node)
        
        # Add END node if it doesn't exist
        if not has_end:
            end_node = ExecutionNode(
                node_id="END",
                node_type=NodeType.END,
                description="End execution"
            )
            graph.add_node(end_node)
            node_ids.append("END")

        # Add edges
        cls._add_edges_to_graph(graph, data, node_ids)
        
        # Add metadata if specified
        if 'metadata' in data:
            for key, value in data['metadata'].items():
                graph.metadata[key] = value
        
        return graph
    
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
    def create_from_config(cls, name: str,
                           objective: Union[str, Objective],
                           role: Optional[str] = None,
                           custom_prompts: Optional[Dict[str, str]] = None) -> ExecutionGraph:
        """Create an execution graph from named configuration.
        
        Args:
            name: Name of the configuration to load
            objective: The objective to accomplish
            role: Optional role for the agent
            custom_prompts: Optional custom prompts to override defaults
            
        Returns:
            A configured execution graph
        """
        if not isinstance(objective, Objective):
            objective = Objective(objective)

        graph = cls.from_yaml(name, objective, custom_prompts)
        
        # Set role if provided
        if role:
            graph.metadata["role"] = role
        
        return graph