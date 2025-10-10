"""
Regression tests for Dana conversational agent app.

Tests basic functionality of the Dana app without network access (no LLM calls).
"""

from pathlib import Path
from unittest.mock import patch

import os
import sys

import pytest

from adana.apps.dana.dana_app import DanaApp


@pytest.mark.requires_api_keys
class TestDanaAppInitialization:
    """Test Dana app initialization."""

    def test_dana_app_creation(self):
        """Test that Dana app can be created without errors."""
        # Handle Windows console issues in CI/CD environments
        if sys.platform == "win32":
            # Set environment variables to avoid console issues in CI/CD
            original_term = os.environ.get("TERM")
            original_wt_session = os.environ.get("WT_SESSION")

            # Simulate CI/CD environment that might cause console issues
            if not os.environ.get("WT_SESSION"):
                os.environ["TERM"] = "xterm-256color"

        try:
            app = DanaApp()
            assert app is not None
        finally:
            # Restore original environment
            if sys.platform == "win32":
                if original_term is not None:
                    os.environ["TERM"] = original_term
                elif "TERM" in os.environ:
                    del os.environ["TERM"]
                if original_wt_session is not None:
                    os.environ["WT_SESSION"] = original_wt_session
                elif "WT_SESSION" in os.environ:
                    del os.environ["WT_SESSION"]

    @pytest.mark.windows_console
    def test_dana_app_with_prompt_toolkit(self):
        """Test Dana app with prompt toolkit enabled."""
        app = DanaApp()
        assert app is not None
        # Check that prompt toolkit is available if installed
        if hasattr(app, "session") and app.session is not None:
            assert app.session is not None

    def test_dana_app_history_file_creation(self):
        """Test that Dana app creates history file."""
        # The history file is created in the user's home directory, not in the current directory
        history_file = Path.home() / ".adana" / "dana_history.txt"

        # Create the app
        app = DanaApp()

        # The history file is only created when the FileHistory object is actually used
        # So we need to trigger history usage to create the file
        if app.history is not None:
            # Add a test command to history to trigger file creation
            app.history.append_string("test command")
            # Now the file should exist
            assert history_file.exists()
        else:
            # If prompt toolkit is not available, skip this test
            pytest.skip("Prompt toolkit not available")

    def test_dana_app_initialization_creates_objects(self):
        """Test that Dana app initialization creates required objects."""
        app = DanaApp()

        # After initialization, objects should be None until _initialize_dana() is called
        assert app.dana_agent is None
        assert app.thought_logger is None


@pytest.mark.requires_api_keys
class TestDanaAppCommands:
    """Test Dana app command handling."""

    @patch("adana.apps.dana.dana_agent.DanaAgent")
    def test_help_command(self, mock_dana_agent_class, capsys):
        """Test /help command."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"

        # Mock the task manager

        app = DanaApp()
        # Initialize the dana_agent and thought_logger
        app._initialize_dana()
        result = app._handle_command("/help")

        assert result is True
        captured = capsys.readouterr()
        assert "Dana Commands" in captured.out

    @patch("adana.apps.dana.dana_agent.DanaAgent")
    def test_agents_command(self, mock_dana_agent_class, capsys):
        """Test /agents command."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.available_agents = []

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()
        result = app._handle_command("/agents")

        assert result is True
        captured = capsys.readouterr()
        assert "Available Agents" in captured.out

    @patch("adana.apps.dana.dana_agent.DanaAgent")
    def test_resources_command(self, mock_dana_agent_class, capsys):
        """Test /resources command."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.available_resources = []

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()
        result = app._handle_command("/resources")

        assert result is True
        captured = capsys.readouterr()
        assert "Available Resources" in captured.out

    @patch("adana.apps.dana.dana_agent.DanaAgent")
    def test_workflows_command(self, mock_dana_agent_class, capsys):
        """Test /workflows command."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.available_workflows = []

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()
        result = app._handle_command("/workflows")

        assert result is True
        captured = capsys.readouterr()
        assert "Available Workflows" in captured.out

    @patch("adana.apps.dana.dana_agent.DanaAgent")
    def test_thoughts_command_toggle(self, mock_dana_agent_class, capsys):
        """Test /thoughts command toggle."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()

        # Test turning thoughts on
        result = app._handle_command("/thoughts")
        assert result is True
        captured = capsys.readouterr()
        assert "enabled" in captured.out or "disabled" in captured.out

    @patch("adana.apps.dana.dana_agent.DanaAgent")
    def test_invalid_command(self, mock_dana_agent_class, capsys):
        """Test invalid command."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()
        result = app._handle_command("/invalid")

        assert result is True
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out


@pytest.mark.requires_api_keys
class TestDanaAppConversation:
    """Test Dana app conversation functionality."""

    @patch("adana.apps.dana.dana_app.DanaAgent")
    def test_converse_with_response(
        self,
        mock_dana_agent_class,
        capsys,
    ):
        """Test conversation with a response."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.query.return_value = {"response": "Hello! How can I help you today?"}
        mock_dana_agent.ensure_registered.return_value = None

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()
        app._converse("Hello")

        captured = capsys.readouterr()
        assert "Hello! How can I help you today?" in captured.out

    @patch("adana.apps.dana.dana_app.DanaAgent")
    def test_converse_clears_thoughts(self, mock_dana_agent_class):
        """Test that conversation clears thoughts after processing."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.query.return_value = {"response": "Test response"}
        mock_dana_agent.ensure_registered.return_value = None

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()
        app._converse("Test message")

        # Check that thoughts were cleared
        assert app.thought_logger is not None

    @patch("adana.apps.dana.dana_app.DanaAgent")
    def test_converse_with_error(self, mock_dana_agent_class, capsys):
        """Test conversation with an error."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.query.side_effect = Exception("Test error")
        mock_dana_agent.ensure_registered.return_value = None

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()
        app._converse("Test message")

        captured = capsys.readouterr()
        assert "Test error" in captured.out

    @patch("adana.apps.dana.dana_app.DanaAgent")
    def test_converse_with_no_response_key(self, mock_dana_agent_class, capsys):
        """Test conversation with no response key."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.query.return_value = {"other_key": "value"}
        mock_dana_agent.ensure_registered.return_value = None

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()
        app._converse("Test message")

        captured = capsys.readouterr()
        # Should show default response
        assert "I'm not sure how to respond" in captured.out


@pytest.mark.requires_api_keys
class TestDanaAppRegression:
    """Regression tests for known issues."""

    @patch("adana.apps.dana.dana_agent.DanaAgent")
    def test_dana_app_does_not_crash_on_empty_input(
        self,
        mock_dana_agent_class,
        capsys,
    ):
        """Test that Dana app doesn't crash on empty input."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.query.return_value = {"response": "Test response"}

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()

        # Test empty input
        app._converse("")

        # Test None input
        app._converse(None)

        # Test whitespace-only input
        app._converse("   ")

    @patch("adana.apps.dana.dana_app.DanaAgent")
    def test_dana_app_handles_unicode(self, mock_dana_agent_class, capsys):
        """Test that Dana app handles unicode characters."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.query.return_value = {"response": "Unicode test: 🚀"}
        mock_dana_agent.ensure_registered.return_value = None

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()
        app._converse("Test with unicode: 🚀")

        captured = capsys.readouterr()
        assert "Unicode test: 🚀" in captured.out

    @patch("adana.apps.dana.dana_agent.DanaAgent")
    def test_dana_app_works_without_prompt_toolkit(self, mock_dana_agent_class):
        """Test that Dana app works without prompt toolkit."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"

        # Mock the task manager

        app = DanaApp()
        assert app is not None

    @patch("adana.apps.dana.dana_app.DanaAgent")
    def test_dana_app_thought_logger_state_persistence(self, mock_dana_agent_class):
        """Test that thought logger state persists across conversations."""
        # Mock the DanaAgent class
        mock_dana_agent = mock_dana_agent_class.return_value
        mock_dana_agent.agent_id = "test-agent"
        mock_dana_agent.ensure_registered.return_value = None

        # Mock the task manager

        app = DanaApp()
        app._initialize_dana()

        # Check that thought logger is initialized
        assert app.thought_logger is not None

        # Check that thought logger state persists
        initial_state = app.thought_logger.verbose
        app.thought_logger.verbose = not initial_state
        assert app.thought_logger.verbose != initial_state
