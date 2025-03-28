"""Base class for all executors in the execution system."""

from abc import ABC
from enum import Enum
from typing import Generic, List, Optional, Type, TypeVar, Any, cast, Dict, TYPE_CHECKING, Union

from ..common import DXA_LOGGER
from .execution_context import ExecutionContext
from .execution_graph import ExecutionGraph
from .execution_types import (
    ExecutionNode, ExecutionSignal, Objective, 
    ExecutionNodeStatus, ExecutionSignalType
)
from ..common.graph import NodeType

# Type variables for generic type parameters
StrategyT = TypeVar('StrategyT', bound=Enum)
GraphT = TypeVar('GraphT', bound=ExecutionGraph)

if TYPE_CHECKING:
    from .workflow.workflow_executor import WorkflowExecutor
    from .planning.plan_executor import PlanExecutor
    from .reasoning.reasoning_executor import ReasoningExecutor

class ExecutionError(Exception):
    """Exception raised for errors during execution."""
    pass


class Executor(ABC, Generic[StrategyT, GraphT]):
    """Base class for all executors in the execution system.
    
    The Executor class provides common execution logic for all layers
    in the execution system. Each layer (workflow, plan, reasoning)
    implements its own specific behavior while inheriting common
    functionality from this base class.
    """
    
    # Class attributes that can be overridden by subclasses
    _strategy_type: Type[StrategyT] = StrategyT  # type: ignore
    _default_strategy_value: Optional[StrategyT] = None  # Will be set by subclasses
    _graph_class: Type[GraphT] = GraphT  # type: ignore
    _depth: int = 0  # Will be overridden by subclasses
    
    def __init__(
        self,
        strategy: Optional[StrategyT] = None,
        lower_executor: Optional[Union['WorkflowExecutor', 'PlanExecutor', 'ReasoningExecutor']] = None
    ):
        """Initialize executor.
        
        Args:
            strategy: Execution strategy (defaults to class default)
            lower_executor: Optional lower layer executor
        """
        self._graph: Optional[GraphT] = None
        self.lower_executor = lower_executor
        self._strategy = strategy or self.default_strategy
        self.logger = DXA_LOGGER.getLogger(f"dxa.execution.{self.layer}")
        self._configure_logger()
    
    @property
    def layer(self) -> str:
        """Get the layer name from the graph class name."""
        return self._graph_class.__name__.lower()
    
    @property
    def strategy_class(self) -> Type[StrategyT]:
        """Get the strategy class."""
        return self._strategy_type
    
    @property
    def default_strategy(self) -> StrategyT:
        """Get the default strategy."""
        if self._default_strategy_value is None:
            raise RuntimeError(f"No default strategy set for {self.__class__.__name__}")
        return self._default_strategy_value
    
    @property
    def strategy(self) -> StrategyT:
        """Get current execution strategy."""
        return self._strategy
    
    @strategy.setter
    def strategy(self, value: StrategyT) -> None:
        """Set execution strategy."""
        if not isinstance(value, self.strategy_class):
            raise ValueError(f"Strategy must be of type {self.strategy_class}")
        self._strategy = value
    
    @property
    def graph(self) -> Optional[GraphT]:
        """Get current execution graph."""
        return self._graph
    
    @graph.setter
    def graph(self, value: Optional[GraphT]) -> None:
        """Set current execution graph."""
        if value is not None and not isinstance(value, self._graph_class):
            raise ValueError(f"Graph must be of type {self._graph_class}")
        self._graph = value
    
    @property
    def depth(self) -> int:
        """Get the layer depth."""
        return self._depth
    
    async def execute_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a node in the execution graph.
        
        This method orchestrates the execution of a node by:
        1. Setting up pre-execution state
        2. Validating the node
        3. Building execution context
        4. Executing the lower layer
        5. Cleaning up post-execution
        
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
            # Phase 1: Pre-execution setup
            await self._pre_execute_node(node)
            
            # Phase 2: Node validation
            if not self._validate_node_for_execution(node):
                return []
            
            # Phase 3: Build context
            execution_context = self._build_execution_context(node, context, prev_signals, upper_signals, lower_signals)
            
            # Phase 4: Execute lower layer
            signals = await self._execute_node_core(node, execution_context)
            
            # Phase 5: Post-execution cleanup
            await self._post_execute_node(node)
            
            return signals
            
        except Exception as e:
            return self._handle_execution_error(node, e)
    
    async def _pre_execute_node(self, node: ExecutionNode) -> None:
        """Set up pre-execution state for a node.
        
        This phase handles:
        1. Logging node execution
        2. Updating node status to IN_PROGRESS
        
        Args:
            node: Node to prepare for execution
        """
        self.logger.info(f"Executing {self.layer} node: {node.node_id}")
        
        # Update node status
        if self.graph:
            self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
    
    def _validate_node_for_execution(self, node: ExecutionNode) -> bool:
        """Validate a node for execution.
        
        This phase handles:
        1. Checking if node is START/END
        2. Validating node metadata
        
        Args:
            node: Node to validate
            
        Returns:
            True if node should be executed, False otherwise
        """
        # Skip START and END nodes
        if node.node_type in [NodeType.START, NodeType.END]:
            return False
            
        # Ensure node has metadata
        if node.metadata is None:
            node.metadata = {}
            
        return True
    
    def _build_execution_context(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> ExecutionContext:
        """Build execution context for a node.
        
        This phase handles:
        1. Building layer-specific context
        2. Updating node metadata
        3. Preparing context for lower layer
        
        Args:
            node: Node to build context for
            context: Base execution context
            prev_signals: Signals from previous execution
            upper_signals: Signals from upper layer
            lower_signals: Signals from lower layer
            
        Returns:
            Updated execution context
        """
        # Build layer-specific context
        layer_context = self._build_layer_context(node, prev_signals)
        
        # Update node metadata with layer context
        node.metadata[f"{self.layer}_context"] = layer_context
        
        # Create execution node with updated metadata (but we don't set it in context
        # because ExecutionContext doesn't have current_node attribute)
        return context
    
    async def _execute_node_core(
        self,
        node: ExecutionNode,
        context: ExecutionContext
    ) -> List[ExecutionSignal]:
        """Execute the lower layer for a node.
        
        This phase handles:
        1. Creating lower layer graph
        2. Executing lower layer graph
        
        By default, this method delegates to the lower executor.
        Only the lowest layer (ReasoningExecutor) should override this
        to actually execute tasks.
        
        Args:
            node: Node to execute lower layer for
            context: Execution context
            
        Returns:
            List of execution signals
        """
        if not self.lower_executor:
            self.logger.warning(f"No lower executor available for {self.layer} layer")
            return []
            
        # Create lower layer graph
        if self.graph is None:
            self.logger.warning(f"No graph set for {self.layer} layer")
            return []
            
        lower_graph = self.lower_executor.create_graph_from_upper_node(node, self.graph)
        if not lower_graph:
            self.logger.warning(f"Failed to create lower layer graph for node {node.node_id}")
            return []
            
        # Set the graph in context
        self.lower_executor._set_graph_in_context(lower_graph, context)
        
        # Execute the lower layer graph
        # Use type assertion since we know the lower executor's graph type
        return await self.lower_executor.execute_graph(cast(Any, lower_graph), context)
    
    async def _post_execute_node(self, node: ExecutionNode) -> None:
        """Clean up post-execution state for a node.
        
        This phase handles:
        1. Updating node status to COMPLETED
        
        Args:
            node: Node to clean up after execution
        """
        if self.graph:
            self.graph.update_node_status(node.node_id, ExecutionNodeStatus.COMPLETED)
    
    def _handle_execution_error(
        self,
        node: ExecutionNode,
        error: Exception
    ) -> List[ExecutionSignal]:
        """Handle execution errors for a node.
        
        This phase handles:
        1. Logging error
        2. Updating node status to FAILED
        3. Creating error signal
        
        Args:
            node: Node that encountered an error
            error: Exception that occurred
            
        Returns:
            List containing error signal
        """
        self.logger.error(f"Error executing node {node.node_id}: {str(error)}")
        
        # Update node status to error
        if self.graph:
            self.graph.update_node_status(node.node_id, ExecutionNodeStatus.FAILED)
        
        # Create error signal
        return [self._create_error_signal(node.node_id, str(error))]
    
    def _build_layer_context(
        self,
        node: ExecutionNode,
        prev_signals: Optional[List[ExecutionSignal]] = None
    ) -> Dict[str, Any]:
        """Build layer-specific context for node execution.
        
        This base implementation provides common context building functionality:
        1. Basic node information (ID, type, description)
        2. Node metadata
        3. Previous execution results
        
        Subclasses should call super() and extend the context with layer-specific
        information.
        
        Args:
            node: Node to build context for
            prev_signals: Signals from previous execution
            
        Returns:
            Layer-specific context dictionary
        """
        # Build base context with node information
        context = {
            "node_id": node.node_id,
            "node_type": node.node_type,
            "description": node.description,
            "metadata": node.metadata or {}
        }
        
        # Add previous outputs if available
        if prev_signals:
            context["previous_outputs"] = self._process_previous_signals(prev_signals)
        
        return context
    
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
        # DXA_LOGGER already handles configuration
        pass
    
    async def execute_graph(
        self,
        graph: GraphT,
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
        self._log_execution_start(graph)
        
        # Get start node
        start_node = graph.get_start_node()
        if not start_node:
            self.logger.error(f"{self.layer} has no START node")
            return []
            
        # Create cursor for graph traversal
        from ..common.graph.traversal import Cursor, TopologicalTraversal
        graph.cursor = Cursor(graph, start_node, TopologicalTraversal())
        
        # Execute nodes in sequence
        signals = []
        
        # Traverse graph using cursor
        for node in graph.cursor:
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
    
    # TODO: DEPRECATED
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
    
    def _get_graph_class(self) -> Type[ExecutionGraph]:
        """Get the appropriate graph class for this executor.
        
        Returns:
            Graph class for this layer
        """
        return self._graph_class
    
    def create_graph_from_upper_node(
        self,
        upper_node: ExecutionNode,
        upper_graph: ExecutionGraph,
        objective: Optional[Objective] = None,
        context: Optional[ExecutionContext] = None
    ) -> Optional[GraphT]:
        """Create an execution graph from a node in an upper layer.
        
        This base implementation provides common graph creation functionality:
        1. Checking for existing graph
        2. Creating a minimal graph if no upper graph is available
        3. Delegating to strategy-specific creation methods
        
        Subclasses should implement strategy-specific creation methods
        (e.g., _create_direct_graph, _create_dynamic_graph) and override
        this method to handle their specific graph creation logic.
        
        Args:
            upper_node: Node from upper layer
            upper_graph: Graph from upper layer
            objective: Execution objective
            context: Execution context
            
        Returns:
            Execution graph
        """
        # If we already have a graph, return it
        if self.graph is not None:
            return self.graph
        
        # If no upper graph is available, create a minimal graph
        if not upper_graph:
            return self._create_minimal_graph(upper_node, objective)
        
        # Create graph based on strategy
        if self.strategy == self.default_strategy:
            return self._create_direct_graph(upper_graph, objective, upper_node)
        else:
            # Default to direct graph creation
            return self._create_direct_graph(upper_graph, objective, upper_node)
    
    def _create_minimal_graph(
        self,
        upper_node: ExecutionNode,
        objective: Optional[Objective] = None
    ) -> GraphT:
        """Create a minimal execution graph.
        
        This base implementation creates a minimal graph with:
        1. A default objective
        2. A single task node
        3. START and END nodes
        
        Args:
            upper_node: Node from upper layer
            objective: Execution objective
            
        Returns:
            Minimal execution graph
        """
        # Create graph with default objective
        graph = self._graph_class(
            objective=objective or Objective(f"Execute {self.layer} for {upper_node.node_id}"),
            name=f"{self.layer}_for_{upper_node.node_id}"
        )
        
        # Add START node
        start_node = ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description=f"Start {self.layer} execution"
        )
        graph.add_node(start_node)
        
        # Add task node
        task_node = ExecutionNode(
            node_id=upper_node.node_id,
            node_type=upper_node.node_type,
            description=upper_node.description,
            metadata=upper_node.metadata.copy() if upper_node.metadata else {}
        )
        graph.add_node(task_node)
        
        # Add END node
        end_node = ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description=f"End {self.layer} execution"
        )
        graph.add_node(end_node)
        
        # Connect nodes in sequence
        graph.add_edge_between(start_node.node_id, task_node.node_id)
        graph.add_edge_between(task_node.node_id, end_node.node_id)
        
        return graph
    
    def _create_direct_graph(
        self,
        upper_graph: ExecutionGraph,
        objective: Optional[Objective] = None,
        upper_node: Optional[ExecutionNode] = None
    ) -> GraphT:
        """Create a direct execution graph from an upper graph.
        
        A direct graph follows the upper graph structure directly.
        This base implementation:
        1. Creates a new graph with the same objective
        2. Copies nodes and edges from the upper graph
        3. Preserves node metadata
        
        Args:
            upper_graph: Graph from upper layer
            objective: Execution objective
            upper_node: Node from upper layer to create graph for
            
        Returns:
            Direct execution graph
        """
        # Create graph with objective
        node_id = upper_node.node_id if upper_node else self.layer
        graph = self._graph_class(
            objective=objective or upper_graph.objective,
            name=f"direct_{self.layer}_for_{node_id}"
        )
        
        # Create nodes based on upper graph structure
        for node in upper_graph.nodes.values():
            # Create a copy of the node's metadata
            metadata = node.metadata.copy() if node.metadata else {}
            
            # Ensure prompt is passed through
            if "prompt" in metadata:
                metadata["prompt"] = metadata["prompt"]
            
            graph_node = ExecutionNode(
                node_id=node.node_id,
                node_type=node.node_type,
                description=node.description,
                metadata=metadata
            )
            
            # If this is the upper node, add additional metadata
            if upper_node and node.node_id == upper_node.node_id:
                graph_node.metadata["is_upper_node"] = True
                graph_node.metadata["upper_node_id"] = upper_node.node_id
            
            graph.add_node(graph_node)
        
        # Create edges based on upper graph structure
        for edge in upper_graph.edges:
            graph.add_edge_between(edge.source, edge.target)
        
        return graph
    
    def _create_sequence_graph(self, nodes: List[ExecutionNode]) -> GraphT:
        """Create a sequence graph from a list of nodes.
        
        Args:
            nodes: List of nodes to sequence
            
        Returns:
            Sequence graph
        """
        # Create graph with default objective
        graph = self._graph_class(
            objective=Objective(f"Execute {self.layer} sequence"),
            name=f"{self.layer}_sequence"
        )
        
        # Add START node
        start_node = ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description=f"Start {self.layer} sequence"
        )
        graph.add_node(start_node)
        
        # Add sequence nodes
        prev_node = start_node
        for node in nodes:
            graph.add_node(node)
            graph.add_edge_between(prev_node.node_id, node.node_id)
            prev_node = node
        
        # Add END node
        end_node = ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description=f"End {self.layer} sequence"
        )
        graph.add_node(end_node)
        graph.add_edge_between(prev_node.node_id, end_node.node_id)
        
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
    
    def _log_execution_start(self, graph: ExecutionGraph):
        """Log the start of graph execution.
        
        Args:
            graph: Graph being executed
        """
        self.logger.info(
            f"Starting {self.layer} execution with {len(graph.nodes)} nodes"
        )
    
    def _process_previous_signals(self, signals: List[ExecutionSignal]) -> Dict[str, Any]:
        """Process previous signals to extract outputs.
        
        This base implementation extracts outputs from signals of type
        ExecutionSignalType.DATA_RESULT. Subclasses can override this
        to handle additional signal types or provide custom processing.
        
        Args:
            signals: List of previous execution signals
            
        Returns:
            Dictionary mapping node IDs to their outputs
        """
        return {
            str(signal.content.get("node")): signal.content.get("result")
            for signal in signals
            if signal.type == ExecutionSignalType.DATA_RESULT
        } 