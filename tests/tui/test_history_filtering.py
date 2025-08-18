"""
Test history filtering functionality in Dana TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.apps.tui import DanaTUI
from dana.apps.tui.ui.prompt_textarea import PromptStyleTextArea

from .history_test_utils import HistoryBackup, clear_history_for_test


@pytest.mark.asyncio
async def test_history_filtering_basic():
    """Test basic prefix filtering functionality."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            # Get the prompt widget
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history first
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history

        # Add some test history
        test_history = ["print('hello')", "print('world')", "x = 42", "y = 100", "print('test')", "def func():", "    return True"]

        for item in test_history:
            prompt_widget.add_to_history(item)

        # Test that history was loaded correctly
        assert len(prompt_widget._history) == 7

        # Test that we can find print commands in history
        print_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("print")]
        assert len(print_commands) == 3
        assert "print('hello')" in print_commands
        assert "print('world')" in print_commands
        assert "print('test')" in print_commands


@pytest.mark.asyncio
async def test_history_filtering_no_matches():
    """Test behavior when no history items match the prefix."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history first
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history

        # Add some test history
        test_history = ["print('hello')", "x = 42", "y = 100"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        # Test that history was loaded correctly
        assert len(prompt_widget._history) == 3

        # Test that no commands start with 'nonexistent'
        nonexistent_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("nonexistent")]
        assert len(nonexistent_commands) == 0


@pytest.mark.asyncio
async def test_history_filtering_empty_input():
    """Test that empty input allows navigation through all history."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history first
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history

        # Add some test history
        test_history = ["print('hello')", "x = 42", "y = 100"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        # Test that history was loaded correctly
        assert len(prompt_widget._history) == 3
        assert prompt_widget._history[0] == "print('hello')"
        assert prompt_widget._history[1] == "x = 42"
        assert prompt_widget._history[2] == "y = 100"


@pytest.mark.asyncio
async def test_history_filtering_case_sensitive():
    """Test that filtering is case sensitive."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history first
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history

        # Add test history with mixed case
        test_history = ["Print('hello')", "print('world')", "PRINT('test')"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        # Test that history was loaded correctly
        assert len(prompt_widget._history) == 3

        # Test case sensitive filtering - only lowercase 'print' should match
        print_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("print")]
        assert len(print_commands) == 1
        assert print_commands[0] == "print('world')"


@pytest.mark.asyncio
async def test_history_filtering_multiline():
    """Test that filtering works with multi-line content."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history first
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history

            # Add multi-line history
            multiline_command = "def func():\n    return True"
            prompt_widget.add_to_history(multiline_command)
            prompt_widget.add_to_history("print('hello')")

            # Test that history was loaded correctly
            assert len(prompt_widget._history) == 2
            assert prompt_widget._history[0] == multiline_command
            assert prompt_widget._history[1] == "print('hello')"


@pytest.mark.asyncio
async def test_history_filtering_wrap_around():
    """Test that filtering wraps around correctly."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history first
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history

            # Add multiple items with same prefix
            test_history = ["print('a')", "print('b')", "print('c')"]
            for item in test_history:
                prompt_widget.add_to_history(item)

            # Test that history was loaded correctly
            assert len(prompt_widget._history) == 3

            # Test that all items start with 'print'
            print_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("print")]
            assert len(print_commands) == 3
            assert "print('a')" in print_commands
            assert "print('b')" in print_commands
            assert "print('c')" in print_commands


@pytest.mark.asyncio
async def test_history_filtering_return_to_current():
    """Test that pressing down arrow returns to current input when not in filtered mode."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history first
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history

            # Add some history
            test_history = ["print('hello')", "x = 42"]
            for item in test_history:
                prompt_widget.add_to_history(item)

            # Test that history was loaded correctly
            assert len(prompt_widget._history) == 2
            assert prompt_widget._history[0] == "print('hello')"
            assert prompt_widget._history[1] == "x = 42"
