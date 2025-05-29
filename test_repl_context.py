#!/usr/bin/env python3
"""Test script for REPL input context tracking."""

from opendxa.dana.exec.repl.input.input_state import InputState
from opendxa.dana.ipv.context_analyzer import CodeContextAnalyzer


def test_repl_context_tracking():
    """Test the enhanced REPL input context tracking."""
    print("Testing REPL input context tracking...")

    # Simulate REPL input history
    state = InputState()
    state.add_to_history("x = 5")
    state.add_to_history("y = 10  # some number")
    state.add_to_history("# integer pls")
    state.add_to_history('a = reason("what is pi?")  # integer pls')

    print("Input history:")
    for i, line in enumerate(state.get_input_history()):
        print(f"  {i}: {line}")

    print()
    print("Input context:")
    print(state.get_input_context())

    # Test context analysis
    print()
    print("Testing context extraction:")
    analyzer = CodeContextAnalyzer()

    # Mock a context with REPL input
    class MockContext:
        def get(self, key):
            if key == "system.__repl_input_context":
                return state.get_input_context()
            return None

    mock_context = MockContext()
    code_context = analyzer.analyze_context(mock_context, "a")

    print("Extracted context:")
    print(f"  Comments: {code_context.comments}")
    print(f"  Inline comments: {code_context.inline_comments}")
    print(f"  Surrounding code: {code_context.surrounding_code}")

    # Verify the expected comment was extracted
    expected_comment = "integer pls"
    if expected_comment in code_context.inline_comments:
        print(f"✅ SUCCESS: Found expected comment '{expected_comment}'")
        return True
    else:
        print(f"❌ FAILED: Expected comment '{expected_comment}' not found")
        return False


if __name__ == "__main__":
    success = test_repl_context_tracking()
    exit(0 if success else 1)
