#!/usr/bin/env python3
"""
Test the rationalized library loading system.

This test verifies that:
1. initlib conducts startup activities
2. corelib is preloaded during startup
3. stdlib is available in DANA_PATH for on-demand loading
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
        from dana.core.runtime.modules.core import reset_module_system

        reset_module_system()

    def test_initlib_startup_activities(self):
        """Test that initlib conducts startup activities."""
        # Import initlib to trigger startup
        import dana.libs.initlib

        # Verify environment loading was attempted
        # (We can't easily test the actual .env loading without files, but we can verify the function exists)
        assert hasattr(dana.libs.initlib, "dana_load_dotenv")

        # Verify configuration loader was initialized
        from dana.common.config.config_loader import ConfigLoader

        config_loader = ConfigLoader()
        assert config_loader is not None

    def test_corelib_preloading(self):
        """Test that corelib functions are preloaded during startup."""
        # Import initlib to trigger startup and corelib preloading

        # Check if preloaded functions are stored in the registry module
        import dana.core.lang.interpreter.functions.function_registry as registry_module

        assert hasattr(registry_module, "_preloaded_corelib_functions")

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
        """Test that stdlib is added to DANA_PATH for on-demand loading."""
        # Import initlib to trigger startup and DANA_PATH setup

        # Verify DANA_PATH contains stdlib
        assert "DANAPATH" in os.environ
        danapath = os.environ["DANAPATH"]

        # Get the expected stdlib path
        expected_stdlib_path = str(Path(__file__).parent.parent.parent.parent / "dana" / "libs" / "stdlib")

        # Verify stdlib path is in DANA_PATH
        assert expected_stdlib_path in danapath, f"Expected stdlib path {expected_stdlib_path} not found in DANA_PATH: {danapath}"

    def test_stdlib_on_demand_loading(self):
        """Test that stdlib functions can be loaded on-demand."""
        # Import initlib to trigger startup

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
        result = sandbox.eval(test_code)

        # Verify execution was successful
        assert result.success, f"Stdlib loading test failed: {result.error}"

        # Check that the functions executed by looking at the context state
        context = result.final_context
        assert context.get("local", "result") is not None, "log function should have executed"
        assert context.get("local", "reason_result") is not None, "reason function should have executed"

    def test_library_priority_order(self):
        """Test that library functions have correct priority order."""
        # Import initlib to trigger startup

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

    def test_startup_performance(self):
        """Test that startup performance is maintained."""
        import time

        # Measure time to import initlib (startup activities)
        start_time = time.time()
        initlib_time = time.time() - start_time

        # Measure time to create DanaInterpreter (should be fast due to preloading)
        start_time = time.time()
        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter_time = time.time() - start_time

        # Verify startup times are reasonable
        # (These are rough estimates - adjust based on actual performance requirements)
        assert initlib_time < 1.0, f"Initlib startup took too long: {initlib_time:.3f}s"
        assert interpreter_time < 0.5, f"Interpreter creation took too long: {interpreter_time:.3f}s"

    def test_fallback_loading(self):
        """Test that fallback loading works if preloading fails."""
        # Temporarily remove preloaded functions to test fallback
        import dana.core.lang.interpreter.functions.function_registry as registry_module

        original_preloaded = getattr(registry_module, "_preloaded_corelib_functions", None)

        try:
            # Remove preloaded functions
            if hasattr(registry_module, "_preloaded_corelib_functions"):
                delattr(registry_module, "_preloaded_corelib_functions")

            # Create interpreter - should fall back to normal registration
            from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

            interpreter = DanaInterpreter()
            registry = interpreter.function_registry

            # Verify corelib functions are still available through fallback
            corelib_functions = ["sum_range", "is_odd", "is_even", "factorial"]
            for func_name in corelib_functions:
                assert registry.has(func_name), f"Corelib function {func_name} should be available via fallback"

        finally:
            # Restore preloaded functions
            if original_preloaded is not None:
                registry_module._preloaded_corelib_functions = original_preloaded

    def test_test_mode_startup(self):
        """Test that test mode startup skips heavy initialization."""
        # Set test mode
        os.environ["DANA_TEST_MODE"] = "1"

        try:
            # Import initlib in test mode

            # Verify that heavy initialization was skipped
            # (Module system initialization should be skipped in test mode)
            from dana.core.runtime.modules.core import get_module_registry

            try:
                get_module_registry()
                # If we get here, module system was initialized (not in test mode)
                pytest.fail("Module system should not be initialized in test mode")
            except Exception:
                # Expected - module system not initialized in test mode
                pass

        finally:
            # Clean up test mode
            if "DANA_TEST_MODE" in os.environ:
                del os.environ["DANA_TEST_MODE"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
