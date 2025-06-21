"""
End-to-end test: Run a POET-decorated Dana .na file via DanaSandbox

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from pathlib import Path

import pytest

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


@pytest.mark.poet
def test_poet_e2e_na_file(tmp_path):
    """Run the POET E2E Dana example and check the output."""
    na_path = Path("tests/dana/poet/poet_e2e_example.na")
    assert na_path.exists(), f"Dana file not found: {na_path}"

    sandbox = DanaSandbox(debug_mode=True)
    try:
        result = sandbox.run(na_path)

        assert result.success, f"DanaSandbox run failed: {result.error}"
        assert "POET E2E result: 5" in result.output
    finally:
        sandbox._cleanup()
