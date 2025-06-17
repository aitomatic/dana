"""Pytest fixtures for interpreter tests."""

from unittest.mock import patch

import pytest

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


@pytest.fixture
def mock_sandbox():
    """Fixture to provide a mocked DanaSandbox instance."""
    with patch("opendxa.dana.sandbox.dana_sandbox.DanaSandbox._ensure_initialized") as mock_init:
        sandbox = DanaSandbox()
        yield sandbox
