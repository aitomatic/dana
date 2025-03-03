"""Base factory for creating execution graphs."""

from typing import Dict, Any, Optional, Union, List, Type, TypeVar
from pathlib import Path
from ..common.graph import Edge
from .execution_types import Objective, ExecutionNode
from .execution_graph import ExecutionGraph
import json
import os

# Generic type for strategy enums
StrategyT = TypeVar('StrategyT')

class ExecutionFactory:
    """Base factory for creating execution graphs."""
    
    # To keep track of which of the various graph classes we're operating on
    graph_class: Type[ExecutionGraph] = ExecutionGraph
    
    # Strategy enum class - to be overridden by subclasses
    strategy_class = None
    
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

    @classmethod
    def create_minimal_graph(cls, objective: Optional[Objective] = None, name: Optional[str] = None) -> ExecutionGraph:
        """Create a minimal graph with just START and END nodes.
        
        This is a common pattern used across different factory classes.
        
        Args:
            objective: The objective for the graph
            name: Optional name for the graph
            
        Returns:
            A minimal execution graph
        """
        graph = cls.graph_class(objective, name)
        
        # Create START and END nodes
        start_node = ExecutionNode(
            node_id="start",
            node_type="START",
            description="Start node"
        )
        
        end_node = ExecutionNode(
            node_id="end",
            node_type="END",
            description="End node"
        )
        
        # Add nodes to graph
        graph.add_node(start_node)
        graph.add_node(end_node)
        
        # Connect START to END
        graph.add_edge_between(start_node.node_id, end_node.node_id)
        
        return graph
        
    @classmethod
    def select_strategy_from_description(cls, description: str, default_strategy: StrategyT) -> StrategyT:
        """Select appropriate strategy based on task description.
        
        This provides a common heuristic for strategy selection that can be used
        across different factory classes.
        
        Args:
            description: Task description text
            default_strategy: Default strategy to use if no match is found
            
        Returns:
            Selected strategy
        """
        if cls.strategy_class is None:
            return default_strategy
            
        description = description.lower()
        
        # Common patterns for strategy selection
        # These can be overridden or extended by subclasses
        strategy_keywords = {
            "sequential": ["step", "sequence", "order", "sequential"],
            "parallel": ["parallel", "concurrent", "simultaneous"],
            "conditional": ["condition", "if", "when", "unless", "choose"],
            "chain_of_thought": ["think", "step by step", "reasoning", "thought"],
            "ooda": ["observe", "orient", "decide", "act", "ooda"],
            "dana": ["define", "analyze", "navigate", "advance", "dana"],
            "prosea": ["problem", "research", "options", "selection", "execution", "assessment", "prosea"]
        }
        
        # Check for keyword matches
        for strategy_name, keywords in strategy_keywords.items():
            if any(keyword in description for keyword in keywords):
                # Try to find the strategy in the strategy class
                try:
                    return cls.strategy_class[strategy_name.upper()]
                except (KeyError, AttributeError):
                    pass  # Strategy not available in this class
        
        return default_strategy