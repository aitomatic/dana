"""Pipeline-specific execution context."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
from ..execution_context import ExecutionContext
from ...common.utils.logging.loggable import Loggable

@dataclass
class PipelineContext(ExecutionContext, Loggable):
    """Context for pipeline execution with buffer management."""
    
    # Buffer management
    buffers: Dict[str, asyncio.Queue] = field(default_factory=dict)
    buffer_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    buffer_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize Loggable after dataclass initialization."""
        Loggable.__init__(self)

    async def setup_buffer(self, node_id: str, size: int = 1000) -> None:
        """Setup buffer for node."""
        self.buffers[node_id] = asyncio.Queue(maxsize=size)
        self.buffer_metrics[node_id] = {
            "created": datetime.now(),
            "messages_processed": 0,
            "last_activity": datetime.now()
        }

    async def send_data(self, node_id: str, data: Any) -> None:
        """Send data to node buffer."""
        if node_id in self.buffers:
            buffer = self.buffers[node_id]
            if buffer.full():
                self.warning("Buffer %s full", node_id, size=buffer.qsize())
            await buffer.put(data)
            self.buffer_metrics[node_id]["messages_processed"] += 1
            self.buffer_metrics[node_id]["last_activity"] = datetime.now()

    async def receive_data(self, node_id: str) -> Optional[Any]:
        """Receive data from node buffer."""
        if node_id in self.buffers:
            try:
                data = await asyncio.wait_for(self.buffers[node_id].get(), timeout=0.1)
                self.buffer_metrics[node_id]["last_activity"] = datetime.now()
                return data
            except asyncio.TimeoutError:
                return None
        return None

    async def cleanup_buffers(self) -> None:
        """Cleanup all buffers."""
        self.debug("Cleaning up pipeline buffers (count: %d)", len(self.buffers))
        for buffer in self.buffers.values():
            while not buffer.empty():
                try:
                    buffer.get_nowait()
                except asyncio.QueueEmpty:
                    break 