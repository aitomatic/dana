"""Performance baseline tests for import functionality (Step 5.5).

This test suite measures:
- Import statement execution time
- Module loading performance
- Memory usage of loaded modules
- Performance comparison between Python and Dana imports
"""

import os
import time
from pathlib import Path

import pytest

from opendxa.dana.module.core import initialize_module_system, reset_module_system
from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


@pytest.mark.deep
class TestImportPerformance:
    """Performance baseline tests for import functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sandbox = DanaSandbox()

        # Set the module search path to include our test modules
        test_modules_path = Path(__file__).parent / "test_modules"
        self.test_modules_path = str(test_modules_path.resolve())

        # Add the test modules path to DANAPATH for testing
        os.environ.setdefault("DANAPATH", "")
        if self.test_modules_path not in os.environ["DANAPATH"]:
            os.environ["DANAPATH"] = f"{self.test_modules_path}{os.pathsep}{os.environ['DANAPATH']}"

        # Reset and reinitialize the module system to pick up the updated search paths
        reset_module_system()
        initialize_module_system()

    def measure_execution_time(self, operation_func, iterations=10):
        """Measure average execution time for an operation."""
        times = []
        for _ in range(iterations):
            start_time = time.perf_counter()
            operation_func()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        return {
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "total_time": sum(times),
            "iterations": iterations,
            "times": times,
        }

    def test_basic_import_performance(self):
        """Test performance of basic import statements."""

        def import_simple_math():
            result = self.sandbox.eval("import simple_math")
            assert result.success is True
            return result

        # Measure basic import performance
        perf_stats = self.measure_execution_time(import_simple_math, iterations=5)

        # Performance assertions (reasonable thresholds)
        assert perf_stats["avg_time"] < 0.5, f"Basic import too slow: {perf_stats['avg_time']:.4f}s"
        assert perf_stats["max_time"] < 1.0, f"Worst case import too slow: {perf_stats['max_time']:.4f}s"
        std_dev = (sum([(t - perf_stats["avg_time"]) ** 2 for t in perf_stats["times"]]) / len(perf_stats["times"])) ** 0.5
        assert std_dev < 0.2, f"Import performance too inconsistent: {std_dev:.4f}s std dev"

        print(f"✅ Basic import performance: {perf_stats['avg_time']:.4f}s average")

    def test_python_vs_dana_import_performance(self):
        """Test performance comparison between Python and Dana imports."""

        def import_python():
            result = self.sandbox.eval("import math.py")
            assert result.success is True

        def import_dana():
            result = self.sandbox.eval("import simple_math")
            assert result.success is True

        python_stats = self.measure_execution_time(import_python, iterations=10)
        dana_stats = self.measure_execution_time(import_dana, iterations=10)

        ratio = dana_stats["avg_time"] / python_stats["avg_time"]

        print(f"Python import: {python_stats['avg_time']:.4f}s")
        print(f"Dana import: {dana_stats['avg_time']:.4f}s")
        print(f"Ratio (Dana/Python): {ratio:.2f}x")

        # Dana imports should be within reasonable overhead of Python imports
        assert ratio < 5.0, f"Dana imports too slow compared to Python: {ratio:.2f}x"

    def test_from_import_performance(self):
        """Test performance of from-import statements."""

        def from_import_operation():
            result = self.sandbox.eval("from simple_math import add")
            assert result.success is True

        perf_stats = self.measure_execution_time(from_import_operation, iterations=10)
        std_dev = (sum([(t - perf_stats["avg_time"]) ** 2 for t in perf_stats["times"]]) / len(perf_stats["times"])) ** 0.5

        # Performance assertions (reasonable thresholds)
        assert perf_stats["avg_time"] < 0.5, f"From-import too slow: {perf_stats['avg_time']:.4f}s"
        assert perf_stats["max_time"] < 1.0, f"Worst case from-import too slow: {perf_stats['max_time']:.4f}s"
        assert std_dev < 0.2, f"From-import performance too inconsistent: {std_dev:.4f}s std dev"

        print(f"From-import performance: {perf_stats['avg_time']:.4f}s average")

    def test_package_import_performance(self):
        """Test performance of package imports."""

        def import_package():
            result = self.sandbox.eval("import utils")
            assert result.success is True
            return result

        def import_submodule():
            result = self.sandbox.eval("from utils import factorial")
            assert result.success is True
            return result

        # Measure package import performance
        package_stats = self.measure_execution_time(import_package, iterations=5)
        submodule_stats = self.measure_execution_time(import_submodule, iterations=5)

        # Package imports should be reasonable
        assert package_stats["avg_time"] < 1.0, f"Package import too slow: {package_stats['avg_time']:.4f}s"
        assert submodule_stats["avg_time"] < 1.0, f"Submodule import too slow: {submodule_stats['avg_time']:.4f}s"

        print(f"Package import: {package_stats['avg_time']:.4f}s")
        print(f"Submodule import: {submodule_stats['avg_time']:.4f}s")

    def test_multiple_imports_performance(self):
        """Test performance when doing multiple imports."""

        def multiple_imports():
            imports = [
                "import simple_math",
                "import string_utils",
                "import data_types",
                "from simple_math import add",
                "from string_utils import to_upper",
            ]

            for import_stmt in imports:
                result = self.sandbox.eval(import_stmt)
                assert result.success is True

            return len(imports)

        perf_stats = self.measure_execution_time(multiple_imports, iterations=3)

        # Performance assertions
        avg_per_import = perf_stats["avg_time"] / 5  # 5 imports per iteration
        assert avg_per_import < 0.5, f"Multiple imports too slow: {avg_per_import:.4f}s per import"

        print(f"Multiple imports performance: {perf_stats['avg_time']:.4f}s total, {avg_per_import:.4f}s per import")

    def test_function_call_performance_after_import(self):
        """Test performance of calling imported functions."""
        # First import the module
        result = self.sandbox.eval("import simple_math")
        assert result.success is True

        def call_imported_function():
            result = self.sandbox.eval("simple_math.add(10, 5)")
            assert result.success is True
            return result

        # Now measure function call performance
        func_stats = self.measure_execution_time(call_imported_function, iterations=10)

        # Also test module-level calls vs direct calls
        def direct_module_call():
            result = self.sandbox.eval("simple_math.add(2, 3)")
            assert result.success is True
            return result

        module_stats = self.measure_execution_time(direct_module_call, iterations=10)

        # Function calls should be reasonably fast
        assert func_stats["avg_time"] < 0.5, f"Imported function call too slow: {func_stats['avg_time']:.4f}s"
        assert module_stats["avg_time"] < 0.5, f"Module function call too slow: {module_stats['avg_time']:.4f}s"

    def test_import_caching_performance(self):
        """Test that module caching improves performance on repeated imports."""

        def first_import():
            # Reset sandbox to clear any cached state
            self.sandbox = DanaSandbox()
            result = self.sandbox.eval("import simple_math")
            assert result.success is True
            return result

        def repeated_import():
            result = self.sandbox.eval("import simple_math")
            assert result.success is True
            return result

        # Measure first import (cache miss)
        first_stats = self.measure_execution_time(first_import, iterations=3)

        # Setup for repeated imports
        self.sandbox.eval("import simple_math")  # Prime the cache

        # Measure repeated imports (cache hits)
        repeated_stats = self.measure_execution_time(repeated_import, iterations=10)

        # Repeated imports should be faster (or at least not slower)
        assert repeated_stats["avg_time"] <= first_stats["avg_time"] * 1.5, (
            f"Caching not effective: first={first_stats['avg_time']:.4f}s, repeated={repeated_stats['avg_time']:.4f}s"
        )

        print(f"First import: {first_stats['avg_time']:.4f}s")
        print(f"Repeated import: {repeated_stats['avg_time']:.4f}s")
        print(f"Speedup ratio: {first_stats['avg_time'] / repeated_stats['avg_time']:.2f}x")

    def test_large_scale_import_performance(self):
        """Test performance with many imports and function calls."""

        def large_scale_operations():
            # Setup multiple imports
            setup_imports = [
                "import simple_math",
                "import string_utils",
                "from simple_math import add",
                "from simple_math import multiply",
                "from string_utils import to_upper",
            ]

            for import_stmt in setup_imports:
                result = self.sandbox.eval(import_stmt)
                assert result.success is True

            # Perform many operations
            operations = [
                "result1 = add(10, 20)",
                "result2 = multiply(result1, 2)",
                "result3 = simple_math.square(result2)",
                'text1 = to_upper("hello")',
                'text2 = string_utils.to_lower("WORLD")',
                "final = add(result3, 100)",
            ]

            for op in operations:
                result = self.sandbox.eval(op)
                assert result.success is True

            return len(setup_imports) + len(operations)

        perf_stats = self.measure_execution_time(large_scale_operations, iterations=1)

        # Large scale operations should complete in reasonable time
        assert perf_stats["avg_time"] < 5.0, f"Large scale operations too slow: {perf_stats['avg_time']:.4f}s"

        print(f"Large scale operations (11 total): {perf_stats['avg_time']:.4f}s")
        print(f"Average per operation: {perf_stats['avg_time'] / 11:.4f}s")

    def test_performance_summary(self):
        """Provide a comprehensive performance summary."""
        # This test runs various operations and provides a summary
        operations = {
            "Basic Import": lambda: self.sandbox.eval("import simple_math"),
            "Python Import": lambda: self.sandbox.eval("import math.py"),
            "From Import": lambda: self.sandbox.eval("from simple_math import add"),
            "Package Import": lambda: self.sandbox.eval("import utils"),
            "Function Call": lambda: self.sandbox.eval("simple_math.add(1, 2)"),
        }

        # Setup for function call test
        self.sandbox.eval("import simple_math")

        summary = {}
        for name, operation in operations.items():
            try:
                stats = self.measure_execution_time(operation, iterations=5)
                summary[name] = stats["avg_time"]
            except Exception as e:
                summary[name] = f"FAILED: {e}"

        # Print performance summary
        print("\n=== IMPORT PERFORMANCE SUMMARY ===")
        for name, avg_time in summary.items():
            if isinstance(avg_time, float):
                print(f"{name:15}: {avg_time:.4f}s")
            else:
                print(f"{name:15}: {avg_time}")

        # Verify all operations completed successfully
        failed_ops = [name for name, result in summary.items() if isinstance(result, str)]
        assert len(failed_ops) == 0, f"Failed operations: {failed_ops}"
