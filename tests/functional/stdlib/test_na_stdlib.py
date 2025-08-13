"""
Test runner for stdlib .na test files.

Automatically discovers and runs all test_*.na files in this directory.
"""

from pathlib import Path
from typing import Any

import pytest

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext


def get_na_files():
    """Get all .na test files in the current directory."""
    test_dir = Path(__file__).parent
    return list(test_dir.glob("test_*.na"))


class TestStdlib:
    """Test runner for stdlib functionality using .na files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

        # Set up LLM resource for tests that use reason function
        from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
        from dana.core.resource.builtins.llm_resource_instance import LLMResourceInstance
        from dana.core.resource.builtins.llm_resource_type import LLMResourceType

        llm_resource = LLMResourceInstance(LLMResourceType(), LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini"))
        llm_resource.initialize()

        # Enable mock mode for testing
        # LLMResourceInstance wraps LegacyLLMResource directly, no bridge needed
        llm_resource.with_mock_llm_call(True)

        self.context.set_system_llm_resource(llm_resource)

    def run_dana_test_file(self, file_path: str) -> Any:
        """Run a .na test file and return the result."""
        file_path = Path(file_path)
        if not file_path.exists():
            pytest.skip(f"Test file {file_path} not found")

        with open(file_path) as f:
            code = f.read()

        return self.interpreter._eval(code, self.context)

    @pytest.mark.parametrize("na_file", get_na_files())
    def test_stdlib_files(self, na_file: Path):
        """Auto-discover and run all .na test files in the directory."""
        result = self.run_dana_test_file(str(na_file))
        assert result is None  # Test functions handle their own assertions
