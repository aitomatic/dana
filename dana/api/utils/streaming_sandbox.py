"""
Streaming DanaSandbox

This module provides a custom DanaSandbox that can stream logs in real-time
via WebSocket connections during .na file execution.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from pathlib import Path
from typing import Union
from collections.abc import Callable, Awaitable

from dana.core.lang.dana_sandbox import DanaSandbox, ExecutionResult
from dana.core.lang.sandbox_context import SandboxContext
from dana.api.utils.streaming_executor import StreamingExecutor


class StreamingDanaSandbox(DanaSandbox):
    """
    Custom DanaSandbox that can stream print output in real-time.

    This sandbox extends DanaSandbox to use a StreamingExecutor that can
    stream log messages immediately via WebSocket instead of just buffering.
    """

    def __init__(
        self,
        debug_mode: bool = False,
        context: SandboxContext | None = None,
        module_search_paths: list[str] | None = None,
        log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]] | None = None,
    ):
        """
        Initialize a streaming Dana sandbox.

        Args:
            debug_mode: Enable debug logging
            context: Optional custom context (creates default if None)
            module_search_paths: Optional list of paths to search for modules
            log_streamer: Optional callback for streaming log messages in real-time
        """
        super().__init__(debug_mode, context, module_search_paths)
        self._log_streamer = log_streamer

        # Replace the standard executor with streaming executor after initialization
        self._replace_executor_after_init = True

    def _ensure_initialized(self):
        """Lazy initialization - called on first use, with custom executor setup"""
        super()._ensure_initialized()

        # Replace the executor with streaming executor if we have a log streamer
        if self._replace_executor_after_init and self._log_streamer:
            self._replace_with_streaming_executor()
            self._replace_executor_after_init = False

    def _replace_with_streaming_executor(self):
        """Replace the standard executor with a streaming executor"""
        if self._interpreter and hasattr(self._interpreter, "_executor"):
            # Get the current executor's function registry and settings
            current_executor = self._interpreter._executor
            function_registry = getattr(current_executor, "function_registry", None)
            enable_optimizations = getattr(current_executor, "_optimization_engine", None) is not None

            # Create new streaming executor with the same settings
            streaming_executor = StreamingExecutor(
                function_registry=function_registry, enable_optimizations=enable_optimizations, log_streamer=self._log_streamer
            )

            # Replace the executor in the interpreter
            self._interpreter._executor = streaming_executor

            self.debug("Replaced standard executor with StreamingExecutor for log streaming")

    def set_log_streamer(self, log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]]) -> None:
        """
        Set or update the log streamer callback.

        Args:
            log_streamer: Callback for streaming log messages in real-time
        """
        self._log_streamer = log_streamer

        # Update the executor if it's already initialized
        if self._initialized and self._interpreter and hasattr(self._interpreter, "_executor"):
            if hasattr(self._interpreter._executor, "set_log_streamer"):
                self._interpreter._executor.set_log_streamer(log_streamer)
            else:
                # Need to replace with streaming executor
                self._replace_with_streaming_executor()

    @classmethod
    def quick_run_with_streaming(
        cls,
        file_path: str | Path,
        debug_mode: bool = False,
        context: SandboxContext | None = None,
        log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]] | None = None,
    ) -> ExecutionResult:
        """
        Quick run a Dana file with log streaming support.

        Args:
            file_path: Path to the .na file to execute
            debug_mode: Enable debug logging
            context: Optional custom context
            log_streamer: Optional callback for streaming log messages

        Returns:
            ExecutionResult with success status and results
        """
        with cls(debug_mode=debug_mode, context=context, log_streamer=log_streamer) as sandbox:
            return sandbox.run_file(file_path)

    @classmethod
    def quick_eval_with_streaming(
        cls,
        source_code: str,
        filename: str | None = None,
        debug_mode: bool = False,
        context: SandboxContext | None = None,
        module_search_paths: list[str] | None = None,
        log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]] | None = None,
    ) -> ExecutionResult:
        """
        Quick evaluate Dana code with log streaming support.

        Args:
            source_code: Dana code to execute
            filename: Optional filename for error reporting
            debug_mode: Enable debug logging
            context: Optional custom context
            module_search_paths: Optional list of paths to search for modules
            log_streamer: Optional callback for streaming log messages

        Returns:
            ExecutionResult with success status and results
        """
        with cls(debug_mode=debug_mode, context=context, module_search_paths=module_search_paths, log_streamer=log_streamer) as sandbox:
            return sandbox.eval(source_code, filename)
