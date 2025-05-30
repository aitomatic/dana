#!/usr/bin/env python3
"""Test script for IPV integration with REPL input context."""

from opendxa.dana.exec.repl.input.input_state import InputState
from opendxa.dana.ipv.executor import IPVReason


def test_ipv_with_repl_context():
    """Test that IPV properly receives and uses REPL input context."""
    print("Testing IPV integration with REPL input context...")

    # Simulate REPL input history
    state = InputState()
    state.add_to_history("x = 5")
    state.add_to_history("y = 10  # some number")
    state.add_to_history("# integer pls")
    state.add_to_history('a = reason("what is pi?")  # integer pls')

    # Mock a context that provides both REPL input and assignment type
    class MockContext:
        def get(self, key):
            if key == "system.__repl_input_context":
                return state.get_input_context()
            elif key == "system.__current_assignment_type":
                return None  # No explicit type annotation
            return None

        def get_assignment_target_type(self):
            return None  # No explicit type annotation - IPV should infer from comments

        def hasattr(self, attr):
            return attr == "get_assignment_target_type"

    mock_context = MockContext()

    # Test IPV reasoning with REPL context
    print()
    print("Testing IPV INFER phase with REPL context:")

    reasoner = IPVReason()
    reasoner.set_debug_mode(True)

    # Test the INFER phase to see if it picks up the context
    enhanced_context = reasoner.infer_phase("what is pi?", mock_context, variable_name="a")

    print()
    print("Enhanced context from INFER phase:")
    print(f"  Expected type: {enhanced_context.get('expected_type')}")
    print(f"  Code context available: {enhanced_context.get('code_context') is not None}")

    if enhanced_context.get("code_context"):
        code_ctx = enhanced_context["code_context"]
        print(f"  Comments: {code_ctx.comments}")
        print(f"  Inline comments: {code_ctx.inline_comments}")

        # Check if we found the "integer pls" hint
        has_integer_hint = any("integer" in comment.lower() for comment in code_ctx.comments + code_ctx.inline_comments)

        if has_integer_hint:
            print("✅ SUCCESS: Found 'integer' hint in comments")

            # Test the PROCESS phase to see if LLM gets the context
            print()
            print("Testing PROCESS phase with context:")

            # Use mock LLM to see the enhanced prompt
            result = reasoner.process_phase("what is pi?", enhanced_context, context=mock_context, use_mock=True)
            print(f"Mock LLM result: {result}")

            return True
        else:
            print("❌ FAILED: 'integer' hint not found in context")
            return False
    else:
        print("❌ FAILED: No code context extracted")
        return False


if __name__ == "__main__":
    success = test_ipv_with_repl_context()
    exit(0 if success else 1)
