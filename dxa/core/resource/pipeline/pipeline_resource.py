"""Pipeline resource implementation.

This module implements a pipeline resource that combines BaseResource lifecycle
management with ExecutionGraph structure to create a flexible pipeline system.

Features:
- Process data through a series of steps
- Manage resources and cleanup
- Handle both function and resource-based steps
- Buffer data between steps
"""

import asyncio
from typing import Dict, Any, Optional
from ...common.graph import ExecutionGraph, NodeType
from ..base_resource import BaseResource
from .pipeline_types import (
    PipelineStep,
    PipelineData,
    PipelineContext
)

class PipelineResource(BaseResource, ExecutionGraph):
    """Resource representing a data processing pipeline.
    
    Combines BaseResource lifecycle management with ExecutionGraph structure
    to create a flexible pipeline system.
    
    Args:
        name: Pipeline identifier
        steps: List of processing steps
        buffer_size: Maximum size of step buffers
        batch_size: Optional batch processing size
    """

    def __init__(
        self, 
        name: str,
        steps: list[PipelineStep],
        buffer_size: int = 1000,
        batch_size: Optional[int] = None
    ) -> None:
        """Initialize pipeline resource.
        
        Args:
            name: Pipeline identifier
            steps: List of processing steps
            buffer_size: Maximum size of step buffers
            batch_size: Optional batch processing size
        """
        BaseResource.__init__(self, name)
        ExecutionGraph.__init__(self)
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.context = PipelineContext()
        
        # Build graph from steps
        self._build_graph(steps)

    def _build_graph(self, steps: list[PipelineStep]) -> None:
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
                
            self.add_node({
                "id": node_id,
                "type": node_type,
                "step": step
            })
            
            # Connect to previous
            if prev_node:
                self.add_edge(prev_node["id"], node_id)
            prev_node = node_id

    async def initialize(self) -> None:
        """Initialize pipeline and resources."""
        self._is_available = True

    async def execute(self) -> PipelineData:
        """Execute pipeline."""
        from .pipeline_executor import PipelineExecutor
        executor = PipelineExecutor()
        return await executor.execute(self)

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pipeline on query."""
        return await self.execute()

    async def cleanup(self) -> None:
        """Cleanup pipeline resources."""
        for node in self.nodes.values():
            step = node["step"]
            if isinstance(step, BaseResource):
                await step.cleanup() 