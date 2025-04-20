"""Pipeline implementation.

This module implements a pipeline that uses ExecutionGraph structure 
to create a flexible pipeline system. The Pipeline class inherits from both
ExecutionGraph and BaseResource, allowing it to function both as a graph-based
execution flow and as a data resource that can be managed by the resource system.

This dual inheritance design supports a structure that has graph execution flow
for data processing, but also behaves as a data resource that can be discovered,
initialized, and used through the standard resource interface.

Features:
- Process data through a series of steps
- Handle both function and resource-based steps
- Buffer data between steps
- Function as a resource for discovery and management
"""

from time import perf_counter
from typing import Dict, Any, Optional, List, Callable, Awaitable, cast
from dataclasses import dataclass, field
from opendxa.common.graph import NodeType
from opendxa.base.resource import BaseResource, ResourceResponse
from opendxa.common.mixins.loggable import Loggable
from opendxa.base.execution import (
    ExecutionGraph, ExecutionNode, ExecutionEdge,
    ExecutionSignal, ExecutionContext,
    ExecutionSignalType
)
from .pipeline_context import PipelineContext

# A pipeline step is just an async function that processes data
PipelineStep = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

@dataclass
class PipelineNode(ExecutionNode, Loggable):
    """Pipeline node that executes a step."""

    step: Optional[PipelineStep] = None
    buffer_config: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "size": 1000,
        "mode": "streaming"
    })

    def __post_init__(self):
        """Initialize Loggable after dataclass initialization."""
        Loggable.__init__(self)

    async def _identity(self, data: Any) -> Any:
        """Identity function."""
        return data

    def __init__(
        self,
        node_id: str,
        node_type: NodeType,
        objective: str,
        step: Optional[PipelineStep] = None,
        buffer_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize pipeline node."""
        super().__init__(node_id=node_id, node_type=node_type, objective=objective)

        if step is None:
            step = cast(PipelineStep, self._identity)
        self.step = step

        if buffer_config is None:
            buffer_config = {
                "enabled": False,
                "size": 1000,
                "mode": "streaming"
            }
        self.buffer_config = buffer_config

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the pipeline step."""
        if self.step is None:
            raise RuntimeError("No step defined for node")

        result = await self.step(data)
        return result

class Pipeline(ExecutionGraph, BaseResource, Loggable):
    """A data processing pipeline that also behaves as a resource.
    
    This class inherits from both ExecutionGraph and BaseResource, allowing it to:
    1. Function as a graph-based execution flow for data processing
    2. Behave as a resource that can be discovered, initialized, and used
    
    This dual inheritance design supports a structure that has graph execution flow
    for data processing, but also behaves as a data resource that can be discovered,
    initialized, and used through the standard resource interface.
    """

    def __init__(
        self,
        name: str,
        steps: List[PipelineStep],
        objective: str,
        buffer_size: int = 1000,
        batch_size: Optional[int] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize pipeline.
        
        Args:
            name: Pipeline name
            steps: List of pipeline steps
            objective: Pipeline objective
            buffer_size: Size of the buffer for data between steps
            batch_size: Optional batch size for processing
            description: Optional pipeline description
            config: Optional resource configuration dictionary
        """
        # Initialize ExecutionGraph with objective and name
        ExecutionGraph.__init__(self, objective=objective, name=name)
        
        # Initialize BaseResource with config
        BaseResource.__init__(self, name=name, description=description, config=config)
        
        # Initialize Loggable
        Loggable.__init__(self)
        
        # Pipeline-specific initialization
        self.steps = steps
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self._context: Optional[PipelineContext] = None
        self._cleaned_up = False
        self._buffers_initialized = False
        self._build_graph(steps)

    @property
    def context(self) -> Optional[PipelineContext]:
        """Get execution context."""
        return self._context

    @context.setter
    def context(self, context: ExecutionContext) -> None:
        """Set execution context."""
        if not isinstance(context, PipelineContext):
            raise TypeError("Pipeline requires PipelineContext")
        self._context = context

    def _build_graph(self, steps: List[PipelineStep]) -> None:
        """Build execution graph from steps."""
        prev_node = None
        for i, step in enumerate(steps):
            node_id = f"{self.name}_step_{i}"
            node_type = NodeType.TRANSFORM
            if i == 0:
                node_type = NodeType.SOURCE
            elif i == len(steps) - 1:
                node_type = NodeType.SINK

            buffer_config = {
                "enabled": True,
                "size": self.buffer_size,
                "mode": "streaming"
            }

            self.add_node(PipelineNode(
                node_id=node_id,
                node_type=node_type,
                objective=getattr(step, 'description', str(step)),
                step=step,
                buffer_config=buffer_config
            ))

            if prev_node:
                self.add_edge(ExecutionEdge(source=prev_node, target=node_id))
            prev_node = node_id
        
        ExecutionGraph._add_start_end_nodes(graph=self, node_cls=PipelineNode)

    async def execute(self, context: Optional[PipelineContext] = None) -> Dict[str, Any]:
        """Execute pipeline with context."""
        if context is None:
            context = PipelineContext()
            
        self.context = context
        
        try:
            start_time = perf_counter()
            result = await self._execute()
            duration = perf_counter() - start_time
            self.info("Completed pipeline '%s' in %.2f seconds", self.name, duration)
            return result
        except Exception as e:
            self.error("Pipeline '%s' failed: %s", self.name, str(e))
            raise

    async def _execute(self) -> Dict[str, Any]:
        """Execute pipeline (raw, i.e. without context setup)."""
        if self.context is None:
            raise RuntimeError("Pipeline context not set. Call setup() first.")

        try:
            await self.setup_node_buffers(self.context)
            # pylint: disable=import-outside-toplevel
            from .pipeline_executor import PipelineExecutor
            executor = PipelineExecutor()
            # Note: The PipelineExecutor class should handle setting the graph
            signals = await executor.execute(self, self.context)
            # Get final result from last signal
            return signals[-1].content.get("result", {})
        finally:
            await self.cleanup_node_buffers(self.context)
            self._cleaned_up = True
            self._buffers_initialized = False  # Reset for next execution

    async def setup(self, context: PipelineContext) -> None:
        """Setup pipeline buffers."""
        self.context = context
        await self.setup_node_buffers(context)

    async def cleanup_buffers(self, context: ExecutionContext) -> None:
        """Cleanup pipeline buffers."""
        if self._cleaned_up:
            return
        
        await self.cleanup_node_buffers(context)
        self._cleaned_up = True
        self._buffers_initialized = False  # Reset for next execution

    def get_next_nodes(self, node_id: str) -> List[ExecutionNode]:
        """Get next nodes in pipeline sequence."""
        edges = self.get_outgoing_edges(node_id)
        return [self.nodes[edge.target] for edge in edges]

    async def setup_node_buffers(self, context: ExecutionContext) -> None:
        """Setup buffers for all nodes in pipeline."""
        if not isinstance(context, PipelineContext):
            raise TypeError("Expected PipelineContext, got %s" % type(context))
            
        context = cast(PipelineContext, context)
        
        # Skip if buffers already initialized
        if self._buffers_initialized:
            return
            
        # Setup buffers for all nodes
        for node_id, node in self.nodes.items():
            if isinstance(node, PipelineNode) and node.buffer_config["enabled"]:
                buffer_size = node.buffer_config["size"]
                self.debug("Setting up buffer for %s with size %d", node_id, buffer_size)
                await context.setup_buffer(node_id, buffer_size)
                
        self._buffers_initialized = True

    async def cleanup_node_buffers(self, context: ExecutionContext) -> None:
        """Cleanup buffers for all nodes."""
        context = cast(PipelineContext, context)
        self.debug("Cleaning up all buffers")
        await context.cleanup_buffers()

    async def send_data_signal(
        self,
        source: str,
        target: str,
        data: Any,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionSignal:
        """Send data between nodes via signals."""
        signal = ExecutionSignal(
            type=ExecutionSignalType.BUFFER_DATA,
            content={
                "source": source,
                "target": target,
                "data": data
            }
        )
        if context:
            context = cast(PipelineContext, context)
            await context.send_data(target, data)
        return signal

    async def receive_data_signal(
        self,
        node_id: str,
        context: ExecutionContext
    ) -> Optional[ExecutionSignal]:
        """Receive data for a node via signals."""
        if node_id not in self.nodes:
            return None

        node = self.nodes[node_id]
        if not isinstance(node, PipelineNode) or not node.buffer_config["enabled"]:
            return None

        context = cast(PipelineContext, context)
        data = context.buffer_data.get(node.node_id, {})
        if data is not None:
            return ExecutionSignal(
                type=ExecutionSignalType.BUFFER_DATA,
                content={
                    "node": node_id,
                    "data": data
                }
            )
        return None

    def process_signal(self, signal: ExecutionSignal) -> List[ExecutionSignal]:
        """Process pipeline-specific signals."""
        new_signals = []

        if signal.type == ExecutionSignalType.BUFFER_DATA:
            target = signal.content.get("target")
            assert target is not None
            if target in self.nodes and self.context:
                node = self.nodes[target]
                if isinstance(node, PipelineNode) and node.buffer_config["enabled"]:
                    context = cast(PipelineContext, self.context)
                    buffer = context.buffers.get(target)
                    if buffer and buffer.full():
                        new_signals.append(ExecutionSignal(
                            type=ExecutionSignalType.BUFFER_FULL,
                            content={
                                "node": target,
                                "state": "full"
                            }
                        ))

        return super().process_signal(signal) + new_signals
        
    # BaseResource implementation
    async def initialize(self) -> None:
        """Initialize the pipeline resource."""
        # Call BaseResource's initialize
        await super().initialize()
        
        # Pipeline-specific initialization
        self.info(f"Initializing pipeline resource [{self.name}]")
        # Additional initialization if needed
        
    async def cleanup(self) -> None:
        """Clean up the pipeline resource."""
        # Pipeline-specific cleanup
        if self._context:
            await self.cleanup_node_buffers(self._context)
            self._cleaned_up = True
            self._buffers_initialized = False
            
        # Call BaseResource's cleanup
        await super().cleanup()
        
    async def query(self, request: Optional[Dict[str, Any]] = None) -> ResourceResponse:
        """Execute the pipeline with the provided request data.
        
        Args:
            request: Dictionary containing:
                - data: Input data for the pipeline
                - options: Optional pipeline execution options
                
        Returns:
            ResourceResponse with the pipeline execution results
        """
        if not self._is_available:
            return ResourceResponse.error_response(f"Pipeline resource {self.name} not initialized")
        
        if request is None:
            request = {}
            
        try:
            # Extract data and options from request
            input_data = request.get("data", {})
            options = request.get("options", {})
            
            # Create execution context if needed
            context = options.get("context")
            if not context:
                context = PipelineContext()
                
            # Execute the pipeline with input data
            result = await self.execute(context)
            
            return ResourceResponse(
                success=True,
                content={"result": result, "input_data": input_data}
            )
        except Exception as e:
            self.error(f"Error executing pipeline: {str(e)}")
            return ResourceResponse.error_response(str(e))
            
    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if the pipeline can handle this request.
        
        Args:
            request: Request to check
            
        Returns:
            True if the pipeline can handle this request
        """
        # Check if this is a pipeline request
        request_type = request.get("type", "")
        return request_type == "pipeline" or "pipeline" in request_type 