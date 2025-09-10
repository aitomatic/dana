"""
Comprehensive test suite for PipelineExpression functionality.

This module provides comprehensive testing for the new PipelineExpression feature
including implicit first-argument mode, explicit placeholder mode, and edge cases.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from pathlib import Path

import pytest

from dana.core.lang.dana_sandbox import DanaSandbox


def get_na_files():
    """Get all .na files in the current directory."""
    return list(Path(__file__).parent.glob("test_*.na"))


@pytest.mark.parametrize("na_file", get_na_files())
def test_pipeline_files(na_file):
    """Test pipeline execution from .na files."""
    sandbox = DanaSandbox(debug_mode=True)
    with open(na_file) as f:
        code = f.read()
    result = sandbox.execute_string(code)
    assert result.success, f"Test file {na_file} failed: {result.error}"
