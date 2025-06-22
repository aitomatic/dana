import os
import tempfile
from pathlib import Path

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox, ExecutionResult


class PoetTestBase:
    def _run_dana_code(self, code: str, sandbox: DanaSandbox) -> "ExecutionResult":
        """Write dana code to a temp file and run it."""
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
