"""
Welcome message for Dana REPL.

This module provides the WelcomeDisplay class that shows
the initial greeting and information when the REPL starts.
"""

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.shortcuts import print_formatted_text

from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme, print_header


class WelcomeDisplay(Loggable):
    """Displays welcome message and initial information for the Dana REPL."""

    def __init__(self, colors: ColorScheme):
        """Initialize with a color scheme."""
        super().__init__()
        self.colors = colors

    def show_welcome(self) -> None:
        """Display the welcome message and feature overview."""
        width = 80
        print_header("Dana Interactive REPL", width, self.colors)

        # Welcome message
        welcome_text = (
            "Welcome to the Dana (Domain-Aware NeuroSymbolic Architecture) REPL!\n"
            "Type Dana code or natural language commands and see them executed instantly.\n"
            f"Type {self.colors.bold('help')} or {self.colors.bold('?')} for help, {self.colors.bold('exit')} or {self.colors.bold('quit')} to end the session."
        )
        print_formatted_text(ANSI(welcome_text))

        print_formatted_text(ANSI(f"\n{self.colors.bold('Key Features:')}"))
        print_formatted_text(
            ANSI(f"  • {self.colors.accent('Multi-line Code Entry')} - Continue typing for blocks, prompt changes to '... '")
        )
        print_formatted_text(ANSI(f"  • {self.colors.accent('Press Enter on empty line')} - End multiline blocks and execute them"))
        print_formatted_text(ANSI(f"  • {self.colors.accent('Natural Language Processing')} - Enable with /nlp on to use plain English"))
        print_formatted_text(ANSI(f"  • {self.colors.accent('Tab Completion')} - Press Tab to complete commands and keywords"))
        print_formatted_text(ANSI(f"  • {self.colors.accent('Command History')} - Use up/down arrows to navigate previous commands"))
        print_formatted_text(ANSI(f"  • {self.colors.accent('Syntax Highlighting')} - Colored syntax for better readability"))
        print_formatted_text(ANSI(f"  • {self.colors.accent('History Search')} - Press Ctrl+R to search command history"))

        print_formatted_text(ANSI(f"\n{self.colors.bold('Quick Commands:')}"))
        print_formatted_text(ANSI(f"  • {self.colors.accent('/')} - Force execution of multi-line block"))
        print_formatted_text(ANSI(f"  • {self.colors.accent('/nlp on/off')} - Toggle natural language processing mode"))
        print_formatted_text(ANSI(f"  • {self.colors.accent('Ctrl+C')} - Cancel the current input"))

        print_formatted_text(ANSI(f"\nType {self.colors.bold('help')} for full documentation\n"))
