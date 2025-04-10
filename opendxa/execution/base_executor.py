"""Base class for all executors in the execution system."""

from abc import ABC
from enum import Enum
from typing import Generic, List, Optional, Type, TypeVar, cast, Union

from ..common.utils.logging import Loggable
from .execution_context import ExecutionContext
from .execution_graph import ExecutionGraph
from .execution_factory import ExecutionFactory
from .execution_types import (
    ExecutionNode, ExecutionSignal,
    ExecutionNodeStatus, ExecutionSignalType
)
from ..common.graph import NodeType

# Type variables for generic type parameters
StrategyT = TypeVar('StrategyT', bound=Enum)
GraphT = TypeVar('GraphT', bound=ExecutionGraph)
FactoryT = TypeVar('FactoryT', bound=ExecutionFactory)

class ExecutionError(Exception):
    """Base exception for all execution errors."""
    pass

class BaseExecutor(ABC, Loggable, Generic[StrategyT, GraphT, FactoryT]):
    """Base class for all executors in the execution system.
    
    The Executor class provides common execution logic for all layers
    in the execution system. Each layer (workflow, plan, reasoning)
    implements its own specific behavior while inheriting common
    functionality from this base class.
    """
    
    # Required class attributes that must be set by subclasses
    _strategy_type: Type[StrategyT]
    _default_strategy: StrategyT
    graph_class: Type[GraphT]
    _factory_class: Type[FactoryT]
    _depth: int
    
    def __init_subclass__(cls):
        """Validate that subclasses properly set required class attributes.
        
        This method ensures that all subclasses of Executor properly set:
        1. _strategy_type: The type of strategy enum to use
        2. _default_strategy_value: The default strategy value
        3. graph_class: The type of graph to use
        4. _depth: The execution layer depth
        
        Raises:
            TypeError: If any required class attributes are missing or invalid
        """
        # Check for required class attributes
        required_attrs = [
            '_strategy_type',
            '_default_strategy',
            'graph_class',
            '_depth'
        ]
        
        for attr in required_attrs:
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must set {attr}")
                
        # Validate strategy type
        if not issubclass(cls._strategy_type, Enum):
            raise TypeError(f"{cls.__name__}._strategy_type must be an Enum subclass")
            
        # Validate default strategy value
        if not isinstance(cls._default_strategy, cls._strategy_type):
            raise TypeError(
                f"{cls.__name__}._default_strategy must be of type {cls._strategy_type.__name__}"
            )
            
        # Validate graph class
        if not issubclass(cls.graph_class, ExecutionGraph):
            raise TypeError(f"{cls.__name__}.graph_class must be a subclass of ExecutionGraph")

        # Validate factory class
        if not issubclass(cls._factory_class, ExecutionFactory):
            raise TypeError(f"{cls.__name__}._factory_class must be a subclass of ExecutionFactory")
            
        # Validate depth
        if not isinstance(cls._depth, int):
            raise TypeError(f"{cls.__name__}._depth must be an integer")
            
    def __init__(
        self,
        strategy: Optional[StrategyT] = None,
        lower_executor: Optional['BaseExecutor'] = None
    ):
        """Initialize executor.
        
        Args:
            strategy: Execution strategy (defaults to class default)
            lower_executor: Executor for lower layer tasks
            
        Raises:
            TypeError: If strategy is not of the correct type
            ValueError: If strategy is invalid
        """
        if strategy is not None and not isinstance(strategy, self._strategy_type):
            raise TypeError(f"Strategy must be of type {self._strategy_type.__name__}")
            
        self._strategy = strategy or self._default_strategy
        self._graph: Optional[GraphT] = None
        self.lower_executor = lower_executor
        
        # Initialize Loggable with appropriate logger name
        Loggable.__init__(self, logger_name=f"opendxa.execution.{self.graph_class.__name__.lower()}")
    
    @property
    def strategy(self) -> StrategyT:
        """Get the current strategy."""
        return self._strategy
    
    @property
    def graph(self) -> Optional[GraphT]:
        """Get the current graph."""
        return self._graph
    
    # Core Execution Methods
    async def execute(
        self,
        graph: GraphT,
        context: ExecutionContext
    ) -> List[ExecutionSignal]:
        """Execute a graph using common execution logic."""
        # Set current graph
        self._set_graph(graph)
        
        # Set graph in context
        self._set_graph_in_context(graph, context)
        
        # Log execution start
        self._log_execution_start(graph)
        
        # Create cursor starting at START node
        cursor = graph.start_cursor()
        graph.cursor = cursor
        
        # Execute nodes in sequence
        signals = []
        
        # Traverse graph using cursor
        while True:
            node = cursor.next()
            if node is None:
                break
                
            # Execute current node
            node_signals = await self.execute_node(
                cast(ExecutionNode, node),
                context
            )
            signals.extend(node_signals)
        
        return signals
        
    async def execute_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext
    ) -> List[ExecutionSignal]:
        """Execute a node in the execution graph."""
        try:
            # Initial status check
            if node.status == ExecutionNodeStatus.BLOCKED:
                return []
                
            # Set to PENDING when execution begins
            node.status = ExecutionNodeStatus.PENDING
            
            # Phase 1: Pre-execution setup
            await self._pre_execute_node(node)
            
            # Phase 2: Node validation
            if not self._validate_node_for_execution(node):
                node.status = ExecutionNodeStatus.SKIPPED
                return []
            
            # Set to IN_PROGRESS when actual execution starts
            node.status = ExecutionNodeStatus.IN_PROGRESS
            
            # Phase 3: Build context
            execution_context = self.build_execution_context(
                context, node
            )
            
            # Phase 4: Execute node
            signals = await self._execute_node_core(node, execution_context)
            
            # Phase 5: Process signals
            processed_signals = self._process_signals(signals, node)
            
            # Phase 6: Post-execution cleanup
            await self._post_execute_node(node)
            
            # Set to COMPLETED on success
            node.status = ExecutionNodeStatus.COMPLETED
            return processed_signals
            
        except Exception as e:
            # Set to FAILED on error
            node.status = ExecutionNodeStatus.FAILED
            # _handle_error will always return a List[ExecutionSignal] when create_signal=True
            return self._handle_error(node, e, create_signal=True) or []
            
    async def _execute_node_core(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a node by delegating to the lower executor."""
        # Create graph for lower layer
        if self.lower_executor is None:
            raise ExecutionError("No lower executor available")
            
        if not self.graph:
            raise ExecutionError("No current graph available")
            
        lower_graph = self.lower_executor.create_graph_from_upper_node(node, self.graph)
        if not lower_graph:
            raise ExecutionError("Failed to create graph for lower layer")
        
        return await self.lower_executor.execute(lower_graph, context)
        
    # Execution Phases
    async def _pre_execute_node(self, node: ExecutionNode) -> None:
        """Set up pre-execution state for a node."""
        try:
            self.logger.info(f"Executing {self.graph_class.__name__.lower()} node: {node.node_id}")
            
            # Update node status
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
        except Exception as e:
            raise ExecutionError("Pre-execution setup failed") from e
            
    def _validate_node_for_execution(self, node: ExecutionNode) -> bool:
        """Validate a node for execution."""
        try:
            # Skip START and END nodes
            if node.node_type in [NodeType.START, NodeType.END]:
                return False
                
            # Ensure node has metadata
            if node.metadata is None:
                node.metadata = {}
                
            return True
        except Exception as e:
            raise ExecutionError("Node validation failed") from e
            
    def build_execution_context(
        self,
        context: ExecutionContext,
        node: ExecutionNode,
        parent_node: Optional[ExecutionNode] = None
    ) -> ExecutionContext:
        """Build execution context for a node."""
        try:
            # Create layer-specific context
            layer_context = {
                "node_id": node.node_id,
                "node_type": node.node_type,
                "description": node.description,
                "metadata": node.metadata or {}
            }
            
            # Update node metadata with layer context
            node.metadata[f"{self.graph_class.__name__.lower()}_context"] = layer_context
            
            # Create new execution context
            return ExecutionContext(
                workflow_llm=context.workflow_llm,
                planning_llm=context.planning_llm,
                reasoning_llm=context.reasoning_llm,
                agent_state=context.agent_state,
                world_state=context.world_state,
                execution_state=context.execution_state,
                current_workflow=context.current_workflow,
                current_plan=context.current_plan,
                current_reasoning=context.current_reasoning,
                global_context=context.global_context,
                resources=context.resources
            )
        except Exception as e:
            raise ExecutionError("Context building failed") from e
            
    def _process_signals(
        self,
        signals: List[ExecutionSignal],
        node: Optional[ExecutionNode] = None
    ) -> List[ExecutionSignal]:
        """Process execution signals."""
        try:
            # Handle error signals
            error_signals = [
                signal for signal in signals
                if signal.type == ExecutionSignalType.CONTROL_ERROR
            ]
            if error_signals:
                for signal in error_signals:
                    node_id = signal.content.get("node")
                    error_msg = signal.content.get("error", "Unknown error")
                    self.logger.error(f"Error in node {node_id}: {error_msg}")
                    
                    # Update node status if graph is available
                    if self.graph and isinstance(node_id, str) and node_id in self.graph.nodes:
                        self.graph.update_node_status(node_id, ExecutionNodeStatus.FAILED)
                return error_signals
            
            # Process control signals
            control_signals = [
                signal for signal in signals
                if signal.type in [
                    ExecutionSignalType.CONTROL_STATE_CHANGE,
                    ExecutionSignalType.CONTROL_COMPLETE
                ]
            ]
            for signal in control_signals:
                if signal.type == ExecutionSignalType.CONTROL_STATE_CHANGE:
                    # Update graph metadata if available
                    if self.graph and "metadata" in signal.content:
                        self.graph.metadata.update(signal.content["metadata"])
                        
                elif signal.type == ExecutionSignalType.CONTROL_COMPLETE:
                    # Handle step completion
                    if node_id := signal.content.get("node"):
                        if self.graph and node_id in self.graph.nodes:
                            self.graph.update_node_status(node_id, ExecutionNodeStatus.COMPLETED)
            
            # Return result signals
            return [
                signal for signal in signals
                if signal.type == ExecutionSignalType.DATA_RESULT
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to process signals: {e}")
            return []
            
    async def _post_execute_node(self, node: ExecutionNode) -> None:
        """Clean up post-execution state for a node."""
        try:
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.COMPLETED)
        except Exception as e:
            raise ExecutionError("Post-execution cleanup failed") from e
            
    # Graph Management
    def _set_graph(self, graph: GraphT) -> None:
        """Set the current graph."""
        if not isinstance(graph, self.graph_class):
            raise TypeError(f"Graph must be of type {self.graph_class.__name__}")
            
        # Validate graph before setting
        self._validate_graph(graph)
        self._graph = graph
        
    def _set_graph_in_context(
        self, 
        graph: GraphT, 
        context: ExecutionContext
    ) -> None:
        """Set the current graph in the execution context."""
        if context is None:
            raise ExecutionError("Context cannot be None")
        setattr(context, f"current_{self.graph_class.__name__.lower()}", graph)
        
    def _validate_graph(self, graph: GraphT) -> None:
        """Validate a graph before execution."""
        if not graph:
            raise ExecutionError("Graph cannot be None")
            
        # Check for required nodes
        start_node = graph.get_start_node()
        if not start_node:
            raise ExecutionError("Graph must have a START node")
            
        end_nodes = graph.get_end_nodes()
        if not end_nodes:
            raise ExecutionError("Graph must have at least one END node")
            
        # Validate node types
        for node in graph.nodes.values():
            if node.node_type not in NodeType:
                raise ExecutionError(f"Invalid node type: {node.node_type}")
                
        # Check for cycles using topological sort
        try:
            list(graph)  # This will raise ValueError if there are cycles
        except ValueError as e:
            raise ExecutionError("Graph has cycles") from e
            
        # Check for unreachable nodes
        reachable = set()
        if start_node:
            for node in graph:
                reachable.add(node.node_id)
                
        unreachable = set(graph.nodes.keys()) - reachable
        if unreachable:
            raise ExecutionError(f"Unreachable nodes: {unreachable}")
            
        # Validate edge connections
        for edge in graph.edges:
            if edge.source not in graph.nodes:
                raise ExecutionError(f"Edge source {edge.source} not in graph")
            if edge.target not in graph.nodes:
                raise ExecutionError(f"Edge target {edge.target} not in graph")
                
    # Error Handling
    def _handle_error(
        self,
        node_or_id: Union[ExecutionNode, str],
        error: Union[Exception, str],
        create_signal: bool = True
    ) -> Optional[List[ExecutionSignal]]:
        """Handle execution errors for a node."""
        # Get node ID and error message
        node_id = node_or_id.node_id if isinstance(node_or_id, ExecutionNode) else node_or_id
        error_msg = str(error)
        
        # Log error
        self.logger.error(f"Error executing node {node_id}: {error_msg}")
        
        # Update node status in graph
        if self.graph and node_id in self.graph.nodes:
            self.graph.update_node_status(node_id, ExecutionNodeStatus.FAILED)
        
        # Create and return error signal if requested
        if create_signal:
            return [self._create_error_signal(node_id, error_msg)]
        return None
        
    def _create_error_signal(self, node_id: str, error: str) -> ExecutionSignal:
        """Create an error signal."""
        return ExecutionSignal(
            type=ExecutionSignalType.CONTROL_ERROR,
            content={
                "node": node_id,
                "error": error
            }
        )
        
    # Utility Methods
    def create_graph_from_upper_node(
        self,
        node: ExecutionNode,
        upper_graph: ExecutionGraph
    ) -> Optional[GraphT]:
        """Create a graph for this layer from an upper layer node."""
        try:
            # Create a basic graph with START -> TASK -> END using the factory
            return self._factory_class.create_basic_graph(
                objective=node.objective,
                name=f"{self.graph_class.__name__.lower()}_{node.node_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to create {self.graph_class.__name__.lower()} graph: {e}")
            return None
            
    def _log_execution_start(self, graph: ExecutionGraph):
        """Log the start of graph execution."""
        self.logger.info(
            f"Starting {self.graph_class.__name__.lower()} execution with {len(graph.nodes)} nodes"
        ) 

    