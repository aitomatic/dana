"""
Dana syntax highlighting for TUI components.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import re
from re import Pattern

from rich.highlighter import Highlighter
from rich.text import Text


class DanaSyntaxHighlighter:
    """
    A class for applying syntax highlighting to Dana code using Rich markup.

    This class provides methods to highlight Dana syntax elements including
    keywords, strings, numbers, comments, and function calls. It also handles
    result value highlighting for different data types.

    Performance optimized with compiled regex patterns.
    """

    # Dana keywords to highlight (from dana_grammar.lark)
    DANA_KEYWORDS = [
        # Control flow
        "if",
        "else",
        "elif",
        "for",
        "while",
        "break",
        "continue",
        "pass",
        # Functions and methods
        "def",
        "return",
        "deliver",
        "lambda",
        # Data structures and types
        "struct",
        "resource",
        "agent",
        "agent_blueprint",
        # Type annotations
        "int",
        "float",
        "str",
        "bool",
        "list",
        "dict",
        "tuple",
        "set",
        "None",
        "any",
        # Exception handling
        "try",
        "except",
        "finally",
        "raise",
        "assert",
        # Context management
        "with",
        "as",
        # Import/export
        "import",
        "from",
        "export",
        "use",
        # Scope modifiers
        "private",
        "public",
        "local",
        "system",
        # Logical operators
        "and",
        "or",
        "not",
        "in",
        "is",
        # Other keywords
        "True",
        "False",
        "None",
    ]

    def __init__(self):
        """Initialize the syntax highlighter with compiled regex patterns."""
        # Compile regex patterns once for better performance
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict[str, Pattern]:
        """Compile all regex patterns used for syntax highlighting."""
        patterns = {}

        # Comments (highest priority - most specific)
        patterns["hash_comment"] = re.compile(r"(#[^\n]*)")
        patterns["double_slash_comment"] = re.compile(r"(//[^\n]*)")

        # String literals (before keywords to avoid conflicts)
        patterns["double_quoted_string"] = re.compile(r'("(?:[^"\\]|\\.)*")')
        patterns["single_quoted_string"] = re.compile(r"('(?:[^'\\]|\\.)*')")

        # Numbers (simple pattern - only standalone numbers)
        patterns["numbers"] = re.compile(r"\b(\d+(?:\.\d+)?)\b")

        # Function calls (simple pattern)
        patterns["function_calls"] = re.compile(r"\b([a-zA-Z_]\w*)(?=\s*\()")

        # Result validation patterns
        patterns["result_number"] = re.compile(r"^-?\d+(\.\d+)?$")

        # Create a single compiled pattern for all keywords
        # This is much more efficient than processing keywords one by one
        if self.DANA_KEYWORDS:
            # Sort keywords by length (longest first) to avoid partial matches
            sorted_keywords = sorted(self.DANA_KEYWORDS, key=len, reverse=True)
            # Escape special regex characters in keywords
            escaped_keywords = [re.escape(keyword) for keyword in sorted_keywords]
            # Create a single pattern that matches any keyword with word boundaries
            keyword_pattern = r"\b(" + "|".join(escaped_keywords) + r")\b"
            patterns["keywords"] = re.compile(keyword_pattern)

        return patterns

    def escape_markup(self, text: str) -> str:
        """
        Escape square brackets in text to prevent Rich markup interpretation.

        Args:
            text: Text that may contain square brackets

        Returns:
            Text with square brackets escaped for safe Rich markup display
        """
        if not text or not isinstance(text, str):
            return str(text)

        # Escape square brackets to prevent Rich markup interpretation
        return text.replace("[", r"\[").replace("]", r"\]")

    def highlight_code(self, text: str) -> str:
        """
        Apply syntax highlighting to Dana code using Rich markup.

        Args:
            text: The Dana code text to highlight

        Returns:
            Text with Rich markup for syntax highlighting
        """
        if not text or not isinstance(text, str):
            return str(text)

        # SAFETY FIRST: If the text already contains markup-like patterns,
        # escape them to prevent Rich markup errors

        # Check if the text contains potential markup patterns
        if "[" in text and "]" in text:
            # Escape any existing square brackets to prevent them from being
            # interpreted as Rich markup
            text = text.replace("[", r"\[").replace("]", r"\]")

        # Use single-pass processing with non-overlapping patterns
        result = text

        # 1. Comments (highest priority - most specific)
        result = self._compiled_patterns["hash_comment"].sub(r"[dim]\1[/dim]", result)
        result = self._compiled_patterns["double_slash_comment"].sub(r"[dim]\1[/dim]", result)

        # 2. String literals (before keywords to avoid conflicts)
        result = self._compiled_patterns["double_quoted_string"].sub(r"[green]\1[/green]", result)
        result = self._compiled_patterns["single_quoted_string"].sub(r"[green]\1[/green]", result)

        # 3. Numbers (simple pattern - only standalone numbers)
        result = self._compiled_patterns["numbers"].sub(r"[cyan]\1[/cyan]", result)

        # 4. Highlight Dana keywords (single compiled pattern for all keywords)
        result = self._compiled_patterns["keywords"].sub(r"[blue]\1[/blue]", result)

        # 5. Function calls (simple pattern)
        result = self._compiled_patterns["function_calls"].sub(r"[yellow]\1[/yellow]", result)

        return result

    def highlight_result(self, result_str: str) -> str:
        """
        Apply appropriate highlighting to Dana result values.

        Args:
            result_str: String representation of the result

        Returns:
            Highlighted result string with Rich markup
        """
        if not result_str:
            return result_str

        # Check for different result types and apply appropriate colors

        # Numbers (integers, floats)
        if self._compiled_patterns["result_number"].match(result_str.strip()):
            return f"[cyan]{result_str}[/cyan]"

        # Booleans
        if result_str.strip() in ("True", "False"):
            return f"[bright_blue]{result_str}[/bright_blue]"

        # None
        if result_str.strip() == "None":
            return f"[dim]{result_str}[/dim]"

        # Strings (if they have quotes)
        if (result_str.startswith('"') and result_str.endswith('"')) or (result_str.startswith("'") and result_str.endswith("'")):
            return f"[green]{result_str}[/green]"

        # Lists, tuples, dicts (if they start with appropriate brackets)
        if result_str.startswith("[") and result_str.endswith("]"):
            return f"[yellow]{result_str}[/yellow]"  # Lists
        elif result_str.startswith("(") and result_str.endswith(")"):
            return f"[yellow]{result_str}[/yellow]"  # Tuples
        elif result_str.startswith("{") and result_str.endswith("}"):
            return f"[yellow]{result_str}[/yellow]"  # Dicts/sets

        # For more complex Dana code results, try syntax highlighting
        # This handles cases where Dana returns code-like strings
        if any(keyword in result_str for keyword in ["def ", "class ", "if ", "for ", "while "]):
            return self.highlight_code(result_str)

        # Default: no special highlighting
        return result_str

    def highlight_error(self, error_message: str) -> str:
        """
        Apply error highlighting to error messages.

        Args:
            error_message: The error message to highlight

        Returns:
            Error message with red highlighting
        """
        safe_error = self.escape_markup(str(error_message))
        return f"[red]Error: {safe_error}[/red]"

    def highlight_system_message(self, message: str, style: str = "dim") -> str:
        """
        Apply highlighting to system messages.

        Args:
            message: The system message to highlight
            style: The style to apply ("dim", "yellow", "red", "green")

        Returns:
            System message with appropriate highlighting
        """
        if style == "dim":
            return f"[dim]{message}[/dim]"
        elif style == "yellow":
            return f"[yellow]{message}[/yellow]"
        elif style == "red":
            return f"[red]{message}[/red]"
        elif style == "green":
            return f"[green]{message}[/green]"
        else:
            return message


class RichDanaHighlighter(DanaSyntaxHighlighter, Highlighter):
    """A Rich highlighter for Dana syntax, using multiple inheritance."""

    def highlight(self, text: Text) -> None:
        """Highlight the given text.

        Args:
            text: The text to highlight.
        """
        highlighted_string = self.highlight_code(text.plain)
        highlighted_text = Text.from_markup(highlighted_string)
        text.spans = highlighted_text.spans


# Global instance for convenience
dana_highlighter = RichDanaHighlighter()
