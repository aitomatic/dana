import os
import tempfile
from pathlib import Path

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox, ExecutionResult


class PoetTestBase:
    def setup_method(self):
        """Setup for each test method"""
        # Create sandbox for Dana execution
        self.sandbox = DanaSandbox()

    def teardown_method(self):
        """Cleanup after each test method"""
        # Clean up sandbox
        if hasattr(self, "sandbox"):
            self.sandbox._cleanup()

    def _run_dana_code(self, code: str, sandbox: DanaSandbox | None = None) -> "ExecutionResult":
        """Write dana code to a temp file and run it."""
        if sandbox is None:
            sandbox = self.sandbox

        temp_dir = Path("tmp/poet_tests")
        temp_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".na", dir=temp_dir, delete=False) as f:
            f.write(code)
            filepath = f.name

        try:
            execution_result = sandbox.run(filepath)
        finally:
            os.unlink(filepath)

        return execution_result
