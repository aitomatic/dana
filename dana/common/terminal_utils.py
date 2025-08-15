"""
Terminal Utilities for Dana CLI

This module provides common utilities for terminal styling and color support
to be used across the Dana command-line tools.
"""

import os
import sys

from prompt_toolkit.lexers import PygmentsLexer, SimpleLexer
from pygments.lexer import RegexLexer
from pygments.token import Comment, Keyword, Name, Number, Operator, String, Text

# Constants
DEFAULT_TERMINAL_WIDTH = 80


# Color scheme definitions
class ColorScheme:
    """Defines a consistent color scheme for Dana terminal applications."""

    def __init__(self, use_colors: bool = True):
        """Initialize the color scheme.

        Args:
            use_colors: Whether to use colors or not
        """
        self.use_colors = use_colors

        if use_colors:
            # Simplified color scheme with just a few colors
            self.ACCENT = "\033[36m"  # Cyan - for headers and highlights
            self.ERROR = "\033[91m"  # Red - for errors only
            self.BOLD = "\033[1m"  # Bold text for emphasis
            self.RESET = "\033[0m"  # Reset formatting
        else:
            self.ACCENT = self.ERROR = self.BOLD = self.RESET = ""

    def header(self, text: str) -> str:
        """Format text as a header."""
        return f"{self.ACCENT}{self.BOLD}{text}{self.RESET}"

    def accent(self, text: str) -> str:
        """Format text with accent color."""
        return f"{self.ACCENT}{text}{self.RESET}"

    def error(self, text: str) -> str:
        """Format text as an error."""
        return f"{self.ERROR}{text}{self.RESET}"

    def bold(self, text: str) -> str:
        """Format text as bold."""
        return f"{self.BOLD}{text}{self.RESET}"

    def reset(self, text: str = "") -> str:
        """Reset formatting and optionally add text."""
        return f"{self.RESET}{text}"

    def dim(self, text: str) -> str:
        """Format text as dimmed/faded."""
        if self.use_colors:
            return f"\033[2m{text}{self.RESET}"  # Dim/faded text
        else:
            return text


# Define a Pygments lexer for Dana
class DanaLexer(RegexLexer):
    """A pygments lexer for Dana syntax highlighting."""

    name = "Dana"
    aliases = ["dana"]
    filenames = ["*.na"]

    tokens = {
        "root": [
            # Comments
            (r"#.*$", Comment.Single),
            # Keywords
            (r"\b(if|else|while|print|func|return|try|except|for|in|break|continue|import|and|or|not|true|false|reason)\b", Keyword),
            # Scopes
            (r"\b(local|private|public|system)\b", Name.Builtin),
            # String literals
            (r'"[^"]*"', String),
            (r"'[^']*'", String),
            # Numbers
            (r"\b\d+(\.\d+)?\b", Number),
            # Operators
            (r"(\+|\-|\*|\/|==|!=|<=|>=|<|>|=|\(|\)|\[|\]|\{|\}|\.|\,|\:)", Operator),
            # Whitespace
            (r"\s+", Text),
            # Everything else
            (r"[a-zA-Z_][a-zA-Z0-9_]*", Text),
        ]
    }


def get_dana_lexer():
    """Get a prompt_toolkit lexer for Dana syntax highlighting."""
    try:
        return PygmentsLexer(DanaLexer)
    except Exception:
        # Fall back to simple lexer if there's any issue
        return SimpleLexer()


def supports_color() -> bool:
    """Check if the terminal supports color output."""
    # Return False if not a TTY
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    # Check for NO_COLOR environment variable
    if os.environ.get("NO_COLOR", ""):
        return False

    # Force color support if CLICOLOR_FORCE is set to a non-empty string
    if os.environ.get("CLICOLOR_FORCE", ""):
        return True

    # Check for CLICOLOR environment variable
    clicolor = os.environ.get("CLICOLOR", "1")
    if clicolor == "0":
        return False

    # Check for specific terminals with known color support
    term = os.environ.get("TERM", "")
    colorterm = os.environ.get("COLORTERM", "")
    if term.endswith("-256color") or term.endswith("-color") or term == "xterm" or colorterm:
        return True

    # Windows specific check
    if sys.platform == "win32":
        # Check for ANSICON, ConEMU, Windows Terminal, or Windows 10+
        return (
            os.environ.get("ANSICON", "")
            or os.environ.get("ConEMUANSI", "") == "ON"
            or os.environ.get("WT_SESSION", "")
            or os.environ.get("TERM_PROGRAM", "") == "vscode"
        )

    # Check for modern terminal emulators
    if os.environ.get("TERM_PROGRAM", "") in ["iTerm.app", "Apple_Terminal", "vscode"]:
        return True

    # On other platforms, assume it's supported if it's a TTY
    return True


def print_header(text: str, width: int = DEFAULT_TERMINAL_WIDTH, colors: ColorScheme | None = None) -> None:
    """Print a formatted header with a border.

    Args:
        text: The header text to display
        width: The width of the terminal
        colors: The color scheme to use
    """
    if colors is None:
        colors = ColorScheme(supports_color())

    # Create border and center text
    if colors.use_colors:
        border = "═" * width
    else:
        border = "=" * width

    # Center the text
    padding = (width - len(text)) // 2
    centered_text = " " * padding + text

    print(f"\n{colors.header(border)}")
    print(colors.header(centered_text))
    print(f"{colors.header(border)}\n")


def get_terminal_width() -> int:
    """Get the current terminal width or return a default."""
    try:
        return os.get_terminal_size().columns
    except (AttributeError, OSError):
        return DEFAULT_TERMINAL_WIDTH
