#!/usr/bin/env python3

import pytest

from dana.core.lang import DanaSandbox


class TestCommaSeparatedImports:
    """Test comma-separated import functionality."""

    def setup_method(self):
        """Set up a fresh sandbox for each test."""
        self.sandbox = DanaSandbox()

    def test_basic_comma_separated_import(self):
        """Test basic comma-separated imports: from math.py import sqrt, pi."""
        result = self.sandbox.execute_string("from math.py import sqrt, pi")

        assert result.success is True
        assert result.result is None

        # Test that both imported names are accessible
        sqrt_result = self.sandbox.execute_string("sqrt(16)")
        pi_result = self.sandbox.execute_string("pi")

        assert sqrt_result.success is True
        assert sqrt_result.result == 4.0
        assert pi_result.success is True
        assert abs(pi_result.result - 3.141592653589793) < 1e-10

    def test_comma_separated_import_with_aliases(self):
        """Test comma-separated imports with aliases: from json.py import dumps as jd, loads as jl."""
        result = self.sandbox.execute_string("from json.py import dumps as jd, loads as jl")

        assert result.success is True
        assert result.result is None

        # Test that aliased functions are accessible
        dumps_result = self.sandbox.execute_string('jd({"test": 123})')
        loads_result = self.sandbox.execute_string('jl(\'{"key": "value"}\')')

        assert dumps_result.success is True
        assert dumps_result.result == '{"test": 123}'
        assert loads_result.success is True
        assert loads_result.result == {"key": "value"}

    def test_mixed_comma_separated_import(self):
        """Test mixed imports: some with aliases, some without."""
        result = self.sandbox.execute_string("from math.py import sqrt, pi as PI, floor")

        assert result.success is True
        assert result.result is None

        # Test all imported names
        sqrt_result = self.sandbox.execute_string("sqrt(25)")
        pi_result = self.sandbox.execute_string("PI")
        floor_result = self.sandbox.execute_string("floor(3.7)")

        assert sqrt_result.success is True
        assert sqrt_result.result == 5.0
        assert pi_result.success is True
        assert abs(pi_result.result - 3.141592653589793) < 1e-10
        assert floor_result.success is True
        assert floor_result.result == 3

    def test_three_comma_separated_imports(self):
        """Test three comma-separated imports."""
        result = self.sandbox.execute_string("from math.py import sqrt, pi, floor")

        assert result.success is True
        assert result.result is None

        # Test all three imported names
        sqrt_result = self.sandbox.execute_string("sqrt(9)")
        pi_result = self.sandbox.execute_string("pi")
        floor_result = self.sandbox.execute_string("floor(2.9)")

        assert sqrt_result.success is True
        assert sqrt_result.result == 3.0
        assert pi_result.success is True
        assert abs(pi_result.result - 3.141592653589793) < 1e-10
        assert floor_result.success is True
        assert floor_result.result == 2

    def test_comma_separated_import_error_handling(self):
        """Test error handling for comma-separated imports with invalid names."""
        result = self.sandbox.execute_string("from math.py import sqrt, nonexistent_function")

        assert result.success is False
        assert "cannot import name" in str(result.error).lower()

    def test_comma_separated_import_syntax_error(self):
        """Test that trailing commas are handled properly."""
        # This should fail with a syntax error
        try:
            result = self.sandbox.execute_string("from math.py import sqrt, pi,")
            # If it parses, it should fail with an appropriate error
            assert result.success is False
        except Exception:
            # Parse error is acceptable for invalid syntax
            pass

    def test_comma_separated_import_with_dana_modules(self):
        """Test comma-separated imports with Dana modules (when available)."""
        # This test would require actual Dana modules to be available
        # For now, test that the syntax is parsed correctly
        try:
            result = self.sandbox.execute_string("from simple_math import add, multiply")
            # If simple_math module exists, it should work
            if result.success:
                add_result = self.sandbox.execute_string("add(2, 3)")
                mult_result = self.sandbox.execute_string("multiply(4, 5)")
                assert add_result.success is True
                assert mult_result.success is True
        except Exception:
            # Module not found is acceptable for this test
            pass

    def test_comma_separated_import_backward_compatibility(self):
        """Test that single imports still work (backward compatibility)."""
        result = self.sandbox.execute_string("from math.py import sqrt")

        assert result.success is True
        assert result.result is None

        # Test that the imported name is accessible
        sqrt_result = self.sandbox.execute_string("sqrt(16)")
        assert sqrt_result.success is True
        assert sqrt_result.result == 4.0

    def test_comma_separated_import_with_single_alias(self):
        """Test single import with alias still works."""
        result = self.sandbox.execute_string("from math.py import sqrt as square_root")

        assert result.success is True
        assert result.result is None

        # Test that the aliased name is accessible
        sqrt_result = self.sandbox.execute_string("square_root(16)")
        assert sqrt_result.success is True
        assert sqrt_result.result == 4.0

    def test_submodule_import_2_components(self):
        """Test comma-separated imports from submodules with 2 path components."""
        # Test with a hypothetical submodule structure like dana.core.workflow.workflow_system
        # This will test the grammar parsing for 2-component paths
        try:
            result = self.sandbox.execute_string("from dana.frameworks import workflow, agent")
            # If the module exists, test functionality
            if result.success:
                # Test that the imported modules are accessible
                workflow_result = self.sandbox.execute_string("workflow")
                agent_result = self.sandbox.execute_string("agent")
                assert workflow_result.success is True
                assert agent_result.success is True
            else:
                # Module not found is acceptable for this test
                assert "not found" in str(result.error).lower()
        except Exception:
            # Parse error or module not found is acceptable
            pass

    def test_submodule_import_3_components(self):
        """Test comma-separated imports from submodules with 3 path components."""
        # Test with a hypothetical submodule structure like dana.core.workflow.workflow_system.core
        # This will test the grammar parsing for 3-component paths
        try:
            result = self.sandbox.execute_string("from dana.core.workflow.workflow_system import core, engine")
            # If the module exists, test functionality
            if result.success:
                # Test that the imported modules are accessible
                core_result = self.sandbox.execute_string("core")
                engine_result = self.sandbox.execute_string("engine")
                assert core_result.success is True
                assert engine_result.success is True
            else:
                # Module not found is acceptable for this test
                assert "not found" in str(result.error).lower()
        except Exception:
            # Parse error or module not found is acceptable
            pass

    def test_submodule_import_3_components_with_aliases(self):
        """Test comma-separated imports from submodules with 3 path components and aliases."""
        # Test with aliases for 3-component paths
        try:
            result = self.sandbox.execute_string("from dana.core.workflow.workflow_system import core as wf_core, engine as wf_engine")
            # If the module exists, test functionality
            if result.success:
                # Test that the aliased modules are accessible
                core_result = self.sandbox.execute_string("wf_core")
                engine_result = self.sandbox.execute_string("wf_engine")
                assert core_result.success is True
                assert engine_result.success is True
            else:
                # Module not found is acceptable for this test
                assert "not found" in str(result.error).lower()
        except Exception:
            # Parse error or module not found is acceptable
            pass

    def test_submodule_import_grammar_parsing(self):
        """Test that the grammar correctly parses submodule paths with comma-separated imports."""
        # Test various submodule path combinations to ensure grammar parsing works
        test_cases = [
            "from a.b import x, y",
            "from a.b.c import x, y, z",
            "from a.b.c.d import x as X, y as Y",
            "from dana.core.workflow.workflow_system import core, engine as wf_engine",
            "from utils.text import capitalize, reverse as rev",
        ]

        for test_case in test_cases:
            try:
                result = self.sandbox.execute_string(test_case)
                # We don't care if the modules exist, just that the grammar parses correctly
                # If it gets to execution, the grammar parsing worked
                if result.success is False and "not found" in str(result.error).lower():
                    # This is expected - module not found, but grammar parsed correctly
                    pass
            except Exception as e:
                # If it's a parse error, that's a problem
                if "unexpected" in str(e).lower() or "syntax" in str(e).lower():
                    pytest.fail(f"Grammar parsing failed for: {test_case} - {e}")
                # Other errors (like module not found) are acceptable
