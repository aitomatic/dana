"""Factory for creating planning patterns."""

from typing import Optional, Any, cast

from ..execution_types import ExecutionNode, Objective
from ..execution_factory import ExecutionFactory
from .plan import Plan
from .plan_strategy import PlanStrategy


class PlanFactory(ExecutionFactory):
    """Creates planning pattern instances."""

    # Override class variables
    graph_class = Plan
    strategy_class = PlanStrategy
    
    @classmethod
    def create_planning_strategy(cls, node: ExecutionNode, context: Any = None) -> PlanStrategy:
        """Select appropriate planning strategy based on node metadata or context."""
        # Check if node has explicit planning strategy in metadata
        if "planning" in node.metadata:
            strategy_name = node.metadata["planning"].upper()
            try:
                return PlanStrategy[strategy_name]
            except KeyError:
                pass  # Invalid strategy name, fallback to auto-selection
        
        return cls._select_auto_strategy(node, context)
    
    @classmethod
    def _select_auto_strategy(cls, node: ExecutionNode, context: Any = None) -> PlanStrategy:
        """Select appropriate planning strategy based on node content and context."""
        return cls.select_strategy_from_description(
            node.description, 
            PlanStrategy.DEFAULT
        )
    
    @classmethod
    def create_plan(cls, objective: Objective, strategy: PlanStrategy = PlanStrategy.DEFAULT) -> Plan:
        """Create a planning instance with the specified strategy."""
        plan = Plan(objective)
        
        # Add strategy to plan metadata
        plan.metadata["strategy"] = strategy.value
        
        return plan
    
    @classmethod
    def create_minimal_plan(cls, objective: Optional[Objective] = None) -> Plan:
        """Create a minimal plan with just START and END nodes."""
        return cast(Plan, cls.create_minimal_graph(objective))