"""Mixin for queryable objects."""

from enum import Enum, auto
from typing import Any

from dana.common.mixins.tool_callable import ToolCallable
from dana.common.types import BaseRequest, BaseResponse


class QueryStrategy(Enum):
    """Available query strategies."""

    ONCE = auto()  # Query once
    ITERATIVE = auto()  # Iterative query
    SEMANTIC = auto()  # Semantic query with iteration
    HYBRID = auto()  # Hybrid of direct and semantic


class Queryable:
    """Mixin for queryable objects.
    Note that the @ToolCallable.tool decorator must be applied to the instance
    query() method to expose it as a tool; the decorator is not inherited
    automatically.
    """

    def __init__(self):
        """Initialize the Queryable object."""
        self._query_strategy = getattr(self, "_query_strategy", QueryStrategy.ONCE)
        self._query_max_iterations = getattr(self, "_query_max_iterations", 10)

    @ToolCallable.tool
    async def query(self, request: dict[str, Any]) -> BaseResponse:
        """Query the Queryable object.

        Args:
            request: The request to query the Queryable object with.
        """
        # Convert dict to BaseRequest if needed
        if isinstance(request, dict):
            request = BaseRequest(arguments=request)

        return BaseResponse(success=True, content=request.arguments, error=None)

    def get_query_strategy(self) -> QueryStrategy:
        """Get the query strategy for the resource."""
        return self._query_strategy

    def get_query_max_iterations(self) -> int:
        """Get the maximum number of iterations for iterative querying."""
        return self._query_max_iterations
