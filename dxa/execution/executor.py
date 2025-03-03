"""Base class for all executors in the execution system."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Generic, List, Optional, Type, TypeVar, Any, cast

import logging

from .execution_context import ExecutionContext
from .execution_graph import ExecutionGraph
from .execution_types import (
    ExecutionNode, ExecutionSignal, Objective, 
    ExecutionNodeStatus, ExecutionSignalType
)
from ..common.graph import NodeType, Edge

# Type variable for strategy enums
StrategyT = TypeVar('StrategyT', bound=Enum)


class ExecutionError(Exception):
    """Exception raised for errors during execution."""
    pass


class Executor(ABC, Generic[StrategyT]):
    """Base class for all executors in the execution system.
    
    This abstract class defines the interface and common functionality
    for all executors. Subclasses must implement the abstract methods
    to provide specific execution behavior.
    """
    
    # Default strategy class and value, will be overridden by subclasses
    strategy_class: Type[Enum] = cast(Type[Enum], None)
    default_strategy = None
    
    def __init__(self, depth: int = 0):
        """Initialize the executor.
        
        Args:
            depth: Execution depth level (0 for top-level)
        """
        self.depth = depth
        self._graph = None
        self.layer = "base"  # Will be overridden by subclasses
        self.logger = logging.getLogger(f"dxa.execution.{self.layer}")
        self._strategy = self.default_strategy
        self._configure_logger()
    
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
    def graph(self) -> Optional[ExecutionGraph]:
        """Get current execution graph."""
        return self._graph
    
    @graph.setter
    def graph(self, graph: ExecutionGraph) -> None:
        """Set current execution graph."""
        self._graph = graph
    
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
        upper_graph: ExecutionGraph, 
        context: ExecutionContext,
        upper_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute an execution graph.
        
        This method handles the overall execution of a graph, including:
        1. Creating a graph for this execution layer if needed
        2. Setting up the execution context
        3. Traversing the graph according to the strategy
        4. Processing and returning execution signals
        
        Args:
            upper_graph: Graph from the upper execution layer
            context: Execution context
            upper_signals: Signals from the upper execution layer
            
        Returns:
            List of execution signals resulting from the execution
        """
        # Create graph for this execution layer if needed
        if self.graph is None:
            self.graph = self._create_graph(
                upper_graph=upper_graph,
                context=context
            )
        
        # Set graph in context
        self._set_graph_in_context(self.graph, context)
        
        # Log execution start
        self._log_execution_start()
        
        # Check for custom traversal strategy
        custom_signals = await self._custom_graph_traversal(
            graph=self.graph,
            context=context,
            upper_signals=upper_signals
        )
        
        if custom_signals is not None:
            return custom_signals
        
        # Default traversal: follow graph structure
        signals = []
        
        # Start from the START node
        start_node = self.graph.get_start_node()
        if not start_node:
            self.logger.error("No START node found in graph")
            return signals
        
        # Initialize cursor at START node
        self.graph.update_cursor(start_node.node_id)
        
        # Process nodes in order determined by graph structure
        current_node = start_node
        prev_signals = upper_signals or []
        
        while current_node:
            # Execute current node
            node_signals = await self.execute_node(
                node=current_node,
                context=context,
                prev_signals=prev_signals,
                upper_signals=upper_signals
            )
            
            # Add signals to result
            signals.extend(node_signals)
            
            # Process signals for this node
            self._process_node_signals(current_node.node_id, node_signals)
            
            # Update previous signals for next node
            prev_signals = node_signals
            
            # Get next node based on graph structure
            next_nodes = self.graph.get_valid_transitions(
                current_node.node_id, 
                context
            )
            
            if not next_nodes:
                break
                
            # For now, just take the first valid transition
            # More complex traversal would be implemented in _custom_graph_traversal
            current_node = next_nodes[0]
            self.graph.update_cursor(current_node.node_id)
        
        return signals
    
    async def _custom_graph_traversal(
        self,
        graph: ExecutionGraph,
        context: ExecutionContext,
        upper_signals: Optional[List[ExecutionSignal]] = None
    ) -> Optional[List[ExecutionSignal]]:
        """Implement custom traversal strategies.
        
        Override this method in subclasses to implement custom traversal logic.
        Return None to use the default traversal.
        
        Args:
            graph: Execution graph to traverse
            context: Execution context
            upper_signals: Signals from upper execution layer
            
        Returns:
            List of signals if custom traversal was performed, None otherwise
        """
        # Default implementation: no custom traversal
        return None
    
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
    
    @abstractmethod
    async def execute_node(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a single node in the graph.
        
        This method handles the execution of a single node, including:
        1. Checking if the node should be executed
        2. Preparing the node for execution
        3. Executing the node's task (implementing the specific execution logic)
        4. Processing the results
        
        Subclasses must implement this method with the specific execution
        logic for their node types.
        
        Args:
            node: Node to execute
            context: Execution context
            prev_signals: Signals from previous nodes
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals resulting from the node execution
        """
        pass
    
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
        """Handle an error that occurred during node execution.
        
        Args:
            node_id: ID of the node where the error occurred
            error: Error message
        """
        self.logger.error(f"Error executing node {node_id}: {error}")
        
        # Update node status in graph
        if self.graph and node_id in self.graph.nodes:
            self.graph.update_node_status(node_id, ExecutionNodeStatus.ERROR)
    
    def _create_error_signal(self, node_id: str, error: str) -> ExecutionSignal:
        """Create an error signal for a node.
        
        Args:
            node_id: ID of the node where the error occurred
            error: Error message
            
        Returns:
            Error signal
        """
        return ExecutionSignal(
            type=ExecutionSignalType.CONTROL_ERROR,
            content={
                "node": node_id,
                "message": error
            }
        )
    
    @abstractmethod
    def _create_graph(
        self, 
        upper_graph: ExecutionGraph, 
        objective: Optional[Objective] = None, 
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create an execution graph for this executor.
        
        This method creates a graph for this execution layer based on
        the upper layer's graph and the execution context.
        
        Args:
            upper_graph: Graph from the upper execution layer
            objective: Execution objective
            context: Execution context
            
        Returns:
            Execution graph for this layer
        """
        pass
    
    def _create_sequence_graph(
        self, 
        nodes: List[ExecutionNode]
    ) -> ExecutionGraph:
        """Create a sequential execution graph from a list of nodes.
        
        Args:
            nodes: List of nodes to include in the graph
            
        Returns:
            Sequential execution graph
        """
        # Create graph
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
    
    def create_error_signal(
        self, 
        node_id: str, 
        error: str
    ) -> ExecutionSignal:
        """Create an error signal for a node.
        
        Args:
            node_id: ID of the node where the error occurred
            error: Error message
            
        Returns:
            Error signal
        """
        return ExecutionSignal(
            type=ExecutionSignalType.CONTROL_ERROR,
            content={
                "node": node_id,
                "message": error
            }
        )
    
    def _log_execution_start(self):
        """Log the start of execution."""
        graph_name = self.graph.name if self.graph else "unnamed"
        self.logger.info(
            f"Starting {self.layer} execution: {graph_name} "
            f"with strategy {self.strategy.name if self.strategy else 'DEFAULT'}"
        ) 