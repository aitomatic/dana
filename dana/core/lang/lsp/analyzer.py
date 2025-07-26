"""
Dana Language Analyzer for LSP.

This module provides language analysis capabilities for the Dana Language Server,
leveraging the existing Dana parser infrastructure to provide diagnostics,
hover information, and completions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from lsprotocol import types as lsp

try:
    from lsprotocol import types as lsp

    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False

    # Create mock classes for runtime when LSP isn't available
    class MockDiagnostic:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class MockDiagnosticSeverity:
        Error = 1
        Warning = 2
        Information = 3
        Hint = 4

    class MockCompletionItemKind:
        Text = 1
        Keyword = 14
        Function = 3

    class MockPosition:
        def __init__(self, line=0, character=0):
            self.line = line
            self.character = character

    class MockRange:
        def __init__(self, start=None, end=None):
            self.start = start or MockPosition()
            self.end = end or MockPosition()

    # Mock namespace
    class MockLsp:
        Diagnostic = MockDiagnostic
        DiagnosticSeverity = MockDiagnosticSeverity
        CompletionItemKind = MockCompletionItemKind
        Position = MockPosition
        Range = MockRange

    lsp = MockLsp()

from dana.common.exceptions import ParseError
from dana.core.lang.ast import Program
from dana.core.lang.parser.utils.parsing_utils import ParserCache

logger = logging.getLogger(__name__)


class DanaAnalyzer:
    """Analyzes Dana code to provide LSP features."""

    def __init__(self):
        """Initialize the analyzer."""
        self.parser = ParserCache.get_parser("dana")

        # Dana-specific completions
        self.dana_keywords = [
            "def",
            "if",
            "else",
            "elif",
            "while",
            "for",
            "try",
            "except",
            "finally",
            "return",
            "break",
            "continue",
            "pass",
            "import",
            "from",
            "as",
            "struct",
            "agent",
            "use",
            "export",
            "True",
            "False",
            "None",
            "and",
            "or",
            "not",
            "in",
            "is",
        ]

        self.dana_scope_prefixes = ["private:", "public:", "local:", "system:"]

        self.dana_builtin_functions = [
            "log",
            "log.debug",
            "log.info",
            "log.warn",
            "log.error",
            "print",
            "reason",
            "len",
            "str",
            "int",
            "float",
            "bool",
            "list",
            "dict",
            "tuple",
            "set",
            "range",
            "enumerate",
            "zip",
        ]

    async def analyze(self, text: str) -> list[Any]:
        """Analyze Dana code and return diagnostics."""
        diagnostics = []

        try:
            # Parse the code using the existing Dana parser
            program = self.parser.parse(text, do_transform=True, do_type_check=False)

            # Add custom Dana-specific validations
            custom_diagnostics = self._analyze_dana_specific_rules(text, program)
            diagnostics.extend(custom_diagnostics)

        except ParseError as e:
            # Convert parse errors to LSP diagnostics
            diagnostic = self._parse_error_to_diagnostic(e)
            diagnostics.append(diagnostic)

        except Exception as e:
            # Handle unexpected parser errors
            logger.warning(f"Parser error: {e}")
            diagnostic = lsp.Diagnostic(  # type: ignore
                range=lsp.Range(  # type: ignore
                    start=lsp.Position(line=0, character=0),  # type: ignore
                    end=lsp.Position(line=0, character=0),  # type: ignore
                ),
                message=f"Parse error: {str(e)}",
                severity=lsp.DiagnosticSeverity.Error,  # type: ignore
                source="dana-parser",
            )
            diagnostics.append(diagnostic)

        return diagnostics

    def _analyze_dana_specific_rules(self, text: str, program: Program):
        """Analyze Dana-specific rules and patterns."""
        diagnostics = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines):
            line_diagnostics = self._analyze_line(line, line_num)
            diagnostics.extend(line_diagnostics)

        return diagnostics

    def _analyze_line(self, line: str, line_num: int):
        """Analyze a single line for Dana-specific issues."""
        diagnostics = []

        # Check for incorrect scope syntax (dot instead of colon)
        if self._has_incorrect_scope_syntax(line):
            diagnostic = lsp.Diagnostic(  # type: ignore
                range=lsp.Range(  # type: ignore
                    start=lsp.Position(line=line_num, character=0),  # type: ignore
                    end=lsp.Position(line=line_num, character=len(line)),  # type: ignore
                ),
                message="Use colon ':' for scope access, not dot '.'. Example: private:x instead of private.x",
                severity=lsp.DiagnosticSeverity.Warning,  # type: ignore
                source="dana-style",
            )
            diagnostics.append(diagnostic)

        # Check for string concatenation with + operator (suggest f-strings)
        if self._has_string_concatenation(line):
            diagnostic = lsp.Diagnostic(  # type: ignore
                range=lsp.Range(  # type: ignore
                    start=lsp.Position(line=line_num, character=0),  # type: ignore
                    end=lsp.Position(line=line_num, character=len(line)),  # type: ignore
                ),
                message="Consider using f-strings for string formatting instead of concatenation",
                severity=lsp.DiagnosticSeverity.Information,  # type: ignore
                source="dana-style",
            )
            diagnostics.append(diagnostic)

        # Check for missing scope prefixes on assignments
        if self._has_unscoped_assignment(line):
            diagnostic = lsp.Diagnostic(  # type: ignore
                range=lsp.Range(  # type: ignore
                    start=lsp.Position(line=line_num, character=0),  # type: ignore
                    end=lsp.Position(line=line_num, character=len(line)),  # type: ignore
                ),
                message="Consider adding scope prefix (private:, public:, local:, system:) to variable",
                severity=lsp.DiagnosticSeverity.Hint,  # type: ignore
                source="dana-style",
            )
            diagnostics.append(diagnostic)

        return diagnostics

    def _has_incorrect_scope_syntax(self, line: str) -> bool:
        """Check if line uses dot notation for scope access."""
        scope_prefixes = ["private.", "public.", "local.", "system."]
        return any(prefix in line for prefix in scope_prefixes)

    def _has_string_concatenation(self, line: str) -> bool:
        """Check if line uses string concatenation with +."""
        # Simple heuristic: look for quoted strings followed by + followed by more content
        import re

        pattern = r'["\'][^"\']*["\'\s]*\+\s*'
        return bool(re.search(pattern, line))

    def _has_unscoped_assignment(self, line: str) -> bool:
        """Check if line has an assignment without scope prefix."""
        import re

        # Look for variable assignment without scope prefix
        pattern = r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*="
        match = re.search(pattern, line.strip())
        if match:
            var_name = match.group(1)
            # Check if it's not a known exception (like function parameters, loop variables)
            if var_name not in ["i", "j", "k", "item", "key", "value", "line", "data"]:
                return True
        return False

    async def get_hover(self, text: str, line: int, character: int) -> str | None:
        """Get hover information for a symbol at the given position."""
        try:
            lines = text.split("\n")
            if line >= len(lines):
                return None

            current_line = lines[line]
            if character >= len(current_line):
                return None

            # Find the word at the cursor position
            word = self._get_word_at_position(current_line, character)
            if not word:
                return None

            # Provide hover information for Dana constructs
            hover_info = self._get_dana_hover_info(word)
            return hover_info

        except Exception as e:
            logger.warning(f"Error getting hover info: {e}")
            return None

    def _get_word_at_position(self, line: str, character: int) -> str | None:
        """Extract the word at the given character position."""
        if character >= len(line):
            return None

        # Find word boundaries
        start = character
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] in "_.:"):
            start -= 1

        end = character
        while end < len(line) and (line[end].isalnum() or line[end] in "_.:"):
            end += 1

        if start < end:
            return line[start:end]
        return None

    def _get_dana_hover_info(self, word: str) -> str | None:
        """Get hover information for Dana-specific constructs."""

        # Scope prefixes
        if word in ["private:", "public:", "local:", "system:"]:
            return f"**{word}** - Dana scope prefix for variable access"

        # Keywords
        keyword_docs = {
            "agent": "**agent** - Define an autonomous agent",
            "struct": "**struct** - Define a data structure",
            "use": "**use** - Import external resources or MCP servers",
            "reason": "**reason()** - Dana reasoning function",
            "log": "**log** - Logging utilities (log.info, log.warn, log.error)",
            "log.info": "**log.info()** - Log informational messages",
            "log.warn": "**log.warn()** - Log warning messages",
            "log.error": "**log.error()** - Log error messages",
            "print": "**print()** - Print output to console",
        }

        if word in keyword_docs:
            return keyword_docs[word]

        return None

    async def get_completions(self, text: str, line: int, character: int) -> list[dict[str, Any]]:
        """Get completion suggestions for the given position."""
        try:
            lines = text.split("\n")
            if line >= len(lines):
                return []

            current_line = lines[line]
            prefix = current_line[:character]

            completions = []

            # Add scope prefix completions
            if self._should_suggest_scope_prefixes(prefix):
                for scope in self.dana_scope_prefixes:
                    completions.append(
                        {"label": scope, "kind": lsp.CompletionItemKind.Keyword, "detail": "Dana scope prefix", "insert_text": scope}
                    )

            # Add keyword completions
            for keyword in self.dana_keywords:
                if keyword.startswith(prefix.split()[-1] if prefix.split() else ""):
                    completions.append({"label": keyword, "kind": lsp.CompletionItemKind.Keyword, "detail": "Dana keyword"})

            # Add built-in function completions
            for func in self.dana_builtin_functions:
                if prefix.endswith(".") or func.startswith(prefix.split()[-1] if prefix.split() else ""):
                    completions.append(
                        {
                            "label": func,
                            "kind": lsp.CompletionItemKind.Function,
                            "detail": "Dana built-in function",
                            "insert_text": func + "()" if not func.endswith(".") else func,
                        }
                    )

            return completions

        except Exception as e:
            logger.warning(f"Error getting completions: {e}")
            return []

    def _should_suggest_scope_prefixes(self, prefix: str) -> bool:
        """Check if we should suggest scope prefixes."""
        # Suggest scope prefixes at the beginning of assignments
        return bool(prefix.strip() and "=" not in prefix and ":" not in prefix)

    def _parse_error_to_diagnostic(self, error: ParseError):
        """Convert a ParseError to an LSP Diagnostic."""
        # Try to extract line and column from the error message
        line_num = 0
        character = 0

        # ParseError might have location information
        if hasattr(error, "line") and error.line is not None:
            line_num = max(0, error.line - 1)  # Convert to 0-based
        if hasattr(error, "column") and error.column is not None:
            character = max(0, error.column)

        return lsp.Diagnostic(  # type: ignore
            range=lsp.Range(  # type: ignore
                start=lsp.Position(line=line_num, character=character),  # type: ignore
                end=lsp.Position(line=line_num, character=character + 1),  # type: ignore
            ),
            message=str(error),
            severity=lsp.DiagnosticSeverity.Error,  # type: ignore
            source="dana-parser",
        )
