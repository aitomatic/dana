"""Mixin for queryable objects."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional

from opendxa.common.mixins.tool_callable import ToolCallable
from opendxa.common.types import BaseResponse


class QueryStrategy(Enum):
    """Resource querying strategies."""

    ONCE = auto()  # Single query without iteration, default for most resources
    ITERATIVE = auto()  # Iterative querying - default, e.g., for LLMResource


@dataclass
class QueryResponse(BaseResponse):
    """Base class for all query responses."""


class Queryable(ToolCallable):
    """Mixin for queryable objects that can be called as tools.

    This mixin enables resources to be both queried directly and called as tools
    within the tool-calling ecosystem. The query() method is automatically exposed
    as a tool through the ToolCallable interface, allowing Queryable objects to
    be seamlessly integrated into tool-calling systems.
    """

    def __init__(self):
        """Initialize the Queryable object."""
        ToolCallable.__init__(self)
        self._query_strategy = getattr(self, "_query_strategy", QueryStrategy.ONCE)
        self._query_max_iterations = getattr(self, "_query_max_iterations", 3)

    @ToolCallable.tool
    async def query(self, params: Optional[Dict[str, Any]] = None) -> QueryResponse:
        """Query the Queryable object.

        Args:
            params: The parameters to query the Queryable object with.
        """
        return QueryResponse(success=True, content=params, error=None)

    def get_query_strategy(self) -> QueryStrategy:
        """Get the query strategy for the resource."""
        return self._query_strategy

    def get_query_max_iterations(self) -> int:
        """Get the maximum number of iterations for the resource. Default is 3."""
        return self._query_max_iterations
