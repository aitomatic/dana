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

from dana.api.client import APIClient
from dana.api.server import APIServiceManager
from dana.common.mixins.loggable import Loggable
from dana.common.resource.llm.llm_resource import LLMResource
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.parser.utils.parsing_utils import ParserCache
from dana.core.lang.sandbox_context import SandboxContext
from dana.frameworks.poet.client import POETClient, set_default_client


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


class DanaSandbox(Loggable):
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

    # Resource pooling for better leak resistance and performance
    _shared_api_service: APIServiceManager | None = None
    _shared_api_client: APIClient | None = None
    _shared_llm_resource: LLMResource | None = None
    _resource_users = 0  # Count of instances using shared resources
    _pool_lock = None  # Will be initialized as threading.Lock() when needed

    def __init__(self, debug_mode: bool = False, context: SandboxContext | None = None):
        """
        Initialize a Dana sandbox.

        Args:
            debug_mode: Enable debug logging
            context: Optional custom context (creates default if None)
        """
        super().__init__()  # Initialize Loggable
        self.debug_mode = debug_mode
        self._context = context or self._create_default_context()
        self._interpreter = DanaInterpreter()
        self._parser = ParserCache.get_parser("dana")

        # Set interpreter in context
        self._context.interpreter = self._interpreter

        # Automatic lifecycle management
        self._initialized = False
        self._cleanup_called = False  # Prevent double cleanup
        self._using_shared = False  # Track if using shared resources
        self._api_service: APIServiceManager | None = None
        self._api_client: APIClient | None = None
        self._llm_resource: LLMResource | None = None

        # Track instances for cleanup with weakref callback
        DanaSandbox._instances.add(self)
        self._register_cleanup()

        # Register for automatic cleanup on garbage collection
        self._weakref = weakref.ref(self, self._cleanup_on_deletion)

    def _register_cleanup(self):
        """Register process exit cleanup handler"""
        if not DanaSandbox._cleanup_registered:
            atexit.register(DanaSandbox._cleanup_all_instances)
            DanaSandbox._cleanup_registered = True

    def _create_default_context(self) -> SandboxContext:
        """Create a default execution context - resources added on first use."""
        context = SandboxContext()
        # Don't initialize resources here - use lazy initialization

        # Placeholder for feedback function
        def feedback_placeholder(result: Any, feedback_data: Any):
            self.info(f"Feedback received for result: {result} -> {feedback_data}")
            return True  # Simulate success

        context.set("local:feedback", feedback_placeholder)

        return context

    def _ensure_initialized(self):
        """Lazy initialization - called on first use"""
        if self._initialized:
            return

        try:
            # Check if we can reuse shared resources (for testing efficiency)
            if self._can_reuse_shared_resources():
                self.debug("Reusing shared DanaSandbox resources")
                self._use_shared_resources()
            else:
                self.info("Initializing new DanaSandbox resources")
                self._initialize_new_resources()

            # Store in context
            self._context.set("system:api_client", self._api_client)
            self._context.set("system:llm_resource", self._llm_resource)

            # Register started APIClient as default POET client
            poet_client = POETClient.__new__(POETClient)  # Create without calling __init__
            poet_client.api = self._api_client  # Use our started APIClient
            set_default_client(poet_client)

            self._initialized = True
            self.debug("DanaSandbox resources ready")

        except Exception as e:
            self.error(f"Failed to initialize DanaSandbox: {e}")
            # Cleanup partial initialization
            self._cleanup()
            raise RuntimeError(f"DanaSandbox initialization failed: {e}")

    def _can_reuse_shared_resources(self) -> bool:
        """Check if shared resources are available and healthy"""
        return (
            DanaSandbox._shared_api_service is not None
            and DanaSandbox._shared_api_client is not None
            and DanaSandbox._shared_llm_resource is not None
        )

    def _use_shared_resources(self):
        """Use existing shared resources"""
        self._api_service = DanaSandbox._shared_api_service
        self._api_client = DanaSandbox._shared_api_client
        self._llm_resource = DanaSandbox._shared_llm_resource
        self._using_shared = True
        DanaSandbox._resource_users += 1

    def _initialize_new_resources(self):
        """Initialize new resources and potentially share them"""
        # Initialize API service
        self._api_service = APIServiceManager()
        self._api_service.startup()

        # Get API client
        self._api_client = self._api_service.get_client()
        self._api_client.startup()

        # Initialize LLM resource
        self._llm_resource = LLMResource()
        self._llm_resource.startup()

        self._using_shared = False

        # Make these resources available for sharing if none exist
        if DanaSandbox._shared_api_service is None:
            self.debug("Making resources available for sharing")
            DanaSandbox._shared_api_service = self._api_service
            DanaSandbox._shared_api_client = self._api_client
            DanaSandbox._shared_llm_resource = self._llm_resource
            DanaSandbox._resource_users = 1

    def _cleanup(self):
        """Clean up this instance's resources - safe to call multiple times"""
        if self._cleanup_called or not self._initialized:
            return

        self._cleanup_called = True

        try:
            self.debug("Cleaning up DanaSandbox resources")

            # If using shared resources, just decrement user count
            if self._using_shared:
                DanaSandbox._resource_users = max(0, DanaSandbox._resource_users - 1)
                self.debug(f"Released shared resources, {DanaSandbox._resource_users} users remaining")

                # Only clean up shared resources if this is the last user
                if DanaSandbox._resource_users == 0:
                    self.debug("Last user - cleaning up shared resources")
                    self._cleanup_shared_resources()

                # Clear local references but don't shutdown
                self._llm_resource = None
                self._api_client = None
                self._api_service = None
            else:
                # Clean up instance-specific resources
                self._cleanup_instance_resources()

            # Clear from context
            if hasattr(self._context, "delete"):
                try:
                    self._context.delete("system:api_client")
                    self._context.delete("system:llm_resource")
                except Exception as e:
                    self.debug(f"Error clearing context during cleanup: {e}")

            self._initialized = False
            self.debug("DanaSandbox cleanup completed")

        except Exception as e:
            self.error(f"Error during DanaSandbox cleanup: {e}")
            # Even if cleanup fails, mark as not initialized to prevent resource leaks
            self._initialized = False

    def _cleanup_instance_resources(self):
        """Clean up resources specific to this instance"""
        if self._llm_resource:
            try:
                self._llm_resource.shutdown()
            except Exception as e:
                self.warning(f"Error shutting down LLM resource: {e}")
            finally:
                self._llm_resource = None

        if self._api_client:
            try:
                self._api_client.shutdown()
            except Exception as e:
                self.warning(f"Error shutting down API client: {e}")
            finally:
                self._api_client = None

        if self._api_service:
            try:
                self._api_service.shutdown()
            except Exception as e:
                self.warning(f"Error shutting down API service: {e}")
            finally:
                self._api_service = None

    @classmethod
    def _cleanup_shared_resources(cls):
        """Clean up shared resources when no more users"""
        if cls._shared_llm_resource:
            try:
                cls._shared_llm_resource.shutdown()
            except Exception as e:
                cls.log_warning(f"Error shutting down shared LLM resource: {e}")
            finally:
                cls._shared_llm_resource = None

        if cls._shared_api_client:
            try:
                cls._shared_api_client.shutdown()
            except Exception as e:
                cls.log_warning(f"Error shutting down shared API client: {e}")
            finally:
                cls._shared_api_client = None

        if cls._shared_api_service:
            try:
                cls._shared_api_service.shutdown()
            except Exception as e:
                cls.log_warning(f"Error shutting down shared API service: {e}")
            finally:
                cls._shared_api_service = None

    @staticmethod
    def _cleanup_on_deletion(weakref_obj):
        """Cleanup callback for when instance is garbage collected"""
        # This is called when the weakref is about to be deleted
        # The actual instance is already gone, so we can't call _cleanup()
        # But we can log that cleanup happened via garbage collection
        DanaSandbox.log_debug("DanaSandbox instance garbage collected - automatic cleanup triggered")

    def __del__(self):
        """Destructor - automatic cleanup on garbage collection"""
        try:
            if hasattr(self, "_initialized") and self._initialized and not getattr(self, "_cleanup_called", False):
                self.debug("DanaSandbox garbage collected - performing automatic cleanup")
                self._cleanup()
        except Exception as e:
            # Avoid exceptions in __del__ as they can cause issues
            try:
                self.warning(f"Error in DanaSandbox.__del__: {e}")
            except Exception:
                pass  # Ignore logging errors in destructor

    @classmethod
    def _cleanup_all_instances(cls):
        """Clean up all remaining instances - called by atexit"""
        cls.log_debug("Process exit: cleaning up all DanaSandbox instances")
        instance_count = 0
        for instance in list(cls._instances):
            try:
                if hasattr(instance, "_cleanup") and not getattr(instance, "_cleanup_called", False):
                    instance._cleanup()
                    instance_count += 1
            except Exception as e:
                cls.log_error(f"Error cleaning up DanaSandbox instance: {e}")

        if instance_count > 0:
            cls.log_info(f"Cleaned up {instance_count} DanaSandbox instances at process exit")

    @classmethod
    def cleanup_all(cls):
        """
        Manually clean up all instances - useful for testing or explicit resource management.
        This is safer than relying only on garbage collection or process exit.
        """
        cls.log_info("Manual cleanup of all DanaSandbox instances requested")
        cls._cleanup_all_instances()

    def is_healthy(self) -> bool:
        """
        Check if the sandbox is in a healthy state.
        Returns False if resources have been cleaned up or are in an error state.
        """
        return (
            self._initialized
            and not self._cleanup_called
            and self._api_service is not None
            and self._api_client is not None
            and self._llm_resource is not None
        )

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
            with open(file_path) as f:
                source_code = f.read()

            # Execute through _eval (convergent path)
            result = self._interpreter._eval(source_code, context=self._context, filename=str(file_path))

            # Capture print output from interpreter buffer
            output = self._interpreter.get_and_clear_output()

            # Create execution result with context snapshot
            return ExecutionResult(
                success=True,
                result=result,
                final_context=self._context.copy(),
                output=output,
            )

        except Exception as e:
            # File execution always logs as error since these are unexpected
            self.error(f"Error executing Dana file: {e}")
            return ExecutionResult(
                success=False,
                error=e,
                final_context=self._context.copy(),
            )

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
            # Execute through _eval (convergent path)
            result = self._interpreter._eval(source_code, context=self._context, filename=filename)

            # Capture print output from interpreter buffer
            output = self._interpreter.get_and_clear_output()

            # Create execution result with context snapshot
            return ExecutionResult(
                success=True,
                result=result,
                final_context=self._context.copy(),
                output=output,
            )

        except Exception as e:
            # Check if we're in REPL mode - either by REPL markers or by filename being None (interactive)
            is_repl_mode = (
                filename is None  # Interactive evaluation (REPL)
                or self._context.get("system:__repl_input_context") is not None
                or any("__repl" in str(key) for key in self._context._state.get("system", {}).keys())
            )

            if is_repl_mode:
                # In REPL mode, syntax errors are expected user input - log as debug
                self.debug(f"Error evaluating Dana code: {e}")
            else:
                # In non-REPL mode (file execution), log as error for debugging
                self.error(f"Error evaluating Dana code: {e}")

            return ExecutionResult(
                success=False,
                error=e,
                final_context=self._context.copy(),
            )

    @classmethod
    def quick_run(cls, file_path: str | Path, debug_mode: bool = False, context: SandboxContext | None = None) -> ExecutionResult:
        """
        Quick run a Dana file without managing lifecycle.

        Args:
            file_path: Path to the .na file to execute
            debug_mode: Enable debug logging
            context: Optional custom context

        Returns:
            ExecutionResult with success status and results
        """
        with cls(debug_mode=debug_mode, context=context) as sandbox:
            return sandbox.run(file_path)

    @classmethod
    def quick_eval(
        cls, source_code: str, filename: str | None = None, debug_mode: bool = False, context: SandboxContext | None = None
    ) -> ExecutionResult:
        """
        Quick evaluate Dana code without managing lifecycle.

        Args:
            source_code: Dana code to execute
            filename: Optional filename for error reporting
            debug_mode: Enable debug logging
            context: Optional custom context

        Returns:
            ExecutionResult with success status and results
        """
        with cls(debug_mode=debug_mode, context=context) as sandbox:
            return sandbox.eval(source_code, filename)

    def __enter__(self) -> "DanaSandbox":
        """Context manager entry - ensures initialization."""
        self._ensure_initialized()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - guaranteed cleanup even on exceptions."""
        try:
            self._cleanup()
        except Exception as cleanup_error:
            # If there was already an exception, don't mask it with cleanup errors
            if exc_type is None:
                raise cleanup_error
            else:
                self.error(f"Cleanup error during exception handling: {cleanup_error}")
        # Don't suppress exceptions by returning None (implicit)

    @property
    def context(self) -> SandboxContext:
        """Public accessor for the sandbox execution context."""
        return self._context

    def load_file(self, file_path: str) -> None:
        """Load and evaluate a Dana file in the sandbox context."""
        with open(file_path, encoding="utf-8") as f:
            source_code = f.read()
        self.eval(source_code, filename=file_path)

    @property
    def function_registry(self):
        """Expose the function registry from the internal interpreter."""
        return self._interpreter.function_registry
