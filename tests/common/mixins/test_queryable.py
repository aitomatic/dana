"""Tests for the Queryable mixin."""

import pytest

from opendxa.common.mixins.queryable import Queryable, QueryStrategy
from opendxa.common.types import BaseResponse


# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=protected-access
class TestQueryable:
    """Test suite for the Queryable mixin."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        obj = Queryable()
        assert obj._query_strategy == QueryStrategy.ONCE
        assert obj._query_max_iterations == 3

    def test_get_query_strategy(self):
        """Test getting the query strategy."""
        obj = Queryable()
        assert obj.get_query_strategy() == QueryStrategy.ONCE

    def test_get_query_max_iterations(self):
        """Test getting the maximum number of iterations."""
        obj = Queryable()
        assert obj.get_query_max_iterations() == 3

    @pytest.mark.asyncio
    async def test_query_with_no_params(self):
        """Test querying with no parameters."""
        obj = Queryable()
        response = await obj.query({})
        assert isinstance(response, BaseResponse)
        assert response.success
        assert response.content == {}
        assert response.error is None

    @pytest.mark.asyncio
    async def test_query_with_params(self):
        """Test querying with parameters."""
        obj = Queryable()
        params = {"test": "value"}
        response = await obj.query(params)
        assert isinstance(response, BaseResponse)
        assert response.success
        assert response.content == params
        assert response.error is None

    def test_custom_query_strategy(self):
        """Test setting a custom query strategy."""

        class CustomQueryable(Queryable):
            _query_strategy = QueryStrategy.ITERATIVE

        obj = CustomQueryable()
        assert obj.get_query_strategy() == QueryStrategy.ITERATIVE

    def test_custom_max_iterations(self):
        """Test setting custom maximum iterations."""

        class CustomQueryable(Queryable):
            _query_max_iterations = 5

        obj = CustomQueryable()
        assert obj.get_query_max_iterations() == 5
