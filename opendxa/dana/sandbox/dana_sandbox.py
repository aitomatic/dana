"""
Dana Sandbox - Public API Entry Point

This module provides the main public API for executing Dana code.
Users should interact with DanaSandbox rather than the internal DanaInterpreter.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import atexit
import weakref
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opendxa.api.client import APIClient
from opendxa.api.service_manager import APIServiceManager
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


@dataclass
class ExecutionResult:
    """Result of executing Dana code."""

    success: bool
    result: Any = None
    final_context: SandboxContext | None = None
    execution_time: float = 0.0
    error: Exception | None = None
    output: str = ""

    def __str__(self) -> str:
        """Human-readable execution summary."""
        if self.success:
            return f"Success: {self.result}"
        else:
            return f"Error: {self.error}"


class DanaSandbox:
    """
    Dana Sandbox - The official way to execute Dana code.

    This is the main public API that users should interact with.
    It provides a clean, safe interface for running Dana files and evaluating code.
    
    Features automatic lifecycle management - resources are initialized on first use
    and cleaned up automatically at process exit.
    """

    # Class-level tracking for automatic cleanup
    _instances = weakref.WeakSet()
    _cleanup_registered = False

    def __init__(self, debug: bool = False, context: SandboxContext | None = None):
        """
        Initialize a Dana sandbox.

        Args:
            debug: Enable debug logging
            context: Optional custom context (creates default if None)
        """
        self.debug = debug
        self._context = context or self._create_default_context()
        self._interpreter = DanaInterpreter()
        self._parser = DanaParser()
        
        # Automatic lifecycle management
        self._initialized = False
        self._api_service: APIServiceManager | None = None
        self._api_client: APIClient | None = None
        self._llm_resource: LLMResource | None = None
        
        # Track instances for cleanup
        DanaSandbox._instances.add(self)
        self._register_cleanup()

    def _register_cleanup(self):
        """Register process exit cleanup handler"""
        if not DanaSandbox._cleanup_registered:
            atexit.register(DanaSandbox._cleanup_all_instances)
            DanaSandbox._cleanup_registered = True

    def _create_default_context(self) -> SandboxContext:
        """Create a default execution context - resources added on first use."""
        context = SandboxContext()
        # Don't initialize resources here - use lazy initialization
        return context

    def _ensure_initialized(self):
        """Lazy initialization - called on first use"""
        if self._initialized:
            return

        try:
            DXA_LOGGER.info("Initializing DanaSandbox resources")

            # Initialize API service
            self._api_service = APIServiceManager()
            self._api_service.startup()

            # Get API client
            self._api_client = self._api_service.get_client()
            self._api_client.startup()

            # Initialize LLM resource
            self._llm_resource = LLMResource()
            self._llm_resource.startup()

            # Store in context
            self._context.set("system.api_client", self._api_client)
            self._context.set("system.llm_resource", self._llm_resource)

            self._initialized = True
            DXA_LOGGER.info("DanaSandbox resources initialized successfully")

        except Exception as e:
            DXA_LOGGER.error(f"Failed to initialize DanaSandbox: {e}")
            # Cleanup partial initialization
            self._cleanup()
            raise RuntimeError(f"DanaSandbox initialization failed: {e}")

    def _cleanup(self):
        """Clean up this instance's resources"""
        if not self._initialized:
            return

        try:
            DXA_LOGGER.info("Cleaning up DanaSandbox resources")

            # Cleanup in reverse order
            if self._llm_resource:
                self._llm_resource.shutdown()
                self._llm_resource = None

            if self._api_client:
                self._api_client.shutdown()
                self._api_client = None

            if self._api_service:
                self._api_service.shutdown()
                self._api_service = None

            # Clear from context
            if hasattr(self._context, 'delete'):
                try:
                    self._context.delete("system.api_client")
                    self._context.delete("system.llm_resource")
                except Exception:
                    pass  # Ignore errors during cleanup

            self._initialized = False
            DXA_LOGGER.info("DanaSandbox resources cleaned up")

        except Exception as e:
            DXA_LOGGER.error(f"Error during DanaSandbox cleanup: {e}")

    @classmethod
    def _cleanup_all_instances(cls):
        """Clean up all remaining instances - called by atexit"""
        DXA_LOGGER.info("Cleaning up all DanaSandbox instances")
        for instance in list(cls._instances):
            try:
                instance._cleanup()
            except Exception as e:
                DXA_LOGGER.error(f"Error cleaning up DanaSandbox instance: {e}")

    def run(self, file_path: str | Path) -> ExecutionResult:
        """
        Run a Dana file.

        Args:
            file_path: Path to the .na file to execute

        Returns:
            ExecutionResult with success status and results
        """
        self._ensure_initialized()  # Auto-initialize on first use
        
        try:
            # Read file
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if not file_path.suffix == ".na":
                raise ValueError(f"File must have .na extension: {file_path}")

            source_code = file_path.read_text()

            # Use internal _run method for actual execution
            result = self._interpreter._run(file_path, source_code, self._context)
            output = self._interpreter.get_and_clear_output()

            return ExecutionResult(success=True, result=result, final_context=self._context, output=output)

        except Exception as e:
            return ExecutionResult(success=False, error=e, final_context=self._context)

    def eval(self, source_code: str, filename: str | None = None) -> ExecutionResult:
        """
        Evaluate Dana source code.

        Args:
            source_code: Dana code to execute
            filename: Optional filename for error reporting

        Returns:
            ExecutionResult with success status and results
        """
        self._ensure_initialized()  # Auto-initialize on first use
        
        try:
            # Use internal _eval method for actual execution
            result = self._interpreter._eval(source_code, self._context, filename)
            output = self._interpreter.get_and_clear_output()

            return ExecutionResult(success=True, result=result, final_context=self._context, output=output)

        except Exception as e:
            return ExecutionResult(success=False, error=e, final_context=self._context)

    @classmethod
    def quick_run(cls, file_path: str | Path, debug: bool = False, context: SandboxContext | None = None) -> ExecutionResult:
        """
        Quick file execution (class method).

        Args:
            file_path: Path to the .na file to execute
            debug: Enable debug logging
            context: Optional custom context

        Returns:
            ExecutionResult with success status and results
        """
        sandbox = cls(debug=debug, context=context)
        return sandbox.run(file_path)

    @classmethod
    def quick_eval(
        cls, source_code: str, filename: str | None = None, debug: bool = False, context: SandboxContext | None = None
    ) -> ExecutionResult:
        """
        Quick code evaluation (class method).

        Args:
            source_code: Dana code to execute
            filename: Optional filename for error reporting
            debug: Enable debug logging
            context: Optional custom context

        Returns:
            ExecutionResult with success status and results
        """
        sandbox = cls(debug=debug, context=context)
        return sandbox.eval(source_code, filename)

    # Context manager support (optional explicit lifecycle control)
    def __enter__(self) -> "DanaSandbox":
        """Context manager entry - explicit initialization"""
        self._ensure_initialized()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - explicit cleanup"""
        self._cleanup()
