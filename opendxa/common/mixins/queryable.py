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


QueryParams = Optional[Dict[str, Any]]

@dataclass
class QueryResponse(BaseResponse):
    """Base class for all query responses."""


class Queryable():
    """Mixin for queryable objects.
      Note that the @ToolCallable.tool decorator must be applied to the instance
      query() method to expose it as a tool; the decorator is not inherited
      automatically.
    """

    def __init__(self):
        """Initialize the Queryable object."""
        self._query_strategy = getattr(self, "_query_strategy", QueryStrategy.ONCE)
        self._query_max_iterations = getattr(self, "_query_max_iterations", 3)

    @ToolCallable.tool
    async def query(self, params: QueryParams = None) -> QueryResponse:
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
