#!/usr/bin/env python3
"""Debug script to check prompt format."""

from unittest.mock import Mock, patch

from opendxa.dana.ipv.executor import IPVReason


def debug_prompt_format():
    """Debug the prompt format to fix the failing test."""
    ipv_reason = IPVReason()

    context = Mock()
    context.get_assignment_target_type.return_value = float

    captured_prompt = ""

    def capture_llm_call(prompt, *args, **kwargs):
        nonlocal captured_prompt
        captured_prompt = prompt
        return "42.5"

    with patch.object(ipv_reason, "_execute_llm_call", side_effect=capture_llm_call):
        result = ipv_reason.execute("Extract the price", context=context, use_mock=True)

    print("Actual prompt:")
    print(repr(captured_prompt))
    print()
    print("Formatted prompt:")
    print(captured_prompt)
    print()
    print("Checking for expected text:")
    print("Has 'Expected return type:'", "Expected return type: <class 'float'>" in captured_prompt)
    print("Has 'Expected output type:'", "Expected output type: <class 'float'>" in captured_prompt)


if __name__ == "__main__":
    debug_prompt_format()
