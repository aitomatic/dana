"""
Command handler for Dana REPL special commands.

This module processes special commands like /help, /debug, /nlp, etc.
"""

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.shortcuts import print_formatted_text

from dana.apps.repl.commands.help_formatter import HelpFormatter
from dana.apps.repl.repl import REPL
from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme


class CommandHandler(Loggable):
    """Handles special commands in the Dana REPL."""

    def __init__(self, repl: REPL, colors: ColorScheme, prompt_manager=None):
        """Initialize the command handler."""
        super().__init__()
        self.repl = repl
        self.colors = colors
        self.help_formatter = HelpFormatter(self.repl, self.colors)
        self.prompt_manager = prompt_manager

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

        # Handle status command
        if line_stripped in ["/status", "status"]:
            return await self._handle_status_command()

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

    async def _handle_status_command(self) -> tuple[bool, str]:
        """Handle the /status command to show current REPL status."""
        if self.prompt_manager and hasattr(self.prompt_manager, "status_display"):
            print_formatted_text(ANSI(f"\n{self.colors.bold('Current Dana REPL Status:')}"))

            # Get context information
            status_display = self.prompt_manager.status_display
            context_info = status_display.get_context_info()

            # Count variables in different scopes
            var_details = []
            try:
                context = self.repl.context
                for scope in ["private", "public", "local", "system"]:
                    scope_vars = context._state.get(scope, {})
                    scope_count = 0
                    for var_name in scope_vars.keys():
                        if not var_name.startswith("_"):  # Skip internal variables
                            scope_count += 1
                    if scope_count > 0:
                        var_details.append(f"{scope}: {scope_count}")
            except Exception:
                var_details = ["Unable to read context"]

            # Display status information
            print_formatted_text(ANSI(f"  {self.colors.accent('Context:')} {context_info}"))
            print_formatted_text(ANSI(f"  {self.colors.accent('Variable breakdown:')} {', '.join(var_details) if var_details else 'None'}"))

            # Show NLP status
            nlp_status = "enabled" if self.repl.get_nlp_mode() else "disabled"
            print_formatted_text(ANSI(f"  {self.colors.accent('NLP mode:')} {nlp_status}"))

            # Show available core functions count
            try:
                registry = self.repl.interpreter.function_registry
                core_functions = registry.list_functions("system") or []
                print_formatted_text(ANSI(f"  {self.colors.accent('Core functions:')} {len(core_functions)} available"))
            except Exception:
                print_formatted_text(ANSI(f"  {self.colors.accent('Core functions:')} Unable to count"))

            print_formatted_text(
                ANSI(f"\n{self.colors.dim('💡 Tip: The status bar can be shown at the bottom with appropriate terminal support')}")
            )

            return True, "Status displayed"
        else:
            print_formatted_text(ANSI(self.colors.error("❌ Status display not available")))
            return True, "Status unavailable"
