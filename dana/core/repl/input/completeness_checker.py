"""
Code completeness checking for Dana REPL.

This module provides the InputCompleteChecker class that determines
whether Dana code input is complete or needs continuation.
"""

from dana.common.mixins.loggable import Loggable


class InputCompleteChecker(Loggable):
    """Checks if Dana input is complete."""

    def __init__(self):
        """Initialize the checker."""
        super().__init__()

    def is_complete(self, code: str) -> bool:
        """Check if the input code is a complete Dana statement/block."""
        code = code.strip()
        self.debug(f"Checking if complete: '{code}'")

        if not code:
            self.debug("Empty code, considered complete")
            return True

        # Handle simple assignments first
        if "=" in code and ":" not in code:  # Only check = if not in a block
            parts = code.split("=")
            if len(parts) == 2 and parts[1].strip():  # Has a value after =
                self.debug("Valid assignment found")
                return True
            self.debug("Incomplete assignment")
            return False

        # Handle single word variable reference
        if self._is_single_word_variable(code):
            self.debug("Single word variable reference")
            return True

        # Check brackets
        if not self._has_balanced_brackets(code):
            self.debug("Unbalanced brackets")
            return False

        # Check statements
        if not self._has_complete_statements(code):
            self.debug("Incomplete statements")
            return False

        self.debug("Code is complete")
        return True

    def is_obviously_incomplete(self, line: str) -> bool:
        """Check if input is obviously incomplete and needs continuation."""
        line = line.strip()

        # Lines ending with : are obviously incomplete (if, while, def, etc.)
        if line.endswith(":"):
            return True

        # Incomplete assignments
        if "=" in line and line.endswith("="):
            return True

        # Unbalanced brackets/parentheses
        if not self._has_balanced_brackets(line):
            return True

        # Everything else is considered complete for single-line execution
        return False

    def _is_single_word_variable(self, code: str) -> bool:
        """Check if input is a single word variable reference."""
        words = code.strip().split()
        return len(words) == 1 and "." in words[0] and all(part.isalpha() for part in words[0].split("."))

    def _has_balanced_brackets(self, code: str) -> bool:
        """Check if brackets and braces are balanced."""
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []
        in_string = False
        string_char = None

        for char in code:
            if char in ['"', "'"] and (not in_string or char == string_char):
                in_string = not in_string
                string_char = char if in_string else None
                continue

            if in_string:
                continue

            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack or brackets[stack.pop()] != char:
                    return False

        return not stack

    def _has_complete_statements(self, code: str) -> bool:
        """Check if all statements are complete."""
        code = code.strip()
        self.debug(f"Checking completeness of:\n{code}")

        # Split into lines and track indentation state
        lines = code.split("\n")
        indent_stack = [0]  # Stack to track expected indentation levels
        self.debug("Starting with indent stack: [0]")

        # Quick check for common control structures that are definitely incomplete
        if code.strip().endswith(":"):
            self.debug("Code ends with colon, definitely incomplete")
            return False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:  # Skip empty lines
                self.debug(f"Line {i + 1}: Skipping empty line")
                continue

            # Count leading spaces to determine indentation level
            indent = len(line) - len(line.lstrip())
            self.debug(f"Line {i + 1}: '{line}' (indent={indent}, expected={indent_stack[-1]})")

            # Check block start
            if stripped.endswith(":"):
                if i == len(lines) - 1:  # Block header with no body
                    self.debug(f"Line {i + 1}: Block header with no body")
                    return False
                # Next line must be indented
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line:  # If next line is not empty
                        next_indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                        if next_indent <= indent:  # Must be more indented
                            self.debug(f"Line {i + 1}: Next line not properly indented (next_indent={next_indent})")
                            return False
                indent_stack.append(indent + 4)  # Expect 4 spaces indentation
                self.debug(f"Line {i + 1}: Added indent level {indent + 4}, stack is now {indent_stack}")
                continue

            # Check indentation against current expected level
            if indent < indent_stack[-1]:
                # Dedent must match a previous indentation level
                self.debug(f"Line {i + 1}: Dedent detected, checking against stack {indent_stack}")
                while indent_stack and indent < indent_stack[-1]:
                    popped = indent_stack.pop()
                    self.debug(f"Line {i + 1}: Popped {popped}, stack is now {indent_stack}")
                if not indent_stack or indent != indent_stack[-1]:
                    self.debug(f"Line {i + 1}: Invalid dedent level {indent}")
                    return False
            elif indent > indent_stack[-1]:
                # Unexpected indentation
                self.debug(f"Line {i + 1}: Unexpected indent level {indent}")
                return False

            # Special handling for else blocks
            if stripped.startswith("else:"):
                if indent != indent_stack[-1]:
                    self.debug(f"Line {i + 1}: 'else' at wrong indentation level")
                    return False
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line:  # If next line is not empty
                        next_indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                        if next_indent <= indent:  # Must be more indented
                            self.debug(f"Line {i + 1}: 'else' block not properly indented")
                            return False

        # If we have a non-empty indent stack with more than just the base level,
        # it means we're in the middle of a block
        return len(indent_stack) <= 1
