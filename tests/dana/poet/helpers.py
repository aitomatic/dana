import os
import tempfile
from pathlib import Path

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox, ExecutionResult


class PoetTestBase:
    sandbox: DanaSandbox

    def setup_method(self):
        """Setup for each test"""
        self.sandbox = DanaSandbox()

    def teardown_method(self):
        """Cleanup after each test"""
        if hasattr(self, "sandbox"):
            self.sandbox._cleanup()

    def _run_dana_code(self, code: str) -> "ExecutionResult":
        """Write dana code to a temp file and run it."""
        temp_dir = Path("tmp/poet_tests")
        temp_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".na", dir=temp_dir, delete=False) as f:
            f.write(code)
            filepath = f.name

        try:
            execution_result = self.sandbox.run(filepath)
        finally:
            os.unlink(filepath)

        return execution_result
