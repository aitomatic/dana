"""
Command handling for Dana REPL.

This module provides the CommandHandler class that processes
special commands and coordinates with the help formatter.
"""

from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme
from dana.core.repl.repl import REPL

from .help_formatter import HelpFormatter


class CommandHandler(Loggable):
    """Handles REPL special commands."""

    def __init__(self, repl: REPL, colors: ColorScheme):
        """Initialize with a REPL instance and color scheme."""
        super().__init__()
        self.repl = repl
        self.colors = colors
        self.help_formatter = HelpFormatter(repl, colors)

    async def handle_command(self, cmd: str) -> bool:
        """Process a command and return True if it was a special command."""
        cmd = cmd.strip()

        # Process help commands
        if cmd in ["help", "?"]:
            self.help_formatter.show_help()
            return True

        # Process special "##" commands
        if cmd.startswith("##"):
            parts = cmd[2:].strip().split()
            if not parts:
                # Just "##" - force multiline mode
                print(f"{self.colors.accent('✅ Forced multiline mode - type your code, end with empty line')}")
                return True  # Handle in main loop with special flag

            if parts[0] == "nlp":
                if len(parts) == 1:
                    self.help_formatter.show_nlp_status()
                    return True
                elif len(parts) == 2:
                    if parts[1] == "on":
                        self.repl.set_nlp_mode(True)
                        print(f"{self.colors.accent('✅ NLP mode enabled')}")
                        return True
                    elif parts[1] == "off":
                        self.repl.set_nlp_mode(False)
                        print(f"{self.colors.error('❌ NLP mode disabled')}")
                        return True
                    elif parts[1] == "status":
                        self.help_formatter.show_nlp_status()
                        return True
                    elif parts[1] == "test":
                        await self._run_nlp_test()
                        return True

        return False

    async def _run_nlp_test(self) -> None:
        """Run NLP transcoder test."""
        if not self.repl.transcoder:
            print(f"{self.colors.error('❌ No LLM resource available for transcoding')}")
            print("Configure an LLM resource by setting one of these environment variables:")
            print(f"  {self.colors.accent('- OPENAI_API_KEY, ANTHROPIC_API_KEY, AZURE_OPENAI_API_KEY, etc.')}")
            return

        print("Testing NLP transcoder with common examples...")
        test_inputs = ["calculate 10 + 20", "add 42 and 17", "print hello world", "if x is greater than 10 then log success"]

        original_mode = self.repl.get_nlp_mode()
        self.repl.set_nlp_mode(True)

        # Test each input without progress bar
        for test_input in test_inputs:
            print(f"\n{self.colors.accent(f"➡️ Test input: '{test_input}'")}")
            try:
                result = self.repl.execute(test_input)
                print(f"{self.colors.bold('Execution result:')}\n{result}")
            except Exception as e:
                print(f"{self.colors.error('Execution failed:')}\n{e}")

        self.repl.set_nlp_mode(original_mode)
