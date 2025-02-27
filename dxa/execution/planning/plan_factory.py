"""Factory for creating planning patterns."""

from typing import Any, Dict, Optional, Union
from pathlib import Path

from ..execution_types import ExecutionNode, Objective, NodeType, Edge
from ..execution_graph import ExecutionGraph
from ..execution_factory import ExecutionFactory
from ..execution_config import ExecutionConfig
from .plan import Plan
from .plan_executor import PlanStrategy

class PlanConfig(ExecutionConfig):
    """Configuration for planning patterns."""
    
    @classmethod
    def get_base_path(cls) -> Path:
        """Get base path for configuration files."""
        return Path(__file__).parent

class PlanFactory(ExecutionFactory):
    """Creates planning pattern instances."""

    # Override class variables
    graph_class = Plan
    config_class = PlanConfig

    @classmethod
    def create_from_config(cls, name: str,
                           objective: Union[str, Objective],
                           role: Optional[str] = None,
                           custom_prompts: Optional[Dict[str, str]] = None) -> ExecutionGraph:
        """Create a planning instance by name."""
        plan = super().create_from_config(name, objective, role, custom_prompts)
        return plan
    
    @classmethod
    def create_planning_strategy(cls, node: ExecutionNode, context: Any = None) -> PlanStrategy:
        """Select appropriate planning strategy based on node metadata or context."""
        # Check if node has explicit planning strategy in metadata
        if node.metadata and "planning" in node.metadata:
            strategy_name = node.metadata["planning"]
            try:
                return PlanStrategy[strategy_name]
            except KeyError:
                # If strategy doesn't exist, fall back to default
                return PlanStrategy.DEFAULT
        
        # If no explicit strategy, use AUTO logic to select appropriate strategy
        return cls._select_auto_strategy(node, context)
    
    @classmethod
    def _select_auto_strategy(cls, node: ExecutionNode, context: Any = None) -> PlanStrategy:
        """Select appropriate planning strategy based on node content and context."""
        # Simple heuristics for strategy selection
        description = node.description.lower()
        
        # For sequential tasks, use SEQUENTIAL
        if any(keyword in description for keyword in ["step", "sequence", "order", "sequential"]):
            return PlanStrategy.SEQUENTIAL
        
        # Default to direct planning
        return PlanStrategy.DIRECT
    
    @classmethod
    def unused_from_yaml(cls, yaml_data, objective=None, custom_prompts=None):
        """Create planning from YAML data or file."""
        if isinstance(yaml_data, (str, Path)):
            config = PlanConfig.load_yaml(yaml_data)
        else:
            config = yaml_data
            
        # Create planning object
        plan = Plan(
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
                description = PlanConfig.format_node_description(
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
                
        plan.graph = graph
        return plan
    
    @classmethod
    def create_plan(cls, objective: Objective, strategy: PlanStrategy = PlanStrategy.DEFAULT) -> Plan:
        """Create a planning instance with the specified strategy."""
        plan = Plan(objective)
        plan.metadata["strategy"] = strategy.value
        return plan