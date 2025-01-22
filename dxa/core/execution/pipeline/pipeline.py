"""Pipeline implementation.

This module implements a pipeline that uses ExecutionGraph structure 
to create a flexible pipeline system.

Features:
- Process data through a series of steps
- Handle both function and resource-based steps
- Buffer data between steps
"""

from typing import Dict, Any, Optional, List, Protocol, runtime_checkable
from dataclasses import dataclass, field
from ....common.graph import NodeType
from ...execution import (
    ExecutionGraph, ExecutionNode, ExecutionEdge,
    Executor, ExecutionSignal, ExecutionContext
)

@runtime_checkable
class PipelineStep(Protocol):
    """Protocol defining a pipeline step."""
    async def __call__(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the step on input data."""
        ...

    @property
    def description(self) -> str:
        """Get step description."""
        return "Pipeline step"

@dataclass
class PipelineNode(ExecutionNode):
    """Pipeline node that executes a step.
    
    Args:
        node_id: Unique identifier for the node
        node_type: Type of node (SOURCE, TRANSFORM, SINK)
        description: Human readable description
        step: The pipeline step to execute
        buffer_config: Configuration for node's data buffer
    """
    step: PipelineStep
    buffer_config: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "size": 1000,
        "mode": "streaming"
    })

    def __init__(self, node_id: str, node_type: NodeType, description: str, 
                 step: PipelineStep, buffer_config: Dict[str, Any]) -> None:
        super().__init__(node_id, node_type, description)
        if not isinstance(step, PipelineStep):
            raise TypeError(f"Step must implement PipelineStep protocol, got {type(step)}")
        self.step = step
        self.buffer_config = buffer_config

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the pipeline step."""
        return await self.step(data)

class PipelineExecutor(Executor):
    """Executes pipeline steps in sequence."""

    async def execute_node(self, node: ExecutionNode, context: ExecutionContext, 
                         prev_signals: List[ExecutionSignal], 
                         upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute a pipeline step."""
        if not isinstance(node, PipelineNode):
            raise TypeError(f"Expected PipelineNode, got {type(node)}")
        try:
            data = context.buffer_data.get(node.node_id, {})
            result = await node.execute(data)
            return [self.create_result_signal(node.node_id, result)]
        except Exception as e:
            return [self.create_error_signal(node.node_id, str(e))]

    def _create_graph(self, upper_graph: ExecutionGraph, 
                     objective: Optional[Any] = None, 
                     context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create execution graph - for pipeline this is already built."""
        return upper_graph

class Pipeline(ExecutionGraph):
    """A data processing pipeline.
    
    Uses ExecutionGraph structure to create a flexible pipeline system.
    
    Args:
        name: Pipeline identifier
        steps: List of processing steps
        buffer_size: Maximum size of step buffers
        batch_size: Optional batch processing size
    """

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
        self._context: Optional[ExecutionContext] = None
        
        # Build graph from steps
        self._build_graph(steps)

    @property
    def context(self) -> Optional[ExecutionContext]:
        """Get execution context."""
        return self._context

    @context.setter
    def context(self, context: ExecutionContext) -> None:
        """Set execution context."""
        self._context = context

    def _build_graph(self, steps: List[PipelineStep]) -> None:
        """Build execution graph from steps."""
        prev_node = None
        for i, step in enumerate(steps):
            # Create node
            node_id = f"{self.name}_step_{i}"
            node_type = NodeType.TRANSFORM
            if i == 0:
                node_type = NodeType.SOURCE
            elif i == len(steps) - 1:
                node_type = NodeType.SINK
                
            # Configure buffer for step
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

    async def execute(self) -> Dict[str, Any]:
        """Execute pipeline."""
        if self.context is None:
            raise RuntimeError("Pipeline context not set. Call setup() first.")
        executor = PipelineExecutor()
        executor.graph = self
        return await executor.execute(self, self.context)

    async def setup(self, context: ExecutionContext) -> None:
        """Setup pipeline buffers."""
        self.context = context
        await self.setup_node_buffers(context)

    async def cleanup(self, context: ExecutionContext) -> None:
        """Cleanup pipeline buffers."""
        await self.cleanup_node_buffers(context)

    def get_next_nodes(self, node_id: str) -> List[ExecutionNode]:
        """Get next nodes in pipeline sequence."""
        edges = self.get_outgoing_edges(node_id)
        return [self.nodes[edge.target] for edge in edges] 