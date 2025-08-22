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
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.core.builtin_types.resource.builtins.llm_resource_instance import LLMResourceInstance
from dana.core.builtin_types.resource.builtins.llm_resource_type import LLMResourceType
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.parser.utils.parsing_utils import ParserCache
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.runtime import DanaThreadPool

# from dana.frameworks.poet.core.client import POETClient, set_default_client  # Removed for KISS


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
    _shared_llm_resource: LegacyLLMResource | None = None
    _resource_users = 0  # Count of instances using shared resources

    def __init__(self, debug_mode: bool = False, context: SandboxContext | None = None, module_search_paths: list[str] | None = None):
        """
        Initialize a Dana sandbox.

        Args:
            debug_mode: Enable debug logging
            context: Optional custom context (creates default if None)
            module_search_paths: Optional list of paths to search for modules
        """
        super().__init__()  # Initialize Loggable
        self.debug_mode = debug_mode
        self._context = context or self._create_default_context()
        self._interpreter = DanaInterpreter()
        self._parser = ParserCache.get_parser("dana")
        self._module_search_paths = module_search_paths

        # Set interpreter in context
        self._context.interpreter = self._interpreter

        # Store module search paths in context for import handler access
        if module_search_paths:
            self._context.set("system:module_search_paths", module_search_paths)

        # Always ensure core built-in functions are available in the sandbox's function registry
        # This is especially important in test environments where the global registry might be cleared
        try:
            # Check if basic functions are missing and register them if needed
            if not self._interpreter.function_registry.has("len", None):
                # Register built-in functions
                from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins

                do_register_py_builtins(self._interpreter.function_registry)

                # Register wrapper functions
                from pathlib import Path

                from dana.libs.corelib.py_wrappers.register_py_wrappers import _register_python_functions

                py_dir = Path(__file__).parent.parent.parent / "libs" / "corelib" / "py_wrappers"
                _register_python_functions(py_dir, self._interpreter.function_registry)

                # Debug: Check if functions are now available
                if self.debug_mode:
                    self.debug(f"Function registry has len: {self._interpreter.function_registry.has('len', None)}")
                    self.debug(f"Function registry has print: {self._interpreter.function_registry.has('print', None)}")

        except Exception as e:
            self.warning(f"Failed to load corelib functions: {e}")

        # Automatic lifecycle management
        self._initialized = False
        self._cleanup_called = False  # Prevent double cleanup
        self._using_shared = False  # Track if using shared resources
        self._api_service: APIServiceManager | None = None
        self._api_client: APIClient | None = None
        self._llm_resource: LLMResourceInstance | None = None

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
                self._use_shared_resources()
            else:
                self.info("Initializing new DanaSandbox resources")
                self._initialize_new_resources()

            # TODO(#262): Temporarily disabled API context storage
            # Store in context
            # self._context.set("system:api_client", self._api_client)

            # Set LLM resource in context so reason() function can access it
            self._context.set_system_llm_resource(self._llm_resource)

            # Enable mock mode for tests (check environment variable)
            import os

            if os.environ.get("DANA_MOCK_LLM", "false").lower() == "true":
                self._llm_resource.with_mock_llm_call(True)

            # Load Dana startup file that handles all Dana resource loading and initialization
            try:
                # Load the main Dana startup file
                startup_file = Path(__file__).parent.parent.parent / "__init__.na"
                if startup_file.exists():
                    with open(startup_file, encoding="utf-8") as f:
                        startup_code = f.read()

                    self._interpreter._eval_source_code(
                        startup_code,
                        context=self._context,
                        filename="<dana-init-na>",
                    )
                    self.info("Dana startup file loaded successfully")
                else:
                    self.warning(f"Dana startup file not found at {startup_file}")

            except Exception as startup_err:
                # Non-fatal: if startup fails, continue without it
                self.error(f"Dana startup file loading failed: {startup_err}")

            # Register started APIClient as default POET client
            # poet_client = POETClient.__new__(POETClient)  # Create without calling __init__
            # poet_client.api = self._api_client  # Use our started APIClient
            # set_default_client(poet_client)

            self._initialized = True

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
        # TODO(#262): Temporarily disabled API auto-start for development
        # Initialize API service
        # self._api_service = APIServiceManager()
        # self._api_service.startup()

        # Get API client
        # self._api_client = self._api_service.get_client()
        # self._api_client.startup()

        # Initialize LLM resource (required for core Dana functionalities involving language model operations)
        self._llm_resource = LLMResourceInstance(LLMResourceType(), LegacyLLMResource())
        # self._llm_resource = LLMResource()
        self._llm_resource.initialize()
        self._llm_resource.start()

        self._using_shared = False

        # TODO(#262): Temporarily disabled API resource sharing
        # Make these resources available for sharing if none exist
        # if DanaSandbox._shared_api_service is None:
        #     self.debug("Making resources available for sharing")
        #     DanaSandbox._shared_api_service = self._api_service
        #     DanaSandbox._shared_api_client = self._api_client
        #     DanaSandbox._shared_llm_resource = self._llm_resource
        #     DanaSandbox._resource_users = 1

    def _cleanup(self):
        """Clean up this instance's resources - safe to call multiple times"""
        if self._cleanup_called or not self._initialized:
            return

        self._cleanup_called = True

        try:
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
                try:
                    logger = cls.get_class_logger()
                    if logger and logger.handlers:
                        cls.log_warning(f"Error shutting down shared LLM resource: {e}")
                except Exception:
                    # Logger may be closed during process exit
                    pass
            finally:
                cls._shared_llm_resource = None

        if cls._shared_api_client:
            try:
                cls._shared_api_client.shutdown()
            except Exception as e:
                try:
                    logger = cls.get_class_logger()
                    if logger and logger.handlers:
                        cls.log_warning(f"Error shutting down shared API client: {e}")
                except Exception:
                    # Logger may be closed during process exit
                    pass
            finally:
                cls._shared_api_client = None

        if cls._shared_api_service:
            try:
                cls._shared_api_service.shutdown()
            except Exception as e:
                try:
                    logger = cls.get_class_logger()
                    if logger and logger.handlers:
                        cls.log_warning(f"Error shutting down shared API service: {e}")
                except Exception:
                    # Logger may be closed during process exit
                    pass
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
        # Check if logger is available before logging
        try:
            logger = cls.get_class_logger()
            if logger and logger.handlers:
                cls.log_debug("Process exit: cleaning up all DanaSandbox instances")
        except Exception:
            # Logger may be closed during process exit
            pass

        instance_count = 0
        for instance in list(cls._instances):
            try:
                if hasattr(instance, "_cleanup") and not getattr(instance, "_cleanup_called", False):
                    instance._cleanup()
                    instance_count += 1
            except Exception as e:
                try:
                    logger = cls.get_class_logger()
                    if logger and logger.handlers:
                        cls.log_error(f"Error cleaning up DanaSandbox instance: {e}")
                except Exception:
                    # Logger may be closed during process exit
                    pass

        if instance_count > 0:
            try:
                logger = cls.get_class_logger()
                if logger and logger.handlers:
                    cls.log_info(f"Cleaned up {instance_count} DanaSandbox instances at process exit")
            except Exception:
                # Logger may be closed during process exit
                pass

        # Shutdown shared ThreadPoolExecutor
        DanaThreadPool.get_instance().shutdown(wait=False)  # Don't wait during process exit

    @classmethod
    def cleanup_all(cls):
        """
        Manually clean up all instances - useful for testing or explicit resource management.
        This is safer than relying only on garbage collection or process exit.
        """
        try:
            logger = cls.get_class_logger()
            if logger and logger.handlers:
                cls.log_info("Manual cleanup of all DanaSandbox instances requested")
        except Exception:
            # Logger may be closed during process exit
            pass
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

    def execute_file(self, file_path: str | Path) -> ExecutionResult:
        """
        Run a Dana file.

        Args:
            file_path: Path to the .na file to execute

        Returns:
            ExecutionResult with success status and results
        """
        self._ensure_initialized()  # Auto-initialize on first use

        try:
            # Convert to Path for easier manipulation
            file_path = Path(file_path).resolve()

            # Add the file's directory to the module search path temporarily
            from dana.__init__.init_modules import get_module_loader

            loader = get_module_loader()
            file_dir = file_path.parent

            # Add the file's directory to search paths if not already there
            if file_dir not in loader.search_paths:
                loader.search_paths.insert(0, file_dir)

            # Set up error context with file information
            if self._context.error_context:
                self._context.error_context.set_file(str(file_path))

            # Read file
            with open(file_path) as f:
                source_code = f.read()

            # Execute through _eval (convergent path)
            result = self._interpreter._eval_source_code(source_code, context=self._context, filename=str(file_path))

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
            # Format error with location information
            from dana.common.exceptions import EnhancedDanaError
            from dana.core.lang.interpreter.error_formatter import EnhancedErrorFormatter

            formatted_error = EnhancedErrorFormatter.format_developer_error(e, self._context.error_context, show_traceback=True)

            # Log the formatted error
            self.debug(f"Error context current location: {self._context.error_context.current_location}")
            self.debug(f"Error context stack size: {len(self._context.error_context.execution_stack)}")
            # self.error(f"Error executing Dana file:\n{formatted_error}")

            # Create an enhanced error with location information
            error_context = self._context.error_context

            # If the error is already an EnhancedDanaError, preserve its location info
            if isinstance(e, EnhancedDanaError):
                # Use existing location info from the error
                enhanced_error = EnhancedDanaError(
                    formatted_error,
                    filename=e.filename or (error_context.current_file if error_context else None),
                    line=e.line or (error_context.current_location.line if error_context and error_context.current_location else None),
                    column=e.column
                    or (error_context.current_location.column if error_context and error_context.current_location else None),
                    traceback_str=e.traceback_str or (error_context.format_stack_trace() if error_context else None),
                )
            else:
                enhanced_error = EnhancedDanaError(
                    formatted_error,
                    filename=error_context.current_file if error_context else None,
                    line=error_context.current_location.line if error_context and error_context.current_location else None,
                    column=error_context.current_location.column if error_context and error_context.current_location else None,
                    traceback_str=error_context.format_stack_trace() if error_context else None,
                )
            enhanced_error.__cause__ = e

            return ExecutionResult(
                success=False,
                error=enhanced_error,
                final_context=self._context.copy(),
            )

    def execute_string(self, source_code: str, filename: str | None = None) -> ExecutionResult:
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
            result = self._interpreter._eval_source_code(source_code, context=self._context, filename=filename)

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

            # Format error with location information
            from dana.common.exceptions import EnhancedDanaError
            from dana.core.lang.interpreter.error_formatter import EnhancedErrorFormatter

            formatted_error = EnhancedErrorFormatter.format_developer_error(
                e,
                self._context.error_context,
                show_traceback=not is_repl_mode,  # Show full traceback in non-REPL mode
            )

            if is_repl_mode:
                # In REPL mode, syntax errors are expected user input - log as debug
                self.debug(f"Error evaluating Dana code: {e}")
            else:
                # In non-REPL mode (file execution), log as error for debugging
                self.error(f"Error evaluating Dana code:\n{formatted_error}")

            # Create an enhanced error with location information
            error_context = self._context.error_context

            # If the error is already an EnhancedDanaError, preserve its location info
            if isinstance(e, EnhancedDanaError):
                # Use existing location info from the error
                enhanced_error = EnhancedDanaError(
                    formatted_error,
                    filename=e.filename or (error_context.current_file if error_context else None),
                    line=e.line or (error_context.current_location.line if error_context and error_context.current_location else None),
                    column=e.column
                    or (error_context.current_location.column if error_context and error_context.current_location else None),
                    traceback_str=e.traceback_str or (error_context.format_stack_trace() if error_context else None),
                )
            else:
                enhanced_error = EnhancedDanaError(
                    formatted_error,
                    filename=error_context.current_file if error_context else None,
                    line=error_context.current_location.line if error_context and error_context.current_location else None,
                    column=error_context.current_location.column if error_context and error_context.current_location else None,
                    traceback_str=error_context.format_stack_trace() if error_context else None,
                )
            enhanced_error.__cause__ = e

            return ExecutionResult(
                success=False,
                error=enhanced_error,
                final_context=self._context.copy(),
            )

    @classmethod
    def execute_file_once(cls, file_path: str | Path, debug_mode: bool = False, context: SandboxContext | None = None) -> ExecutionResult:
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
            return sandbox.execute_file(file_path)

    @classmethod
    def execute_string_once(
        cls,
        source_code: str,
        filename: str | None = None,
        debug_mode: bool = False,
        context: SandboxContext | None = None,
        module_search_paths: list[str] | None = None,
    ) -> ExecutionResult:
        """
        Quick evaluate Dana code without managing lifecycle.

        Args:
            source_code: Dana code to execute
            filename: Optional filename for error reporting
            debug_mode: Enable debug logging
            context: Optional custom context
            module_search_paths: Optional list of paths to search for modules

        Returns:
            ExecutionResult with success status and results
        """
        with cls(debug_mode=debug_mode, context=context, module_search_paths=module_search_paths) as sandbox:
            return sandbox.execute_string(source_code, filename)

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

    @property
    def function_registry(self):
        """Expose the function registry from the internal interpreter."""
        return self._interpreter.function_registry
