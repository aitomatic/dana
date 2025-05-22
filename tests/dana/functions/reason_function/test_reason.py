#!/usr/bin/env python
"""
Test script for the reason function in Dana.

This script tests the reason function directly without the REPL complexity.
"""

import os

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_reason_direct():
    """Test the reason_function directly without REPL."""

    # Create an LLM resource
    llm_resource = LLMResource()

    # Create a context with the LLM resource
    context = SandboxContext()
    context._state = {"system": {"llm_resource": llm_resource}, "local": {}}

    # Get whether to use real LLM or mock
    use_real_llm = os.environ.get("OPENDXA_USE_REAL_LLM", "").lower() == "true"

    # Directly call the reason function, using mock by default
    result = reason_function("what is 2+2?", context, use_mock=not use_real_llm)
    assert result is not None

    # When using mock, we should get some result
    if not use_real_llm:
        # Handle both string and dict responses
        if isinstance(result, str):
            assert "mock" in result.lower() or "4" in result
        else:
            # For dict responses, just check we got something
            assert result is not None


if __name__ == "__main__":
    test_reason_direct()
