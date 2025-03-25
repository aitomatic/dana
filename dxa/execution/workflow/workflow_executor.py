"""Workflow executor implementation."""

from typing import List, Optional, cast, Dict, Any

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import (
    ExecutionNode, ExecutionSignal, ExecutionNodeStatus,
    ExecutionSignalType
)
from ...common import DXA_LOGGER
from ...common.graph import Cursor, TopologicalTraversal, NodeType
from .workflow_strategy import WorkflowStrategy
from .workflow import Workflow
from ..planning import PlanExecutor, PlanStrategy
from ..reasoning import ReasoningExecutor, ReasoningStrategy

class WorkflowExecutor(Executor[WorkflowStrategy]):
    """Executes workflows by delegating to a plan executor.
    
    The WorkflowExecutor is responsible for executing workflow graphs,
    which represent high-level execution flows. It delegates the actual
    planning and reasoning tasks to a PlanExecutor.
    """
    
    @property
    def layer(self) -> str:
        """Get the execution layer name."""
        return "workflow"
    
    @property
    def strategy_class(self) -> type[WorkflowStrategy]:
        """Get the strategy class for this executor."""
        return WorkflowStrategy
    
    @property
    def default_strategy(self) -> WorkflowStrategy:
        """Get the default strategy for this executor."""
        return WorkflowStrategy.DEFAULT
    
    def __init__(
        self, 
        workflow_strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT,
        planning_strategy: PlanStrategy = PlanStrategy.DEFAULT,
        reasoning_strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT
    ):
        """Initialize workflow executor.
        
        Args:
            workflow_strategy: Workflow execution strategy
            planning_strategy: Plan execution strategy
            reasoning_strategy: Reasoning execution strategy
        """
        super().__init__(depth=0)
        self.strategy = workflow_strategy
        self.lower_executor = PlanExecutor(strategy=planning_strategy)
        self.lower_executor.lower_executor = ReasoningExecutor(strategy=reasoning_strategy)
        self.logger = DXA_LOGGER.getLogger(f"dxa.execution.{self.layer}")
    
    def _get_graph_class(self):
        """Get the appropriate graph class for this executor.
        
        Returns:
            Workflow graph class
        """
        return Workflow
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a workflow graph.
        
        This is the main entry point for executing a workflow. It sets up
        the execution context and delegates to the common graph execution
        logic.
        
        Args:
            workflow: Workflow graph to execute
            context: Execution context
            prev_signals: Signals from previous execution
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals
        """
        # Set the workflow graph
        self.graph = workflow
        
        # Set the workflow in context
        context.current_workflow = workflow
        
        # Execute the graph using common logic
        return await self.execute_graph(
            workflow,
            context,
            prev_signals,
            upper_signals,
            lower_signals
        )
    
    async def execute_graph(
        self,
        graph: ExecutionGraph,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a workflow graph.
        
        This method executes the workflow graph using the standard execution pattern.
        For optimized execution with planning ahead and node compression, use the
        OptimalWorkflowExecutor instead.
        
        Args:
            graph: Workflow graph to execute
            context: Execution context
            prev_signals: Signals from previous execution
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals
        """
        # Set current graph
        self.graph = graph
        
        # Set graph in context
        self._set_graph_in_context(graph, context)
        
        # Log execution start
        self._log_execution_start()
        
        # Get start node
        start_node = graph.get_start_node()
        if not start_node:
            self.logger.error("Workflow has no START node")
            return []
            
        # Create cursor for graph traversal
        cursor = Cursor(graph, start_node, TopologicalTraversal())
        
        # Execute nodes in sequence
        signals = []
        
        # Traverse graph using cursor
        for node in cursor:
            # Execute current node
            node_signals = await self.execute_node(
                cast(ExecutionNode, node),
                context,
                prev_signals=signals,
                upper_signals=upper_signals,
                lower_signals=lower_signals
            )
            signals.extend(node_signals)
        
        return signals
    
    def _build_layer_context(
        self,
        node: ExecutionNode,
        prev_signals: Optional[List[ExecutionSignal]] = None
    ) -> Dict[str, Any]:
        """Build the workflow context for a node.
        
        This method builds the context needed for workflow layer execution,
        including:
        1. Node information
        2. Previous execution results
        3. Workflow-specific metadata
        
        Args:
            node: Node to build context for
            prev_signals: Signals from previous execution
            
        Returns:
            Workflow context dictionary
        """
        # Create basic context with node info
        context = {
            "node_id": node.node_id,
            "node_type": node.node_type,
            "description": node.description,
            "metadata": node.metadata or {}
        }
        
        # Add workflow-specific information
        context.update({
            "dependencies": self._get_node_dependencies(node),
            "position": self._get_node_position(node),
            "progress": self._get_workflow_progress()
        })
        
        # Add previous outputs if available
        if prev_signals:
            context["previous_outputs"] = {
                signal.content.get("node"): signal.content.get("result")
                for signal in prev_signals
                if signal.type == ExecutionSignalType.DATA_RESULT
            }
        
        # Save the workflow context in node metadata
        node.metadata["workflow_context"] = context
        
        return context
        
    def _get_node_dependencies(self, node: ExecutionNode) -> List[str]:
        """Get dependencies for a node in the workflow.
        
        Args:
            node: Node to get dependencies for
            
        Returns:
            List of node IDs that this node depends on
        """
        dependencies = []
        if self.graph:
            for edge in self.graph.edges:
                if edge.target == node.node_id:
                    dependencies.append(edge.source)
        return dependencies
    
    def _get_node_position(self, node: ExecutionNode) -> Dict[str, Any]:
        """Get the position of a node in the workflow.
        
        Args:
            node: Node to get position for
            
        Returns:
            Dictionary with position information
        """
        # Default position info
        position = {
            "is_start": False,
            "is_end": False,
            "depth": 0,
            "parallel_index": 0
        }
        
        if not self.graph:
            return position
            
        # Check if start or end
        if node.node_type == NodeType.START:
            position["is_start"] = True
        elif node.node_type == NodeType.END:
            position["is_end"] = True
            
        # Calculate depth (distance from start)
        if self.graph:
            start_node = self.graph.get_start_node()
            if start_node:
                # Simple BFS to find depth
                visited = {start_node.node_id: 0}
                queue = [(start_node.node_id, 0)]
                
                while queue:
                    current_id, depth = queue.pop(0)
                    
                    for edge in self.graph.edges:
                        if edge.source == current_id and edge.target not in visited:
                            visited[edge.target] = depth + 1
                            queue.append((edge.target, depth + 1))
                
                position["depth"] = visited.get(node.node_id, 0)
        
        return position
    
    def _get_workflow_progress(self) -> Dict[str, Any]:
        """Get the current progress of the workflow.
        
        Returns:
            Dictionary with workflow progress information
        """
        progress = {
            "total_nodes": 0,
            "completed_nodes": 0,
            "in_progress_nodes": 0,
            "failed_nodes": 0,
            "percent_complete": 0.0
        }
        
        if not self.graph:
            return progress
            
        # Count nodes by status
        total = 0
        completed = 0
        in_progress = 0
        failed = 0
        
        for node in self.graph.nodes.values():
            if node.node_type not in [NodeType.START, NodeType.END]:
                total += 1
                if node.status == ExecutionNodeStatus.COMPLETED:
                    completed += 1
                elif node.status == ExecutionNodeStatus.IN_PROGRESS:
                    in_progress += 1
                elif node.status == ExecutionNodeStatus.FAILED:
                    failed += 1
        
        progress["total_nodes"] = total
        progress["completed_nodes"] = completed
        progress["in_progress_nodes"] = in_progress
        progress["failed_nodes"] = failed
        
        # Calculate percent complete
        if total > 0:
            progress["percent_complete"] = (completed / total) * 100.0
            
        return progress
    