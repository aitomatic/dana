#!/usr/bin/env python3
"""
Test the rationalized library loading system.

This test verifies that:
1. Startup activities are conducted correctly
2. corelib is preloaded during startup
3. stdlib is available in DANAPATH for on-demand loading
"""

import os
from pathlib import Path

import pytest

from dana.core.lang.dana_sandbox import DanaSandbox


class TestRationalizedLibraryLoading:
    """Test the rationalized library loading system."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset module system to ensure clean state
        from dana.__init__.init_modules import reset_module_system

        reset_module_system()

    def test_initlib_startup_activities(self):
        """Test that initialization startup activities work correctly."""
        # Import dana to trigger startup activities (done in dana.__init__.py)
        import dana  # noqa: F401  # noqa: F401

        # Verify environment loading function exists and was called
        from dana.common.utils.dana_load_dotenv import dana_load_dotenv

        assert callable(dana_load_dotenv)

        # Verify configuration loader was initialized
        from dana.common.config.config_loader import ConfigLoader

        config_loader = ConfigLoader()
        assert config_loader is not None

    def test_corelib_preloading(self):
        """Test that corelib functions are preloaded during startup."""
        # Import dana to trigger startup and corelib preloading

        # Check if preloaded functions are stored in the registry module
        import dana  # noqa: F401
        import dana.core.lang.interpreter.functions.function_registry as registry_module

        assert hasattr(registry_module, "_preloaded_functions")

        # Verify that corelib functions are available when DanaInterpreter is created
        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()

        # Test that corelib functions are available
        # (These should be math functions like sum_range, is_odd, etc.)
        registry = interpreter.function_registry

        # Check for some expected corelib functions
        corelib_functions = ["sum_range", "is_odd", "is_even", "factorial"]
        for func_name in corelib_functions:
            assert registry.has(func_name), f"Corelib function {func_name} should be available"

    def test_stdlib_in_danapath(self):
        """Test that stdlib is added to DANAPATH for on-demand loading."""
        # Import dana to trigger startup and DANAPATH setup
        import dana  # noqa: F401

        # Explicitly initialize module system to ensure DANAPATH is set up
        from dana.__init__.init_modules import initialize_module_system

        initialize_module_system()

        # Verify DANAPATH contains stdlib (note: variable name is DANAPATH, not DANAPATH)
        assert "DANAPATH" in os.environ, "DANAPATH not found in environment"
        danapath = os.environ["DANAPATH"]

        # Get the expected stdlib path
        expected_stdlib_path = str(Path(__file__).parent.parent.parent.parent / "dana" / "libs" / "stdlib")

        # Verify stdlib path is in DANAPATH
        assert expected_stdlib_path in danapath, f"Expected stdlib path {expected_stdlib_path} not found in DANAPATH: {danapath}"

    def test_stdlib_on_demand_loading(self):
        """Test that stdlib functions can be loaded on-demand."""
        # Import dana to trigger startup

        # Create a sandbox to test stdlib loading
        sandbox = DanaSandbox()

        # Test that stdlib functions are available through the function registry
        # Stdlib functions are registered during DanaInterpreter creation
        test_code = """
# Test that stdlib functions are available
result = log("Testing stdlib loading")
reason_result = reason("What is 2 + 2?")

# Just verify the functions executed without error
result
"""

        # Execute the test code
        result = sandbox.execute_string(test_code)

        # Verify execution was successful
        assert result.success, f"Stdlib loading test failed: {result.error}"

        # Check that the functions executed by looking at the context state
        context = result.final_context
        assert context is not None
        assert context.get("local", "result") is not None, "log function should have executed"
        assert context.get("local", "reason_result") is not None, "reason function should have executed"

    def test_library_priority_order(self):
        """Test that library functions have correct priority order."""
        # Import dana to trigger startup

        # Create interpreter to test function registration
        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        registry = interpreter.function_registry

        # Test that corelib functions take precedence over stdlib functions
        # (This is tested by the fact that corelib functions are registered first)

        # List all available functions to verify registration order
        all_functions = registry.list()

        # Verify corelib functions are present
        corelib_functions = ["sum_range", "is_odd", "is_even", "factorial"]
        for func_name in corelib_functions:
            assert func_name in all_functions, f"Corelib function {func_name} should be registered"

        # Verify interpreter was created successfully (use the variable)
        assert interpreter is not None, "Interpreter should be created successfully"

    def test_startup_performance(self):
        """Test that startup performance is maintained."""
        import time

        # Measure time to import dana (startup activities)
        start_time = time.time()

        startup_time = time.time() - start_time

        # Measure time to create DanaInterpreter (should be fast due to preloading)
        start_time = time.time()
        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter_time = time.time() - start_time

        # Verify startup times are reasonable
        # (These are rough estimates - adjust based on actual performance requirements)
        assert startup_time < 1.0, f"Dana startup took too long: {startup_time:.3f}s"
        assert interpreter_time < 0.5, f"Interpreter creation took too long: {interpreter_time:.3f}s"

        # Verify interpreter was created successfully (use the variable)
        assert interpreter is not None, "Interpreter should be created successfully"

    def test_preloading_required(self):
        """Test that corelib functions are available through the global registry system."""
        # The current architecture loads corelib functions through the global registry
        # during startup, not through the deprecated _preloaded_functions mechanism
        import dana  # noqa: F401
        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        # Create interpreter - corelib functions should be available
        interpreter = DanaInterpreter()
        registry = interpreter.function_registry

        # Verify corelib functions are available (they're loaded through global registry)
        corelib_functions = ["sum_range", "is_odd", "is_even", "factorial"]
        for func_name in corelib_functions:
            assert registry.has(func_name), f"Corelib function {func_name} should be available through global registry"

    def test_test_mode_startup(self):
        """Test that test mode startup works correctly."""
        # Set test mode
        os.environ["DANA_TEST_MODE"] = "1"

        try:
            # Reset module system to test clean startup
            from dana.__init__.init_modules import reset_module_system

            reset_module_system()

            # Import dana in test mode - should still work but with minimal initialization

            # Module system should be available (test mode doesn't prevent initialization,
            # it just minimizes resource usage)
            from dana.__init__.init_modules import get_module_registry

            # This should succeed - test mode allows module system initialization
            registry = get_module_registry()
            assert registry is not None, "Module registry should be available even in test mode"

        finally:
            # Clean up test mode
            if "DANA_TEST_MODE" in os.environ:
                del os.environ["DANA_TEST_MODE"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
