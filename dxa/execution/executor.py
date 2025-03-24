"""Base class for all executors in the execution system."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Generic, List, Optional, Type, TypeVar, Any, cast, Dict, TYPE_CHECKING, Union

import logging

from .execution_context import ExecutionContext
from .execution_graph import ExecutionGraph
from .execution_types import (
    ExecutionNode, ExecutionSignal, Objective, 
    ExecutionNodeStatus, ExecutionSignalType
)
from ..common.graph import NodeType

# Type variable for strategy enums
StrategyT = TypeVar('StrategyT', bound=Enum)

if TYPE_CHECKING:
    from .workflow.workflow_executor import WorkflowExecutor
    from .planning.plan_executor import PlanExecutor
    from .reasoning.reasoning_executor import ReasoningExecutor

class ExecutionError(Exception):
    """Exception raised for errors during execution."""
    pass


class Executor(ABC, Generic[StrategyT]):
    """Base class for all executors in the execution system.
    
    The Executor class provides common execution logic for all layers
    in the execution system. Each layer (workflow, plan, reasoning)
    implements its own specific behavior while inheriting common
    functionality from this base class.
    """
    
    def __init__(self, depth: int = 0):
        """Initialize executor.
        
        Args:
            depth: Execution depth (0 for workflow, 1 for plan, 2 for reasoning)
        """
        self.depth = depth
        self._graph: Optional[ExecutionGraph] = None
        self.lower_executor: Optional[Union['WorkflowExecutor', 'PlanExecutor', 'ReasoningExecutor']] = None
        self.logger = logging.getLogger(f"dxa.execution.{self.layer}")
        self._strategy = self.default_strategy
        self._configure_logger()
    
    @property
    @abstractmethod
    def layer(self) -> str:
        """Get the execution layer name."""
        pass
    
    @property
    @abstractmethod
    def strategy_class(self) -> Type[StrategyT]:
        """Get the strategy class for this executor."""
        pass
    
    @property
    @abstractmethod
    def default_strategy(self) -> StrategyT:
        """Get the default strategy for this executor."""
        pass
    
    @property
    def graph(self) -> Optional[ExecutionGraph]:
        """Get current execution graph."""
        return self._graph
    
    @graph.setter
    def graph(self, graph: ExecutionGraph) -> None:
        """Set current execution graph."""
        self._graph = graph
    
    async def execute_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a node using common execution logic.
        
        Args:
            node: Node to execute
            context: Execution context
            prev_signals: Signals from previous node execution
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals
        """
        try:
            # Update node status
            assert self.graph is not None, "Graph is not set"
            self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
            
            # Skip START and END nodes
            if node.node_type in [NodeType.START, NodeType.END]:
                return []
            
            # Ensure node has metadata
            if node.metadata is None:
                node.metadata = {}
            
            # Build layer-specific context and update node metadata
            layer_context = self._build_layer_context(node, prev_signals)
            node.metadata[f"{self.layer}_context"] = layer_context
            
            # Execute next layer
            assert self.lower_executor is not None, "Lower executor is not set"
            lower_graph = self.lower_executor.create_graph_from_node(
                upper_node=node,
                upper_graph=self.graph,
                objective=self.graph.objective if self.graph else None,
                context=context
            )
            signals = await self.lower_executor.execute_graph(lower_graph, context) 
            
            # Update node status to completed
            self.graph.update_node_status(node.node_id, ExecutionNodeStatus.COMPLETED)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error executing node {node.node_id}: {str(e)}")
            
            # Update node status to error
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.FAILED)
            
            # Create error signal
            return [self._create_error_signal(node.node_id, str(e))]
    
    @abstractmethod
    def _build_layer_context(
        self,
        node: ExecutionNode,
        prev_signals: Optional[List[ExecutionSignal]] = None
    ) -> Dict[str, Any]:
        """Build layer-specific context for node execution.
        
        Args:
            node: Node to execute
            prev_signals: Signals from previous node execution
            
        Returns:
            Layer-specific context dictionary
        """
        pass
    
    def _create_error_signal(self, node_id: str, error: str) -> ExecutionSignal:
        """Create an error signal.
        
        Args:
            node_id: ID of the node that failed
            error: Error message
            
        Returns:
            Error signal
        """
        return ExecutionSignal(
            type=ExecutionSignalType.CONTROL_ERROR,
            content={
                "node": node_id,
                "error": error
            }
        )
    
    def _configure_logger(self):
        """Configure logger with appropriate handlers and formatters."""
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    @property
    def strategy(self) -> StrategyT:
        """Get current execution strategy."""
        return cast(StrategyT, self._strategy)
    
    @strategy.setter
    def strategy(self, strategy) -> None:
        """Set execution strategy.
        
        Can accept either string representation or enum value.
        
        Args:
            strategy: Strategy value or string representation
        """
        if isinstance(strategy, str) and self.strategy_class is not None:
            try:
                self._strategy = self.strategy_class[strategy]
            except KeyError:
                try:
                    self._strategy = next(
                        s for s in self.strategy_class 
                        if s.value == strategy
                    )
                except StopIteration:
                    raise ValueError(f"Invalid strategy: {strategy}")
        else:
            self._strategy = strategy
    
    async def execute_graph(
        self,
        graph: ExecutionGraph,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a graph using common execution logic.
        
        Args:
            graph: Graph to execute
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
            self.logger.error(f"{self.layer} has no START node")
            return []
            
        # Execute nodes in sequence
        signals = []
        current_node = start_node
        
        while current_node and current_node.node_type != NodeType.END:
            # Execute current node
            node_signals = await self.execute_node(
                current_node,
                context,
                prev_signals=signals,
                upper_signals=upper_signals,
                lower_signals=lower_signals
            )
            signals.extend(node_signals)
            
            # Get next node
            next_node = self._get_next_node(current_node)
            if not next_node:
                break
            current_node = next_node
        
        return signals
    
    def _get_next_node(self, current_node: ExecutionNode) -> Optional[ExecutionNode]:
        """Get the next node in the execution sequence.
        
        Args:
            current_node: Current node
            
        Returns:
            Next node, or None if no next node
        """
        if not self.graph:
            return None
            
        # Get outgoing edges
        outgoing_edges = [e for e in self.graph.edges if e.source == current_node.node_id]
        if not outgoing_edges:
            return None
            
        # Get next node
        next_node_id = outgoing_edges[0].target
        return self.graph.nodes.get(next_node_id)
    
    def _set_graph_in_context(
        self, 
        graph: ExecutionGraph, 
        context: ExecutionContext
    ) -> None:
        """Set the current graph in the execution context.
        
        Args:
            graph: Execution graph
            context: Execution context
        """
        if context is None:
            return
            
        # Set graph in context based on layer
        if self.layer == "workflow":
            from ..execution.workflow import Workflow
            context.current_workflow = cast(Workflow, graph)
        elif self.layer == "plan":
            from ..execution.planning import Plan
            context.current_plan = cast(Plan, graph)
        elif self.layer == "reasoning":
            from ..execution.reasoning import Reasoning
            context.current_reasoning = cast(Reasoning, graph)
    
    def _should_propagate_down(self, signal: ExecutionSignal) -> bool:
        """Determine if signal should propagate down the execution hierarchy.
        
        Args:
            signal: Execution signal to check
            
        Returns:
            True if signal should propagate down, False otherwise
        """
        # Default implementation: propagate control signals down
        return signal.type.name.startswith("CONTROL_")
    
    def _should_propagate_up(self, signal: ExecutionSignal) -> bool:
        """Determine if signal should propagate up the execution hierarchy.
        
        Args:
            signal: Execution signal to check
            
        Returns:
            True if signal should propagate up, False otherwise
        """
        # Default implementation: propagate result signals up
        return signal.type.name.startswith("RESULT_")
    
    def _should_propagate_horizontal(self, signal: ExecutionSignal) -> bool:
        """Determine if signal should propagate to sibling nodes.
        
        Args:
            signal: Execution signal to check
            
        Returns:
            True if signal should propagate horizontally, False otherwise
        """
        # Default implementation: don't propagate horizontally
        return False
    
    def _process_node_signals(
        self, 
        node_id: str, 
        signals: List[ExecutionSignal]
    ) -> None:
        """Process signals generated by a node execution.
        
        Args:
            node_id: ID of the node that generated the signals
            signals: Signals to process
        """
        if not signals:
            return
            
        # Process each signal
        for signal in signals:
            # Check for error signals
            if signal.type.name == "ERROR":
                error_msg = signal.content.get("message", "Unknown error")
                self._handle_node_error(node_id, error_msg)
    
    def _handle_node_error(self, node_id: str, error: str) -> None:
        """Handle node execution error.
        
        Args:
            node_id: ID of the node that failed
            error: Error message
        """
        # Log error
        self.logger.error("Error executing node %s: %s", node_id, error)
        
        # Update node status in graph
        if self.graph and node_id in self.graph.nodes:
            self.graph.update_node_status(node_id, ExecutionNodeStatus.FAILED)
    
    def _get_graph_class(self):
        """Get the appropriate graph class for this executor.
        
        Returns:
            Graph class for this layer, or None to use ExecutionGraph
        """
        # Subclasses should override this if they use a specific graph class
        return None
    
    @abstractmethod
    def create_graph_from_node(
        self,
        upper_node: ExecutionNode,
        upper_graph: ExecutionGraph,
        objective: Optional[Objective] = None,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create an execution graph from a node in an upper layer.
        
        Args:
            upper_node: Node from upper layer
            upper_graph: Graph from upper layer
            objective: Execution objective
            context: Execution context
            
        Returns:
            Execution graph
        """
        pass
    
    def _create_sequence_graph(self, nodes: List[ExecutionNode]) -> ExecutionGraph:
        """Create a sequential execution graph from a list of nodes.
        
        Args:
            nodes: List of nodes to include in the graph
            
        Returns:
            Sequential execution graph
        """
        # Create graph
        # Use ExecutionGraph directly instead of trying to use graph_class
        graph = ExecutionGraph(layer=self.layer)
        
        # Add START node
        start_node = ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description=f"Start {self.layer} execution"
        )
        graph.add_node(start_node)
        
        # Add task nodes
        for node in nodes:
            graph.add_node(node)
        
        # Add END node
        end_node = ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description=f"End {self.layer} execution"
        )
        graph.add_node(end_node)
        
        # Connect nodes in sequence
        prev_id = start_node.node_id
        for node in nodes:
            graph.add_edge_between(prev_id, node.node_id)
            prev_id = node.node_id
        
        # Connect last node to END
        graph.add_edge_between(prev_id, end_node.node_id)
        
        return graph
    
    def _create_execution_graph(
        self, 
        nodes: List[ExecutionNode]
    ) -> ExecutionGraph:
        """Create an execution graph with the given nodes.
        
        This is a simple wrapper around _create_sequence_graph for now.
        Subclasses can override to create more complex graphs.
        
        Args:
            nodes: List of nodes to include in the graph
            
        Returns:
            Execution graph
        """
        return self._create_sequence_graph(nodes)
    
    def create_result_signal(
        self, 
        node_id: str, 
        result: Any
    ) -> ExecutionSignal:
        """Create a result signal for a node.
        
        Args:
            node_id: ID of the node that produced the result
            result: Result data
            
        Returns:
            Result signal
        """
        return ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "node": node_id,
                "result": result
            }
        )
    
    def _log_execution_start(self):
        """Log the start of execution."""
        graph_name = self.graph.name if self.graph else "unnamed"
        self.logger.info(
            f"Starting {self.layer} execution: {graph_name} "
            f"with strategy {self.strategy.name if self.strategy else 'DEFAULT'}"
        ) 