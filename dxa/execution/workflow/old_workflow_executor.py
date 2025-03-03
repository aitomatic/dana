"""Workflow executor implementation."""

from enum import Enum
from typing import List, cast, Optional, TYPE_CHECKING
import logging

from ..execution_context import ExecutionContext
from ..execution_types import ExecutionNode, ExecutionSignal, Objective, ExecutionNodeStatus, ExecutionSignalType
from ..execution_graph import ExecutionGraph
from ..old_executor import Executor
from .workflow import Workflow
from ...common.graph import NodeType
from ...common.utils.text_processor import TextProcessor

if TYPE_CHECKING:
    from ..planning.old_plan_executor import PlanExecutor

class WorkflowStrategy(Enum):
    """Workflow execution strategies."""
    DEFAULT = "DEFAULT"      # same as WORKFLOW_IS_PLAN
    WORKFLOW_IS_PLAN = "WORKFLOW_IS_PLAN"
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    CONDITIONAL = "CONDITIONAL"

class WorkflowExecutor(Executor[WorkflowStrategy]):
    """Executes workflows by delegating to a plan executor."""
    
    strategy_class = WorkflowStrategy
    default_strategy = WorkflowStrategy.DEFAULT
    
    def __init__(self, plan_executor: 'PlanExecutor', strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT):
        """Initialize workflow executor.
        
        Args:
            plan_executor: Plan executor to use for executing plans
            strategy: Workflow execution strategy
        """
        super().__init__(depth=0)
        self.plan_executor = plan_executor
        self.strategy = strategy
        self.layer = "workflow"
        self.logger = logging.getLogger(f"dxa.execution.{self.layer}")
        self.parse_by_key = TextProcessor().parse_by_key

    async def _execute_task(
            self,
            node: ExecutionNode,
            context: ExecutionContext,
            prev_signals: Optional[List[ExecutionSignal]] = None,
            upper_signals: Optional[List[ExecutionSignal]] = None,
            lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a workflow task with custom logic."""
        # Any custom logic that was in execute_graph can be moved here
        # ...
        
        # Then delegate to plan executor
        signals = await self.plan_executor.execute_graph(
            upper_graph=self.graph,
            context=context,
            upper_signals=prev_signals
        )
        
        # Any post-processing that was in execute_graph
        # ...
        
        return signals

    def _create_graph(
            self,
            upper_graph: ExecutionGraph,
            objective: Optional[Objective] = None,
            context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create a workflow graph."""
        from .workflow_factory import WorkflowFactory
        
        # Create a minimal workflow if no objective is provided
        return WorkflowFactory.create_minimal_workflow(objective or upper_graph.objective)

    async def _custom_graph_traversal(self,
                                    graph: ExecutionGraph,
                                    context: ExecutionContext,
                                    upper_signals: Optional[List[ExecutionSignal]] = None) -> Optional[List[ExecutionSignal]]:
        """Implement custom traversal strategies for workflows."""
        # If using a special workflow strategy that requires custom traversal, handle it here
        if self.strategy == WorkflowStrategy.PARALLEL:
            # Implement parallel execution strategy
            self.logger.info("Using parallel execution strategy")
            # Custom parallel traversal logic would go here
            # For now, return None to use default traversal
            return None
            
        elif self.strategy == WorkflowStrategy.CONDITIONAL:
            # Implement conditional execution strategy
            self.logger.info("Using conditional execution strategy")
            # Custom conditional traversal logic would go here
            # For now, return None to use default traversal
            return None
            
        # For DEFAULT/WORKFLOW_IS_PLAN and SEQUENTIAL, use default traversal
        return None
