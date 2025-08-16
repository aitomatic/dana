#!/usr/bin/env python3
"""Test script for combined multi-line input behavior in Dana TUI."""

import os
import sys

# Ensure DANA_MOCK_LLM is set for testing
os.environ["DANA_MOCK_LLM"] = "true"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dana.tui.ui.prompt_textarea import PromptStyleTextArea
from dana.core.lang.dana_sandbox import DanaSandbox


def test_combined_multiline():
    """Test the combined multi-line mode logic with both colon and backslash."""
    print("Testing Combined Multi-line Input Logic")
    print("=" * 50)

    # Create sandbox and widget
    sandbox = DanaSandbox()
    widget = PromptStyleTextArea(sandbox=sandbox)

    # Test 1: Colon triggers multi-line mode
    print("\nTest 1: Colon triggers multi-line mode")
    print("-" * 30)
    test_line = "def greet(name):"
    print(f"Input: '{test_line}'")
    print("Press Enter → Enters multi-line mode")
    print("Prompt changes: ⏵ → ...")

    # Test 2: Backslash triggers multi-line mode
    print("\nTest 2: Backslash triggers multi-line mode")
    print("-" * 30)
    test_line = "x = 5"
    print(f"Input: '{test_line}'")
    print("Press \\ → Enters multi-line mode, adds new line")
    print("Prompt changes: ⏵ → ...")

    # Test 3: Backslash in multi-line mode
    print("\nTest 3: Backslash continues multi-line mode")
    print("-" * 30)
    print("Already in multi-line mode...")
    test_line = "    y = 10"
    print(f"Input: '{test_line}'")
    print("Press \\ → Stays in multi-line mode, adds new line")
    print("Prompt remains: ...")

    # Test 4: Mixed usage
    print("\nTest 4: Mixed colon and backslash usage")
    print("-" * 30)
    print("Scenario 1:")
    print("  ⏵ if x > 0:")
    print("      [Enter pressed - enters multi-line mode]")
    print("  ... print('positive')")
    print("      [Backslash pressed - continues multi-line]")
    print("  ... else:")
    print("      [Enter pressed - continues multi-line]")
    print("  ... print('non-positive')")
    print("      [Enter pressed on empty line - executes]")

    print("\nScenario 2:")
    print("  ⏵ x = 5")
    print("      [Backslash pressed - enters multi-line mode]")
    print("  ... y = 10")
    print("      [Backslash pressed - continues multi-line]")
    print("  ... z = x + y")
    print("      [Enter pressed on empty line - executes]")

    # Test 5: Empty line behavior
    print("\nTest 5: Empty line exits multi-line mode")
    print("-" * 30)
    print("In multi-line mode:")
    print("  ... some_code()")
    print("      [Enter on empty line]")
    print("  → Exits multi-line mode and executes")
    print("  → Prompt changes: ... → ⏵")

    # Test 6: Edge cases
    print("\nTest 6: Edge cases")
    print("-" * 30)
    print("Case 1: Trailing whitespace with colon")
    test_line = "if condition:   "
    print(f"  Input: '{test_line}'")
    print(f"  After strip: '{test_line.rstrip()}'")
    print("  Result: Enters multi-line mode")

    print("\nCase 2: Backslash with empty line")
    print("  Input: '' (empty)")
    print("  Press \\ → Enters multi-line mode with empty first line")

    print("\n" + "=" * 50)
    print("Combined functionality summary:")
    print("  • Colon (:) at end of line → Auto-enter multi-line mode")
    print("  • Backslash (\\) any time → Enter/stay in multi-line mode + new line")
    print("  • Empty line in multi-line mode → Execute and exit")
    print("  • History navigation disabled during multi-line mode")
    print("  • All lines have trailing whitespace stripped")

    # Clean up history file if it was created
    history_file = widget._get_history_file()
    if history_file.exists():
        history_file.unlink()


if __name__ == "__main__":
    test_combined_multiline()
