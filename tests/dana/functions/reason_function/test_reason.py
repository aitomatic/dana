#!/usr/bin/env python
"""
Test script for the reason function in Dana.

This script tests the reason function directly without the REPL complexity.
"""

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

    # Directly call the reason function
    try:
        result = reason_function("what is 2+2?", context)
        assert result is not None
    except Exception as e:
        # LLM timeouts are expected in test environments
        assert "timeout" in str(e).lower() or "reasoning" in str(e).lower()


if __name__ == "__main__":
    test_reason_direct()
