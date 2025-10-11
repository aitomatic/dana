"""
Regression tests for Adana REPL app.

Tests basic functionality of the REPL application without network access.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from adana.apps.repl.repl_app import AdanaREPLApp


class TestREPLAppInitialization:
    """Test REPL app initialization."""

    def test_repl_app_creation(self):
        """Test that REPL app can be created without errors."""
        # Handle Windows console issues in CI/CD environments
        if sys.platform == "win32":
            # Set environment variables to avoid console issues in CI/CD
            original_term = os.environ.get("TERM")
            original_wt_session = os.environ.get("WT_SESSION")

            # Simulate CI/CD environment that might cause console issues
            if not os.environ.get("WT_SESSION"):
                os.environ["TERM"] = "xterm-256color"

        try:
            app = AdanaREPLApp()
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
    @patch("adana.apps.repl.repl_app.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("adana.apps.repl.repl_app.FileHistory")
    @patch("adana.apps.repl.repl_app.PromptSession")
    @patch("adana.apps.repl.repl_app.PygmentsLexer")
    @patch("adana.apps.repl.repl_app.PythonLexer")
    def test_repl_app_with_prompt_toolkit(self, mock_python_lexer, mock_pygments_lexer, mock_prompt_session, mock_file_history):
        """Test REPL app initialization with prompt_toolkit available."""
        # Mock the imports to return mock objects
        mock_file_history.return_value = Mock()
        mock_prompt_session.return_value = Mock()
        mock_pygments_lexer.return_value = Mock()
        mock_python_lexer.return_value = Mock()

        app = AdanaREPLApp()
        assert hasattr(app, "session")
        assert hasattr(app, "history")

    def test_repl_app_history_file_creation(self):
        """Test that history file location is set correctly."""
        app = AdanaREPLApp()
        if hasattr(app, "history"):
            # History should be FileHistory pointing to ~/.adana/repl_history.txt
            history_path = Path.home() / ".adana" / "repl_history.txt"
            assert history_path.parent.exists()

    def test_repl_app_namespace_imports(self):
        """Test that REPL namespace has expected imports."""
        app = AdanaREPLApp()

        # Check for key imports
        expected_imports = [
            "STARAgent",
            "BaseAgent",
            "BaseSTARAgent",
            "BaseWorkflow",
            "BaseResource",
        ]

        for import_name in expected_imports:
            assert import_name in app.namespace, f"Expected import '{import_name}' not found in namespace"


class TestREPLAppCommands:
    """Test REPL app command handling."""

    def test_help_command(self, capsys):
        """Test /help command."""
        app = AdanaREPLApp()
        result = app._handle_command("/help")

        assert result is True
        captured = capsys.readouterr()
        assert "Available commands:" in captured.out or "help" in captured.out.lower()

    def test_exit_command(self):
        """Test /exit command."""
        app = AdanaREPLApp()
        result = app._handle_command("/exit")
        assert result is False  # Exit should return False to stop loop

    def test_quit_command(self):
        """Test /quit command."""
        app = AdanaREPLApp()
        result = app._handle_command("/quit")
        assert result is False  # Quit should return False to stop loop

    def test_invalid_command(self, capsys):
        """Test handling of invalid command."""
        app = AdanaREPLApp()
        result = app._handle_command("/invalid_command")

        # Should handle gracefully
        assert result is True  # Should continue even on invalid command


class TestREPLAppExecution:
    """Test REPL app code execution."""

    def test_execute_simple_expression(self, capsys):
        """Test executing a simple Python expression."""
        app = AdanaREPLApp()
        app._execute("2 + 2")

        captured = capsys.readouterr()
        assert "4" in captured.out

    def test_execute_variable_assignment(self):
        """Test executing variable assignment."""
        app = AdanaREPLApp()
        app._execute("x = 42")
        app._execute("x")

        # Variable should be in namespace
        assert app.namespace.get("x") == 42

    def test_execute_import_statement(self):
        """Test executing import statement."""
        app = AdanaREPLApp()
        app._execute("import math")

        assert "math" in app.namespace

    def test_execute_multiline_code(self):
        """Test executing multiline code."""
        app = AdanaREPLApp()
        code = """
def test_func():
    return "hello"
result = test_func()
"""
        app._execute(code)
        assert app.namespace.get("result") == "hello"

    def test_execute_with_syntax_error(self, capsys):
        """Test handling of syntax errors."""
        app = AdanaREPLApp()
        app._execute("def invalid syntax")

        captured = capsys.readouterr()
        # Should show error without crashing
        assert "SyntaxError" in captured.out or "error" in captured.out.lower()

    def test_execute_with_runtime_error(self, capsys):
        """Test handling of runtime errors."""
        app = AdanaREPLApp()
        app._execute("1 / 0")

        captured = capsys.readouterr()
        # Should show error without crashing
        # Error output may go to stdout or stderr, check both
        all_output = captured.out + captured.err
        assert "ZeroDivisionError" in all_output or "Traceback" in all_output


class TestREPLAppNamespace:
    """Test REPL app namespace management."""

    def test_namespace_persistence(self):
        """Test that namespace persists across executions."""
        app = AdanaREPLApp()

        # Set a variable
        app._execute("x = 10")
        assert app.namespace.get("x") == 10

        # Use it in another execution
        app._execute("y = x + 5")
        assert app.namespace.get("y") == 15

    def test_namespace_has_builtins(self):
        """Test that namespace includes Python builtins."""
        app = AdanaREPLApp()

        # Check for common builtins via __builtins__
        builtins_dict = app.namespace.get("__builtins__")
        if isinstance(builtins_dict, dict):
            assert "print" in builtins_dict
            assert "len" in builtins_dict
            assert "str" in builtins_dict
            assert "int" in builtins_dict
        else:
            # __builtins__ might be a module
            assert hasattr(builtins_dict, "print")
            assert hasattr(builtins_dict, "len")
            assert hasattr(builtins_dict, "str")
            assert hasattr(builtins_dict, "int")

    def test_namespace_preimported_classes(self):
        """Test that expected Adana classes are pre-imported."""
        app = AdanaREPLApp()

        # Check for Adana framework classes
        from adana.core.agent.base_agent import BaseAgent
        from adana.core.agent.star_agent import STARAgent

        assert app.namespace.get("STARAgent") is STARAgent
        assert app.namespace.get("BaseAgent") is BaseAgent


class TestREPLAppRegression:
    """Regression tests for known issues."""

    def test_repl_app_does_not_crash_on_empty_input(self):
        """Regression: REPL should handle empty input gracefully."""
        app = AdanaREPLApp()
        # Should not crash
        app._execute("")
        app._execute("   ")
        app._execute("\n")

    def test_repl_app_handles_none_result(self, capsys):
        """Regression: REPL should handle None results properly."""
        app = AdanaREPLApp()
        app._execute("None")

        # Should not print anything for None
        # (This is standard Python REPL behavior)

    def test_repl_app_handles_unicode(self):
        """Regression: REPL should handle unicode characters."""
        app = AdanaREPLApp()
        app._execute('message = "Hello 世界 🌍"')

        assert app.namespace.get("message") == "Hello 世界 🌍"

    def test_repl_app_works_without_prompt_toolkit(self):
        """Regression: REPL should work even without prompt_toolkit."""
        # Mock PROMPT_TOOLKIT_AVAILABLE before importing
        with patch("adana.apps.repl.repl_app.PROMPT_TOOLKIT_AVAILABLE", False):
            # Need to reload or create a new app with patched value
            app = AdanaREPLApp()
            # Should still create app successfully
            assert app is not None
            # Session should be None when prompt_toolkit is not available
            assert app.session is None
            assert app.history is None

    def test_repl_app_namespace_cleanup(self):
        """Regression: Variables from previous executions should persist correctly."""
        app = AdanaREPLApp()

        app._execute("temp_var = 123")
        assert "temp_var" in app.namespace

        # Overwrite variable
        app._execute("temp_var = 456")
        assert app.namespace.get("temp_var") == 456

        # Delete variable
        app._execute("del temp_var")
        assert "temp_var" not in app.namespace
