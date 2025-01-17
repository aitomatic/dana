"""Pipeline types and data structures."""

import asyncio
from typing import Dict, Any, Union, Callable, Awaitable, TypeVar
from dataclasses import dataclass, field
from ..base_resource import BaseResource

T = TypeVar('T')  # Generic type for pipeline data

# Type aliases
PipelineStep = Union[
    Callable[[Dict[str, T]], Awaitable[Dict[str, T]]],  # Function step
    BaseResource  # Resource step
]
PipelineData = Dict[str, Any]

@dataclass
class PipelineContext:
    """Pipeline execution context."""
    buffers: Dict[str, asyncio.Queue] = field(default_factory=dict)
    data: PipelineData = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
