#!/usr/bin/env python3
"""
Test the reason function directly.
"""


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

    print(f"Type of prompt: {type(prompt)}")
    print(f"Prompt: {prompt}")

    try:
        # Call the reason function directly
        result = reason_function(prompt, context)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_reason()
