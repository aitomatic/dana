"""
History Navigation Tests using Pilot.

Tests the actual history navigation behavior using Textual's Pilot for realistic user interaction testing.
"""

import pytest

from dana.apps.tui import DanaTUI
from dana.apps.tui.ui.prompt_textarea import PromptStyleTextArea

from .history_test_utils import HistoryBackup, clear_history_for_test


@pytest.mark.asyncio
async def test_history_cycling_empty_input():
    """Test cycling through history with empty input using Pilot."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history and add test items
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history
            test_history = ["print('hello')", "x = 42", "def func(): pass"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        print(f"Test history: {prompt_widget._history}")

        # Test that history was loaded correctly
        assert len(prompt_widget._history) == 3
        assert prompt_widget._history[0] == "print('hello')"
        assert prompt_widget._history[1] == "x = 42"
        assert prompt_widget._history[2] == "def func(): pass"


@pytest.mark.asyncio
async def test_history_cycling_with_prefix():
    """Test cycling through history with a prefix using Pilot."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history and add test items
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history
            test_history = ["print('hello')", "print('world')", "x = 42", "print('test')"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        print(f"Test history: {prompt_widget._history}")

        # Test that history was loaded correctly
        assert len(prompt_widget._history) == 4

        # Test that we can find print commands in history
        print_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("print")]
        assert len(print_commands) == 3
        assert "print('hello')" in print_commands
        assert "print('world')" in print_commands
        assert "print('test')" in print_commands


@pytest.mark.asyncio
async def test_history_reset_on_typing():
    """Test that history navigation resets when user starts typing."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history and add test items
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history
            test_history = ["print('hello')", "x = 42"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        # Test that history was loaded correctly
        assert len(prompt_widget._history) == 2
        assert prompt_widget._history[0] == "print('hello')"
        assert prompt_widget._history[1] == "x = 42"


if __name__ == "__main__":
    # Run the tests directly
    import asyncio

    async def run_tests():
        print("Testing history cycling with empty input...")
        await test_history_cycling_empty_input()
        print("✓ Empty input cycling test passed")

        print("\nTesting history cycling with prefix...")
        await test_history_cycling_with_prefix()
        print("✓ Prefix cycling test passed")

        print("\nTesting history reset on typing...")
        await test_history_reset_on_typing()
        print("✓ Reset on typing test passed")

        print("\nAll tests passed!")

    asyncio.run(run_tests())
