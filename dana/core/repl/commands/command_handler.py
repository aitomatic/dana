"""
Command handler for Dana REPL special commands.

This module processes special commands like /help, /debug, /nlp, etc.
"""

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.shortcuts import print_formatted_text

from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme
from dana.core.repl.commands.help_formatter import HelpFormatter
from dana.core.repl.repl import REPL


class CommandHandler(Loggable):
    """Handles special commands in the Dana REPL."""

    def __init__(self, repl: REPL, colors: ColorScheme):
        """Initialize the command handler."""
        super().__init__()
        self.repl = repl
        self.colors = colors
        self.help_formatter = HelpFormatter(self.repl, self.colors)

    async def handle_command(self, line: str) -> tuple[bool, str]:
        """
        Handle special commands and return (is_command, output).

        Args:
            line: The input line to check for commands

        Returns:
            Tuple of (is_command: bool, output: str)
        """
        line_stripped = line.strip()

        # Handle / command (force multiline)
        if line_stripped == "/":
            print_formatted_text(ANSI(self.colors.accent("✅ Forced multiline mode - type your code, end with empty line")))
            return True, "Multiline mode activated"

        # Handle NLP commands
        if line_stripped.startswith("/nlp"):
            return await self._handle_nlp_command(line_stripped)

        # Handle help commands
        if line_stripped in ["help", "?", "/help"]:
            self.help_formatter.show_help()
            return True, "Help displayed"

        return False, ""

    async def _handle_nlp_command(self, command: str) -> tuple[bool, str]:
        """Handle NLP-related commands."""
        parts = command.split()

        if len(parts) == 1 or (len(parts) == 2 and parts[1] == "status"):
            # Show NLP status
            self.help_formatter.show_nlp_status()
            return True, "NLP status displayed"

        elif len(parts) == 2:
            if parts[1] == "on":
                self.repl.set_nlp_mode(True)
                print_formatted_text(ANSI(self.colors.accent("✅ NLP mode enabled")))
                return True, "NLP enabled"

            elif parts[1] == "off":
                self.repl.set_nlp_mode(False)
                print_formatted_text(ANSI(self.colors.error("❌ NLP mode disabled")))
                return True, "NLP disabled"

            elif parts[1] == "test":
                return await self._handle_nlp_test()

        return False, ""

    async def _handle_nlp_test(self) -> tuple[bool, str]:
        """Test the NLP transcoder functionality."""
        if not self.repl.transcoder:
            print_formatted_text(ANSI(self.colors.error("❌ No LLM resource available for transcoding")))
            print_formatted_text(ANSI("  Set up API keys for transcoding:"))
            print_formatted_text(ANSI(f"  {self.colors.accent('- OPENAI_API_KEY, ANTHROPIC_API_KEY, AZURE_OPENAI_API_KEY, etc.')}"))
            return True, "NLP test failed - no LLM"

        # Test with a simple natural language input
        original_mode = self.repl.get_nlp_mode()
        self.repl.set_nlp_mode(True)

        try:
            test_input = "print hello world"
            print_formatted_text(ANSI(f"\n{self.colors.accent(f"➡️ Test input: '{test_input}'")}"))

            # Execute the test
            result = self.repl.execute(test_input)
            print_formatted_text(ANSI(f"{self.colors.bold('Execution result:')}\n{result}"))

        except Exception as e:
            print_formatted_text(ANSI(f"{self.colors.error('Execution failed:')}\n{e}"))
        finally:
            self.repl.set_nlp_mode(original_mode)

        return True, "NLP test completed"
