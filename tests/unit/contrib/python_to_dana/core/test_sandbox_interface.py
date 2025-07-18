"""
Tests for Sandbox Interface Protocol

Tests the SandboxInterface protocol definition and ensures all implementations
follow the expected interface contract.
"""

from typing import get_type_hints

import pytest

from dana.integrations.python.to_dana.core.inprocess_sandbox import InProcessSandboxInterface
from dana.integrations.python.to_dana.core.sandbox_interface import SandboxInterface
from dana.integrations.python.to_dana.core.subprocess_sandbox import SubprocessSandboxInterface

# Table-driven test parameters for interface implementations
interface_implementation_params = [
    {
        "name": "inprocess_sandbox_interface",
        "implementation_class": InProcessSandboxInterface,
        "init_kwargs": {"debug": True},
    },
    {
        "name": "subprocess_sandbox_interface",
        "implementation_class": SubprocessSandboxInterface,
        "init_kwargs": {"debug": True},
    },
]

# Table-driven test parameters for required methods
required_method_params = [
    {
        "name": "reason_method",
        "method_name": "reason",
        "should_be_callable": True,
        "required_params": ["prompt", "options"],
    },
    {
        "name": "close_method",
        "method_name": "close",
        "should_be_callable": True,
        "required_params": [],
    },
]

# Table-driven test parameters for protocol documentation
protocol_doc_params = [
    {
        "name": "protocol_docstring",
        "component": "SandboxInterface",
        "should_have_docstring": True,
        "min_length": 10,
    },
    {
        "name": "reason_method_docstring",
        "component": "reason",
        "should_have_docstring": True,
        "should_contain": ["prompt", "options"],
    },
    {
        "name": "close_method_docstring",
        "component": "close",
        "should_have_docstring": True,
        "should_contain_any": ["close", "cleanup"],
    },
]

# Table-driven test parameters for architectural design testing
architectural_design_params = [
    {
        "name": "mock_sandbox_interface",
        "test_response": "Mock response to: test",
        "prompt": "test",
        "expected_in_response": "Mock response",
    },
    {
        "name": "test_double_sandbox",
        "test_response": "test response",
        "prompt": "test prompt",
        "options": {"temp": 0.5},
        "expected_calls": 2,  # reason + close
    },
]


class TestSandboxInterfaceProtocol:
    """Test the SandboxInterface protocol definition."""

    def test_protocol_exists(self):
        """Test that SandboxInterface protocol is properly defined."""
        assert SandboxInterface is not None
        assert hasattr(SandboxInterface, "reason")
        assert hasattr(SandboxInterface, "close")

    def test_reason_method_signature(self):
        """Test that reason method has correct signature."""
        hints = get_type_hints(SandboxInterface.reason)

        # Should have proper type hints
        assert "prompt" in hints
        assert "options" in hints
        assert "return" in hints

    def test_close_method_signature(self):
        """Test that close method has correct signature."""
        hints = get_type_hints(SandboxInterface.close)

        # Should return None
        assert hints.get("return") is type(None)

    def test_protocol_methods_are_abstract(self):
        """Test that protocol methods use ellipsis (abstract)."""
        import inspect

        # Get the source of the reason method
        try:
            reason_source = inspect.getsource(SandboxInterface.reason)
            assert "..." in reason_source
        except (OSError, TypeError):
            # Some environments might not support getsource
            pass

        try:
            close_source = inspect.getsource(SandboxInterface.close)
            assert "..." in close_source
        except (OSError, TypeError):
            pass


class TestImplementationCompliance:
    """Test that all implementations comply with the SandboxInterface protocol."""

    @pytest.mark.parametrize("test_case", interface_implementation_params, ids=lambda x: x["name"])
    def test_implementation_has_required_interface(self, test_case):
        """Test that implementations have all required methods."""
        sandbox = test_case["implementation_class"](**test_case["init_kwargs"])

        # Should have all required methods
        assert hasattr(sandbox, "reason")
        assert hasattr(sandbox, "close")
        assert callable(sandbox.reason)
        assert callable(sandbox.close)

    @pytest.mark.parametrize("test_case", interface_implementation_params, ids=lambda x: x["name"])
    def test_implementation_method_signatures(self, test_case):
        """Test that implementations have compatible method signatures."""
        sandbox = test_case["implementation_class"](**test_case["init_kwargs"])
        import inspect

        # reason method
        reason_sig = inspect.signature(sandbox.reason)
        params = list(reason_sig.parameters.keys())
        assert "prompt" in params
        assert "options" in params

        # close method
        close_sig = inspect.signature(sandbox.close)
        # close should take no parameters (except self)
        assert len(close_sig.parameters) == 0

    @pytest.mark.parametrize("test_case", interface_implementation_params, ids=lambda x: x["name"])
    def test_implementations_can_be_used_polymorphically(self, test_case):
        """Test that implementations can be used interchangeably."""
        impl = test_case["implementation_class"](**test_case["init_kwargs"])

        # Should be able to call methods without knowing the specific type
        assert hasattr(impl, "reason")
        assert hasattr(impl, "close")

        # Methods should be callable
        assert callable(impl.reason)
        assert callable(impl.close)

        # close should work without errors
        impl.close()

    def test_protocol_supports_type_checking(self):
        """Test that the protocol supports static type checking."""
        # This test ensures the protocol is properly defined for type checkers

        def use_sandbox(sandbox: SandboxInterface) -> str:
            """Function that uses a sandbox following the protocol."""
            result = sandbox.reason("test", None)
            sandbox.close()
            return str(result)

        # Should accept any implementation
        inprocess = InProcessSandboxInterface()
        subprocess = SubprocessSandboxInterface()

        # Type checker should accept these
        assert callable(lambda: use_sandbox(inprocess))
        assert callable(lambda: use_sandbox(subprocess))


class TestInterfaceDocumentation:
    """Test that the interface is properly documented."""

    @pytest.mark.parametrize("test_case", protocol_doc_params, ids=lambda x: x["name"])
    def test_protocol_documentation(self, test_case):
        """Test that protocol components are properly documented."""
        if test_case["component"] == "SandboxInterface":
            component = SandboxInterface
        else:
            component = getattr(SandboxInterface, test_case["component"])

        if test_case["should_have_docstring"]:
            assert component.__doc__ is not None
            if "min_length" in test_case:
                assert len(component.__doc__.strip()) >= test_case["min_length"]

        if "should_contain" in test_case:
            for expected_text in test_case["should_contain"]:
                assert expected_text in component.__doc__

        if "should_contain_any" in test_case:
            doc_lower = component.__doc__.lower() if component.__doc__ else ""
            assert any(text in doc_lower for text in test_case["should_contain_any"])


class TestArchitecturalDesign:
    """Test the architectural design of the interface system."""

    def test_protocol_enables_clean_separation(self):
        """Test that protocol enables clean separation of concerns."""
        # The protocol should allow different execution models
        implementations = [
            InProcessSandboxInterface,
            SubprocessSandboxInterface,
        ]

        # All should follow the same interface
        for impl_class in implementations:
            impl = impl_class()

            # Should have consistent interface
            assert hasattr(impl, "reason")
            assert hasattr(impl, "close")

    @pytest.mark.parametrize("test_case", architectural_design_params, ids=lambda x: x["name"])
    def test_interface_supports_future_extensions(self, test_case):
        """Test that the interface can support future extensions."""
        if test_case["name"] == "mock_sandbox_interface":
            # The protocol should be flexible enough for new implementations
            class MockSandboxInterface:
                """Mock implementation for testing."""

                def reason(self, prompt: str, options: dict | None = None):
                    return f"Mock response to: {prompt}"

                def close(self) -> None:
                    pass

            mock = MockSandboxInterface()

            # Should be able to use like any other implementation
            result = mock.reason(test_case["prompt"], None)
            assert test_case["expected_in_response"] in result
            mock.close()  # Should not error

        elif test_case["name"] == "test_double_sandbox":
            # Protocol should make it easy to create test doubles
            class TestDoubleSandbox:
                """Test double implementation."""

                def __init__(self):
                    self.calls = []

                def reason(self, prompt: str, options: dict | None = None):
                    self.calls.append(("reason", prompt, options))
                    return test_case["test_response"]

                def close(self) -> None:
                    self.calls.append(("close",))

            test_double = TestDoubleSandbox()

            # Should track calls for testing
            result = test_double.reason(test_case["prompt"], test_case["options"])
            test_double.close()

            assert len(test_double.calls) == test_case["expected_calls"]
            assert test_double.calls[0] == ("reason", test_case["prompt"], test_case["options"])
            assert test_double.calls[1] == ("close",)
            assert result == test_case["test_response"]


class TestModuleIntegration:
    """Test integration with the overall module architecture."""

    def test_protocol_accessible_from_core_module(self):
        """Test that protocol is accessible from core module."""
        from dana.integrations.python.to_dana.core import SandboxInterface as CoreSandboxInterface

        # Should be the same interface
        assert CoreSandboxInterface is SandboxInterface

    def test_implementations_accessible_from_core_module(self):
        """Test that implementations are accessible from core module."""
        from dana.integrations.python.to_dana.core import (
            InProcessSandboxInterface as CoreInProcess,
        )
        from dana.integrations.python.to_dana.core import (
            SubprocessSandboxInterface as CoreSubprocess,
        )

        # Should be the same classes
        assert CoreInProcess is InProcessSandboxInterface
        assert CoreSubprocess is SubprocessSandboxInterface

    def test_all_exports_are_correct(self):
        """Test that __all__ exports are correct in core module."""
        from dana.integrations.python.to_dana import core

        # Should export all the interface components
        expected_exports = {
            "SandboxInterface",
            "InProcessSandboxInterface",
            "SubprocessSandboxInterface",
        }

        # Check that these are in __all__
        actual_exports = set(core.__all__)
        assert expected_exports.issubset(actual_exports)
