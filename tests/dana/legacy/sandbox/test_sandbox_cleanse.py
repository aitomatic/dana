#!/usr/bin/env python
"""
Test script for the SandboxContext.cleanse() method.

This script tests that the cleanse method correctly removes or masks sensitive properties.
"""

from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_sandbox_context_cleanse():
    """Test the SandboxContext.cleanse() method."""
    # Create a context with various types of data
    context = SandboxContext()

    # Add normal data
    context.set_in_scope("normal_string", "This is a normal string", scope="local")
    context.set_in_scope("normal_number", 42, scope="public")
    context.set_in_scope("normal_list", [1, 2, 3], scope="private")

    # Add sensitive data by naming convention
    context.set_in_scope("api_key", "sk_live_1234567890abcdef", scope="local")
    context.set_in_scope("secret_token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", scope="public")
    context.set_in_scope("password", "supersecretpassword", scope="private")
    context.set_in_scope("auth_token", "Bearer abcdef1234567890", scope="system")

    # Add data that looks like credentials based on format
    context.set_in_scope("user_id", "usr_1234567890abcdef", scope="local")
    context.set_in_scope("config", {"api_key": "12345", "endpoint": "api.example.com"}, scope="system")

    # Add LLM resource
    class MockLLMResource:
        def __init__(self):
            self.api_key = "sk_12345"

    context.set_in_scope("llm_resource", MockLLMResource(), scope="system")

    print("Before cleansing:")
    print_scopes(context)

    # Cleanse the context
    sanitized = context.sanitize()

    print("\nAfter cleansing:")
    print_scopes(sanitized)

    # Verify that normal data is preserved
    assert sanitized.get("local:normal_string") == "This is a normal string"
    assert sanitized.get("public:normal_number") == 42

    # Verify that sensitive scopes (private/system) are completely removed
    assert "private" not in sanitized._state
    assert "system" not in sanitized._state

    # Verify that sensitive data in local/public is masked
    api_key_value = sanitized.get("local:api_key")
    assert api_key_value.startswith("sk_l")
    assert api_key_value.endswith("cdef")
    assert "****" in api_key_value

    # Verify JWT token in public is masked
    token_value = sanitized.get("public:secret_token")
    assert "****" in token_value

    # Verify that user_id is masked
    user_id_value = sanitized.get("local:user_id")
    assert "****" in user_id_value

    print("\nAll tests passed!")


def print_scopes(context):
    """Print the contents of each scope in the context."""
    for scope in list(context._state.keys()):
        print(f"{scope}: {context._state[scope]}")


if __name__ == "__main__":
    test_sandbox_context_cleanse()
