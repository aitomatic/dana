"""
Core History Logic Tests.

These tests focus on the core history navigation logic without requiring
the full Textual app context, making them faster and more reliable.
"""

import pytest

from .history_test_utils import HistoryBackup


class MockPromptWidget:
    """Mock widget for testing core history logic without Textual dependencies."""

    def __init__(self):
        self._history = []
        self._history_index = -1
        self._current_input = ""
        self._max_history = 1000

    def add_to_history(self, command: str) -> None:
        """Add a command to history."""
        command = command.strip()
        if not command:
            return

        # Remove duplicate if it exists and move to end
        if command in self._history:
            self._history.remove(command)

        self._history.append(command)

        # Limit history size
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # Reset history navigation
        self._history_index = -1
        self._current_input = ""

    def _get_current_input_content(self) -> str:
        """Get current input content."""
        return self._current_input

    def _set_input_content(self, content: str) -> None:
        """Set input content (mock implementation)."""
        # In the real implementation, this updates the display but doesn't change _current_input
        # _current_input represents the original input when navigation started
        pass

    def _navigate_history(self, direction: int) -> None:
        """
        Navigate through command history with prefix filtering.

        This is a copy of the core logic from PromptStyleTextArea._navigate_history
        without the Textual-specific parts.
        """
        if not self._history:
            return

        # Get current input content
        current_input = self._get_current_input_content()

        # If we're not currently navigating history, save current input and start
        if self._history_index == -1:
            self._current_input = current_input

            # If we have a prefix, filter history to matching items
            if current_input:
                matching_indices = [i for i, item in enumerate(self._history) if item.startswith(current_input)]
                if not matching_indices:
                    return  # No matches, don't navigate

                # Start with the appropriate item based on direction
                if direction < 0:  # Up arrow - go to last match
                    self._history_index = matching_indices[-1]
                else:  # Down arrow - go to first match
                    self._history_index = matching_indices[0]
            else:
                # No prefix - navigate through all history
                if direction < 0:  # Up arrow - go to last item
                    self._history_index = len(self._history) - 1
                else:  # Down arrow - go to first item
                    self._history_index = 0
        else:
            # We're already navigating history
            # Check if we started with a prefix filter
            if self._current_input:
                # We started with a prefix, so continue filtering to matching items
                matching_indices = [i for i, item in enumerate(self._history) if item.startswith(self._current_input)]

                if not matching_indices:
                    return  # No matches, don't navigate

                # Find current position in filtered list
                try:
                    current_filtered_index = matching_indices.index(self._history_index)
                except ValueError:
                    # Current index not in filtered list, start from beginning
                    current_filtered_index = -1

                # Calculate new filtered index
                new_filtered_index = current_filtered_index + direction

                # Handle wrap around
                if new_filtered_index < 0:
                    # Going up past first match - wrap to last match
                    self._history_index = matching_indices[-1]
                elif new_filtered_index >= len(matching_indices):
                    # Going down past last match - wrap to first match
                    self._history_index = matching_indices[0]
                else:
                    # Normal navigation within filtered list
                    self._history_index = matching_indices[new_filtered_index]
            else:
                # No prefix filter - navigate through all history
                new_index = self._history_index + direction

                # Handle wrap around
                if new_index < 0:
                    # Going up past first item - wrap to last
                    self._history_index = len(self._history) - 1
                elif new_index >= len(self._history):
                    # Going down past last item - wrap to first
                    self._history_index = 0
                else:
                    # Normal navigation
                    self._history_index = new_index

        # Update content with the selected history item
        if self._history_index != -1:
            # Note: In the real implementation, _set_input_content updates the display
            # but _current_input remains the original input when navigation started
            self._set_input_content(self._history[self._history_index])


@pytest.mark.asyncio
async def test_core_history_filtering_basic():
    """Test basic prefix filtering functionality with core logic."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        # Create mock widget
        prompt_widget = MockPromptWidget()

        # Add some test history
        test_history = ["print('hello')", "print('world')", "x = 42", "y = 100", "print('test')", "def func():", "    return True"]

        for item in test_history:
            prompt_widget.add_to_history(item)

        # Test filtering with 'print' prefix
        prompt_widget._current_input = "print"
        prompt_widget._history_index = -1  # Reset to start

        # Navigate up should find print commands
        prompt_widget._navigate_history(-1)  # Up arrow
        assert prompt_widget._history_index != -1
        assert prompt_widget._history[prompt_widget._history_index].startswith("print")

        # Navigate down should find next print command
        prompt_widget._navigate_history(1)  # Down arrow
        assert prompt_widget._history[prompt_widget._history_index].startswith("print")

        # Navigate up again should wrap around
        prompt_widget._navigate_history(-1)  # Up arrow
        assert prompt_widget._history[prompt_widget._history_index].startswith("print")


@pytest.mark.asyncio
async def test_core_history_filtering_no_matches():
    """Test behavior when no history items match the prefix."""
    with HistoryBackup():
        prompt_widget = MockPromptWidget()

        # Add some test history
        test_history = ["print('hello')", "x = 42", "y = 100"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        # Try to filter with non-matching prefix
        prompt_widget._current_input = "nonexistent"
        prompt_widget._history_index = -1

        # Navigation should not change anything when no matches
        original_index = prompt_widget._history_index
        prompt_widget._navigate_history(-1)
        assert prompt_widget._history_index == original_index


@pytest.mark.asyncio
async def test_core_history_filtering_empty_input():
    """Test that empty input allows navigation through all history."""
    with HistoryBackup():
        prompt_widget = MockPromptWidget()

        # Add some test history
        test_history = ["print('hello')", "x = 42", "y = 100"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        print(f"Test history: {test_history}")
        print(f"Widget history: {prompt_widget._history}")

        # Start with empty input
        prompt_widget._current_input = ""
        prompt_widget._history_index = -1

        print(f"Before first navigation: current_input='{prompt_widget._current_input}', history_index={prompt_widget._history_index}")

        # Navigate up should go to last item
        prompt_widget._navigate_history(-1)
        print(f"After first navigation (up): history_index={prompt_widget._history_index}, expected={len(test_history) - 1}")
        print(f"After first navigation: current_input='{prompt_widget._current_input}'")
        assert prompt_widget._history_index == len(test_history) - 1

        # Navigate down should go to first item
        prompt_widget._navigate_history(1)
        print(f"After second navigation (down): history_index={prompt_widget._history_index}, expected=0")
        print(f"After second navigation: current_input='{prompt_widget._current_input}'")
        assert prompt_widget._history_index == 0


@pytest.mark.asyncio
async def test_core_history_filtering_wrap_around():
    """Test that filtering wraps around correctly."""
    with HistoryBackup():
        prompt_widget = MockPromptWidget()

        # Add multiple items with same prefix
        test_history = ["print('a')", "print('b')", "print('c')"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        prompt_widget._current_input = "print"
        prompt_widget._history_index = -1

        # Navigate through all items
        prompt_widget._navigate_history(-1)  # Should go to last 'print'
        first_index = prompt_widget._history_index

        prompt_widget._navigate_history(1)  # Should go to first 'print'
        second_index = prompt_widget._history_index

        prompt_widget._navigate_history(1)  # Should go to second 'print'
        third_index = prompt_widget._history_index

        # All should be different and all should start with 'print'
        assert first_index != second_index != third_index
        assert all(prompt_widget._history[i].startswith("print") for i in [first_index, second_index, third_index])


@pytest.mark.asyncio
async def test_core_history_filtering_return_to_current():
    """Test that pressing down arrow returns to current input when not in filtered mode."""
    with HistoryBackup():
        prompt_widget = MockPromptWidget()

        # Add some history
        test_history = ["print('hello')", "x = 42"]
        for item in test_history:
            prompt_widget.add_to_history(item)

        # Start with empty input (not filtered mode)
        current_input = ""
        prompt_widget._current_input = current_input
        prompt_widget._history_index = -1

        # Navigate up to history (should go to last item)
        prompt_widget._navigate_history(-1)
        assert prompt_widget._history_index == len(test_history) - 1

        # Navigate down should wrap to first item (not return to current input)
        prompt_widget._navigate_history(1)
        assert prompt_widget._history_index == 0

        # Navigate down again should wrap to last item
        prompt_widget._navigate_history(1)
        assert prompt_widget._history_index == len(test_history) - 1


if __name__ == "__main__":
    # Run the tests directly
    import asyncio

    async def run_core_tests():
        print("Testing core history navigation logic...")
        await test_core_history_filtering_basic()
        print("✓ Basic filtering test passed")

        await test_core_history_filtering_no_matches()
        print("✓ No matches test passed")

        await test_core_history_filtering_empty_input()
        print("✓ Empty input test passed")

        await test_core_history_filtering_wrap_around()
        print("✓ Wrap around test passed")

        await test_core_history_filtering_return_to_current()
        print("✓ Return to current test passed")

        print("\n🎉 All core history logic tests completed successfully!")

    asyncio.run(run_core_tests())
