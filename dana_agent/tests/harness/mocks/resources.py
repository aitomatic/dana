"""
Mock Resources and Workflows for STARAgent robustness testing.
"""

from __future__ import annotations

import asyncio
from typing import Any

from dana.core.resource.base_resource import BaseResource
from dana.core.workflow.base_workflow import BaseWorkflow


class MockResource(BaseResource):
    """
    Simple mock resource for testing.

    Tracks all calls and can be configured to return specific responses
    or raise exceptions.
    """

    def __init__(
        self,
        resource_id: str = "mock-resource",
        default_response: str = "Mock resource response",
        auto_register: bool = False,
        **kwargs,
    ):
        super().__init__(resource_id=resource_id, auto_register=auto_register, **kwargs)
        self.default_response = default_response
        self.call_history: list[dict[str, Any]] = []
        self._response_queue: list[str | Exception] = []
        self._delay_ms: int = 0

    def set_delay(self, delay_ms: int) -> None:
        """Set delay for all method calls."""
        self._delay_ms = delay_ms

    def queue_response(self, response: str | Exception) -> None:
        """Queue a response or exception for the next call."""
        self._response_queue.append(response)

    def _get_response(self) -> str:
        """Get next queued response or default."""
        if self._response_queue:
            response = self._response_queue.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return self.default_response

    def _apply_delay(self) -> None:
        """Apply configured delay."""
        if self._delay_ms > 0:
            import time
            time.sleep(self._delay_ms / 1000)

    def query(self, message: str = "", **kwargs) -> str:
        """Query method - commonly used by agents."""
        self._apply_delay()
        self.call_history.append({
            "method": "query",
            "message": message,
            "kwargs": kwargs,
        })
        return self._get_response()

    def read(self, **kwargs) -> str:
        """Read method."""
        self._apply_delay()
        self.call_history.append({
            "method": "read",
            "kwargs": kwargs,
        })
        return self._get_response()

    def write(self, content: str = "", **kwargs) -> str:
        """Write method."""
        self._apply_delay()
        self.call_history.append({
            "method": "write",
            "content": content,
            "kwargs": kwargs,
        })
        return self._get_response()


class AsyncMockResource(BaseResource):
    """
    Mock resource with async methods for testing async execution paths.
    """

    def __init__(
        self,
        resource_id: str = "async-mock-resource",
        default_response: str = "Async mock response",
        auto_register: bool = False,
        **kwargs,
    ):
        super().__init__(resource_id=resource_id, auto_register=auto_register, **kwargs)
        self.default_response = default_response
        self.call_history: list[dict[str, Any]] = []
        self._delay_ms: int = 0

    def set_delay(self, delay_ms: int) -> None:
        """Set delay for all method calls."""
        self._delay_ms = delay_ms

    async def query(self, message: str = "", **kwargs) -> str:
        """Async query method."""
        if self._delay_ms > 0:
            await asyncio.sleep(self._delay_ms / 1000)
        self.call_history.append({
            "method": "query",
            "message": message,
            "kwargs": kwargs,
        })
        return self.default_response


class FailingResource(BaseResource):
    """
    Resource that always fails - for testing error handling.
    """

    def __init__(
        self,
        resource_id: str = "failing-resource",
        exception_type: type[Exception] = RuntimeError,
        exception_message: str = "Resource failed intentionally",
        auto_register: bool = False,
        **kwargs,
    ):
        super().__init__(resource_id=resource_id, auto_register=auto_register, **kwargs)
        self.exception_type = exception_type
        self.exception_message = exception_message
        self.call_count = 0

    def query(self, **kwargs) -> str:
        """Always raises an exception."""
        self.call_count += 1
        raise self.exception_type(self.exception_message)

    def read(self, **kwargs) -> str:
        """Always raises an exception."""
        self.call_count += 1
        raise self.exception_type(self.exception_message)


class MockWorkflow(BaseWorkflow):
    """
    Simple mock workflow for testing.
    """

    def __init__(
        self,
        workflow_id: str = "mock-workflow",
        default_result: dict | None = None,
        auto_register: bool = False,
        **kwargs,
    ):
        super().__init__(workflow_id=workflow_id, auto_register=auto_register, **kwargs)
        self.default_result = default_result or {"result": "workflow executed"}
        self.call_history: list[dict[str, Any]] = []
        self._result_queue: list[dict | Exception] = []
        self._delay_ms: int = 0

    def set_delay(self, delay_ms: int) -> None:
        """Set delay for execution."""
        self._delay_ms = delay_ms

    def queue_result(self, result: dict | Exception) -> None:
        """Queue a result or exception."""
        self._result_queue.append(result)

    def _do_execute(self, **kwargs) -> dict:
        """Execute the workflow."""
        if self._delay_ms > 0:
            import time
            time.sleep(self._delay_ms / 1000)

        self.call_history.append({
            "kwargs": kwargs,
        })

        if self._result_queue:
            result = self._result_queue.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        return {**self.default_result, **kwargs}


class AsyncMockWorkflow(BaseWorkflow):
    """
    Mock workflow with async execution.
    """

    def __init__(
        self,
        workflow_id: str = "async-mock-workflow",
        default_result: dict | None = None,
        auto_register: bool = False,
        **kwargs,
    ):
        super().__init__(workflow_id=workflow_id, auto_register=auto_register, **kwargs)
        self.default_result = default_result or {"result": "async workflow executed"}
        self.call_history: list[dict[str, Any]] = []
        self._delay_ms: int = 0

    def set_delay(self, delay_ms: int) -> None:
        """Set delay for execution."""
        self._delay_ms = delay_ms

    async def _do_execute(self, **kwargs) -> dict:
        """Async execute the workflow."""
        if self._delay_ms > 0:
            await asyncio.sleep(self._delay_ms / 1000)

        self.call_history.append({
            "kwargs": kwargs,
        })

        return {**self.default_result, **kwargs}


class FailingWorkflow(BaseWorkflow):
    """
    Workflow that always fails.
    """

    def __init__(
        self,
        workflow_id: str = "failing-workflow",
        exception_type: type[Exception] = RuntimeError,
        exception_message: str = "Workflow failed intentionally",
        auto_register: bool = False,
        **kwargs,
    ):
        super().__init__(workflow_id=workflow_id, auto_register=auto_register, **kwargs)
        self.exception_type = exception_type
        self.exception_message = exception_message
        self.call_count = 0

    def _do_execute(self, **kwargs) -> dict:
        """Always raises an exception."""
        self.call_count += 1
        raise self.exception_type(self.exception_message)
