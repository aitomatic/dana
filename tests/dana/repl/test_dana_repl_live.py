"""Live tests for the DANA REPL."""

from unittest.mock import patch

import pytest

from opendxa.dana.repl.dana_repl_app import DanaREPLApp

# Mark all tests in this file as live tests
pytestmark = [pytest.mark.asyncio, pytest.mark.live]


@pytest.mark.live
async def test_dana_repl_basic():
    """Test basic REPL functionality."""
    # Mock the prompt session to simulate user input
    mock_inputs = ["private:x = 5", "private:y = 10", "private:x + private:y", "exit"]  # Should return 15

    with patch("prompt_toolkit.PromptSession.prompt_async") as mock_prompt:
        mock_prompt.side_effect = mock_inputs

        app = DanaREPLApp()
        await app.run()

        # Verify the inputs were processed
        assert mock_prompt.call_count == len(mock_inputs)


@pytest.mark.live
async def test_dana_repl_multiline():
    """Test multiline input handling."""
    mock_inputs = ["if private:x > 0:", "    print('positive')", "else:", "    print('negative')", "exit"]

    with patch("prompt_toolkit.PromptSession.prompt_async") as mock_prompt:
        mock_prompt.side_effect = mock_inputs

        app = DanaREPLApp()
        await app.run()

        assert mock_prompt.call_count == len(mock_inputs)


@pytest.mark.live
async def test_dana_repl_nlp_commands():
    """Test NLP-related commands."""
    mock_inputs = [
        "##nlp status",  # Check initial status
        "##nlp on",  # Enable NLP
        "##nlp status",  # Verify enabled
        "##nlp test",  # Run NLP test
        "##nlp off",  # Disable NLP
        "##nlp status",  # Verify disabled
        "exit",
    ]

    with patch("prompt_toolkit.PromptSession.prompt_async") as mock_prompt:
        mock_prompt.side_effect = mock_inputs

        app = DanaREPLApp()
        await app.run()

        assert mock_prompt.call_count == len(mock_inputs)


@pytest.mark.live
async def test_dana_repl_nlp_transcoding():
    """Test NLP transcoding functionality."""
    mock_inputs = [
        "##nlp on",
        "calculate 10 + 20",  # Should be transcoded to DANA code
        "add 42 and 17",  # Should be transcoded to DANA code
        "exit",
    ]

    with patch("prompt_toolkit.PromptSession.prompt_async") as mock_prompt:
        mock_prompt.side_effect = mock_inputs

        app = DanaREPLApp()
        await app.run()

        assert mock_prompt.call_count == len(mock_inputs)


@pytest.mark.live
async def test_dana_repl_error_handling():
    """Test error handling in the REPL."""
    mock_inputs = [
        "invalid syntax here",  # Should show error
        "private:x = ",  # Incomplete statement
        "if true:",  # Incomplete block
        "    print('test')",  # Complete the block
        "exit",
    ]

    with patch("prompt_toolkit.PromptSession.prompt_async") as mock_prompt:
        mock_prompt.side_effect = mock_inputs

        app = DanaREPLApp()
        await app.run()

        assert mock_prompt.call_count == len(mock_inputs)


@pytest.mark.live
async def test_dana_repl_interrupt_handling():
    """Test handling of keyboard interrupts."""
    mock_inputs = ["private:x = 5", KeyboardInterrupt(), "exit"]  # Simulate Ctrl+C

    with patch("prompt_toolkit.PromptSession.prompt_async") as mock_prompt:
        mock_prompt.side_effect = mock_inputs

        app = DanaREPLApp()
        await app.run()

        assert mock_prompt.call_count == len(mock_inputs)


@pytest.mark.live
async def test_dana_repl_help_command():
    """Test help command functionality."""
    # Mock the prompt session to simulate user input
    mock_inputs = ["help", "exit"]  # Try help command and exit

    with patch("prompt_toolkit.PromptSession.prompt_async") as mock_prompt:
        mock_prompt.side_effect = mock_inputs

        app = DanaREPLApp()
        await app.run()

        # Verify the inputs were processed
        assert mock_prompt.call_count == len(mock_inputs)


@pytest.mark.live
async def test_dana_repl_simple_assignment():
    """Test simple variable assignment in REPL."""
    # Mock the prompt session to simulate user input
    mock_inputs = ["private:a = 5", "exit"]  # Simple assignment and exit

    with patch("prompt_toolkit.PromptSession.prompt_async") as mock_prompt:
        mock_prompt.side_effect = mock_inputs

        app = DanaREPLApp()
        await app.run()

        # Verify the inputs were processed
        assert mock_prompt.call_count == len(mock_inputs)


if __name__ == "__main__":
    pytest.main(["-m", "live", __file__])
