#!/usr/bin/env python3
"""
Test the reason function directly.
"""

import os

import pytest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_reason():
    """Test the reason function directly."""
    # Create a context with an LLM resource
    context = SandboxContext()
    llm_resource = LLMResource()
    context.set("system.llm_resource", llm_resource)

    # Try with a simple string prompt
    prompt = "What is 2+2? Reply with just the number."

    # Get whether to use real LLM or mock
    use_real_llm = os.environ.get("OPENDXA_USE_REAL_LLM", "").lower() == "true"

    try:
        # Call the reason function directly, using mock by default
        result = reason_function(prompt, context, use_mock=not use_real_llm)
        print(f"Result: {result}")
        # Basic assertion to verify we got a result
        assert result is not None
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
