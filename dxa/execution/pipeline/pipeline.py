"""Pipeline implementation.

This module implements a pipeline that uses ExecutionGraph structure 
to create a flexible pipeline system.

Features:
- Process data through a series of steps
- Handle both function and resource-based steps
- Buffer data between steps
"""

from time import perf_counter
from typing import Dict, Any, Optional, List, Callable, Awaitable, cast
from dataclasses import dataclass, field
from ...common.graph import NodeType
from ...execution import (
    ExecutionGraph, ExecutionNode, ExecutionEdge,
    ExecutionSignal, ExecutionContext,
    ExecutionSignalType
)
from .pipeline_context import PipelineContext
from ...common import DXA_LOGGER

# A pipeline step is just an async function that processes data
PipelineStep = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

@dataclass
class PipelineNode(ExecutionNode):
    """Pipeline node that executes a step."""

    step: Optional[PipelineStep] = None
    buffer_config: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "size": 1000,
        "mode": "streaming"
    })

    async def _identity(self, data: Any) -> Any:
        """Identity function."""
        return data

    def __init__(
        self,
        node_id: str,
        node_type: NodeType,
        description: str,
        step: Optional[PipelineStep] = None,
        buffer_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize pipeline node."""
        super().__init__(node_id=node_id, node_type=node_type, description=description)

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

class Pipeline(ExecutionGraph):
    """A data processing pipeline."""

    def __init__(
        self,
        name: str,
        steps: List[PipelineStep],
        buffer_size: int = 1000,
        batch_size: Optional[int] = None
    ) -> None:
        """Initialize pipeline."""
        super().__init__()
        self.name = name
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self._context: Optional[PipelineContext] = None
        self._cleaned_up = False  # Track cleanup state
        self._buffers_initialized = False  # Track buffer setup state
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
                description=getattr(step, 'description', str(step)),
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
            DXA_LOGGER.info("Completed pipeline '%s' in %.2f seconds", self.name, duration)
            return result
        except Exception as e:
            DXA_LOGGER.error("Pipeline '%s' failed: %s", self.name, str(e))
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
            executor.graph = self
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

    async def cleanup(self, context: ExecutionContext) -> None:
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
                DXA_LOGGER.debug("Setting up buffer for %s with size %d", node_id, buffer_size)
                await context.setup_buffer(node_id, buffer_size)
                
        self._buffers_initialized = True

    async def cleanup_node_buffers(self, context: ExecutionContext) -> None:
        """Cleanup buffers for all nodes."""
        context = cast(PipelineContext, context)
        DXA_LOGGER.debug("Cleaning up all buffers")
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