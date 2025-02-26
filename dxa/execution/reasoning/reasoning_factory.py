"""Factory for creating reasoning patterns."""

from typing import Dict, Optional, Union, Any
from pathlib import Path

from ..execution_types import ExecutionNode, Objective, NodeType, Edge
from ..execution_graph import ExecutionGraph
from .reasoning import Reasoning
from .reasoning_executor import ReasoningStrategy
from .reasoning_config import ReasoningConfig

class ReasoningFactory:
    """Creates reasoning pattern instances."""
    
    @classmethod
    def create_reasoning_strategy(cls, node: ExecutionNode, context: Any = None) -> ReasoningStrategy:
        """Select appropriate reasoning strategy based on node metadata or context."""
        # Check if node has explicit reasoning strategy in metadata
        if node.metadata and "reasoning" in node.metadata:
            strategy_name = node.metadata["reasoning"]
            try:
                return ReasoningStrategy[strategy_name]
            except KeyError:
                # If strategy doesn't exist, fall back to default
                return ReasoningStrategy.DEFAULT
        
        # If no explicit strategy, use AUTO logic to select appropriate strategy
        return cls._select_auto_strategy(node, context)
    
    @classmethod
    def _select_auto_strategy(cls, node: ExecutionNode, context: Any = None) -> ReasoningStrategy:
        """Select appropriate reasoning strategy based on node content and context."""
        # Simple heuristics for strategy selection
        description = node.description.lower()
        
        # For mathematical or logical problems, use chain of thought
        if any(keyword in description for keyword in ["calculate", "solve", "equation", "math", "logic", "proof"]):
            return ReasoningStrategy.CHAIN_OF_THOUGHT
        
        # For decision-making or situational analysis, use OODA
        if any(keyword in description for keyword in ["decide", "situation", "analyze", "assess", "evaluate"]):
            return ReasoningStrategy.OODA
        
        # For complex reasoning with multiple steps, use DANA
        if any(keyword in description for keyword in ["complex", "multi-step", "detailed", "comprehensive"]):
            return ReasoningStrategy.DANA
        
        # For PROSEA specific nodes, use PROSEA
        if node.node_id in ["ANALYZE", "PLAN", "FINALIZE"]:
            return ReasoningStrategy.PROSEA
            
        # Default to simple direct reasoning
        return ReasoningStrategy.DEFAULT
    
    @classmethod
    def from_yaml(cls, yaml_data, objective=None, custom_prompts=None):
        """Create reasoning from YAML data or file."""
        if isinstance(yaml_data, (str, Path)):
            config = ReasoningConfig.load_yaml(str(yaml_data))
        else:
            config = yaml_data
            
        # Create reasoning object
        reasoning = Reasoning(
            objective=objective or Objective(config.get("description", ""))
        )
        
        # Process nodes
        nodes = []
        for node_config in config.get("nodes", []):
            node_id = node_config.get("id", f"NODE_{len(nodes)}")
            node_type = NodeType.TASK  # Default to TASK
            
            # Get node description
            description = node_config.get("description", "")
            
            # Handle prompt if specified
            prompt_ref = node_config.get("prompt")
            if prompt_ref:
                # Format description with prompt
                description = ReasoningConfig.format_node_description(
                    description, 
                    prompt_ref, 
                    objective.original if objective else None,
                    custom_prompts
                )
            
            # Create node
            node = ExecutionNode(
                node_id=node_id,
                node_type=node_type,
                description=description,
                metadata=node_config
            )
            nodes.append(node)
            
        # Create graph
        graph = ExecutionGraph()
        for node in nodes:
            graph.add_node(node)
            
        # Add edges if specified
        for edge_config in config.get("edges", []):
            source = edge_config.get("source")
            target = edge_config.get("target")
            if source and target:
                metadata = edge_config.get("metadata", {})
                edge = Edge(source=source, target=target)
                graph.add_edge(edge, metadata)
                
        reasoning.graph = graph
        
        # Process strategies
        strategies = {}
        for node_id, strategy_name in config.get('strategies', {}).items():
            try:
                strategies[node_id] = ReasoningStrategy[strategy_name]
            except KeyError:
                strategies[node_id] = ReasoningStrategy.DEFAULT
                
        reasoning.metadata["strategies"] = strategies
        return reasoning
    
    @classmethod
    def create_reasoning(cls, objective: Objective, strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT) -> Reasoning:
        """Create a reasoning instance with the specified strategy."""
        reasoning = Reasoning(objective)
        reasoning.metadata["strategy"] = strategy.value
        return reasoning