"""
Code Context Analyzer for IPV optimization.

This module provides the CodeContextAnalyzer that extracts contextual information
from surrounding code, comments, and execution environment. The LLM will handle
intelligent analysis of this raw context.
"""

import inspect
from typing import Any

from lark import Token

from opendxa.common.mixins.loggable import Loggable


class CodeContext:
    """Container for extracted code context information."""

    def __init__(self):
        self.comments: list[str] = []
        self.inline_comments: list[str] = []
        self.variable_context: dict[str, Any] = {}
        self.function_context: str | None = None
        self.type_hints: dict[str, str] = {}
        self.surrounding_code: list[str] = []
        self.error_context: list[str] = []
        # Track the current line being executed and its line number
        self.current_line: str | None = None
        self.current_line_number: int | None = None
        self.surrounding_code_line_numbers: list[int] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "comments": self.comments,
            "inline_comments": self.inline_comments,
            "variable_context": self.variable_context,
            "function_context": self.function_context,
            "type_hints": self.type_hints,
            "surrounding_code": self.surrounding_code,
            "error_context": self.error_context,
            "current_line": self.current_line,
            "current_line_number": self.current_line_number,
            "surrounding_code_line_numbers": self.surrounding_code_line_numbers,
        }

    def has_context(self) -> bool:
        """Check if any meaningful context was extracted."""
        return bool(
            self.comments
            or self.inline_comments
            or self.variable_context
            or self.function_context
            or self.type_hints
            or self.surrounding_code
        )

    def get_context_summary(self) -> str:
        """Get a human-readable summary of the extracted context."""
        if not self.has_context():
            return "No additional context available"

        summary_parts = []

        if self.comments:
            summary_parts.append(f"{len(self.comments)} code comments")

        if self.type_hints:
            summary_parts.append(f"Type hints: {', '.join(self.type_hints.values())}")

        if self.surrounding_code:
            summary_parts.append(f"{len(self.surrounding_code)} lines of surrounding code")

        return "Context: " + ", ".join(summary_parts) if summary_parts else "Minimal context available"

    def get_current_line(self):
        return self.current_line

    def get_current_line_number(self):
        return self.current_line_number


class CodeContextAnalyzer(Loggable):
    """
    Analyzer that extracts contextual information from code and comments.

    This analyzer focuses on reliable extraction of raw context information.
    The LLM will handle intelligent analysis and decision-making based on this context.
    """

    def __init__(self):
        super().__init__()

    def analyze_context(self, context: Any, variable_name: str | None = None) -> CodeContext:
        """
        Analyze the execution context to extract code context information.

        Args:
            context: Execution context (e.g., SandboxContext for Dana)
            variable_name: Name of the variable being assigned (optional)

        Returns:
            CodeContext containing extracted information
        """
        code_context = CodeContext()

        # Store context for use in frame extraction
        self._context = context

        # Extract context from different sources
        self._extract_ast_context(context, code_context, variable_name)
        self._extract_frame_context(code_context, variable_name)
        self._extract_variable_context(context, code_context, variable_name)

        return code_context

    def _extract_ast_context(self, context: Any, code_context: CodeContext, variable_name: str | None) -> None:
        """Extract context from AST if available."""
        try:
            # Check if context has access to the current AST or program
            if hasattr(context, "_current_program") and context._current_program:
                program = context._current_program
                self._analyze_program_ast(program, code_context, variable_name)
            elif hasattr(context, "get_current_program"):
                program = context.get_current_program()
                if program:
                    self._analyze_program_ast(program, code_context, variable_name)
        except Exception as e:
            self.debug(f"Could not extract AST context: {e}")

    def _analyze_program_ast(self, program: Any, code_context: CodeContext, variable_name: str | None) -> None:
        """Analyze AST program for comments and context."""
        if not hasattr(program, "statements"):
            return

        # Look for comments and type information in the statement list
        for i, stmt in enumerate(program.statements):
            if isinstance(stmt, Token) and hasattr(stmt, "type") and stmt.type == "COMMENT":
                comment_text = stmt.value.lstrip("#").strip()
                code_context.comments.append(comment_text)

            # Extract variable names and types from assignments
            elif hasattr(stmt, "target") and hasattr(stmt, "value"):
                if hasattr(stmt.target, "name"):
                    var_name = stmt.target.name.split(".")[-1]  # Remove scope prefix
                    code_context.variable_context[var_name] = {"type": getattr(stmt, "type_hint", None), "nearby": True}

                    # Extract type information - this is reliable and concrete
                    if hasattr(stmt, "type_hint") and stmt.type_hint and hasattr(stmt.type_hint, "name"):
                        code_context.type_hints[var_name] = stmt.type_hint.name

    def _extract_frame_context(self, code_context: CodeContext, variable_name: str | None) -> None:
        """Extract context from the call stack and source code."""
        try:
            # First, check if we have REPL input context available
            if hasattr(self, "_context") and self._context:
                repl_input_context = self._context.get("system.__repl_input_context")
                if repl_input_context:
                    self.debug(f"Found REPL input context: {repl_input_context}")
                    self._analyze_repl_input_context(repl_input_context, code_context)
                    return

            # Get the calling frame to access source code
            frame = inspect.currentframe()
            # Go up the stack to find the Dana code execution frame
            for _ in range(6):  # Look up several frames
                if frame is None:
                    break
                frame = frame.f_back

            if frame is None:
                return

            # Try to get source file and line information
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno

            # Skip if it's not a real file (e.g., <string>)
            if "<" in filename and ">" in filename:
                return

            # Read source lines around the current location
            try:
                with open(filename) as f:
                    lines = f.readlines()

                # Extract lines around the current line for context
                start_line = max(0, lineno - 10)
                end_line = min(len(lines), lineno + 5)

                for line_idx in range(start_line, end_line):
                    line = lines[line_idx].strip()

                    # Look for comments
                    if line.startswith("#"):
                        comment_text = line.lstrip("#").strip()
                        code_context.comments.append(comment_text)
                    elif "#" in line:
                        # Inline comment
                        comment_part = line.split("#", 1)[1].strip()
                        code_context.inline_comments.append(comment_part)

                    # Store surrounding code for analysis
                    if line and not line.startswith("#"):
                        code_context.surrounding_code.append(line)
                        code_context.surrounding_code_line_numbers.append(line_idx + 1)

                # Set the current line being executed and its number
                if lineno - 1 >= 0 and lineno - 1 < len(lines):
                    code_context.current_line = lines[lineno - 1].strip()
                    code_context.current_line_number = lineno

            except OSError:
                # Can't read the file, skip source analysis
                pass

        except Exception as e:
            self.debug(f"Error extracting frame context: {e}")

    def _analyze_repl_input_context(self, repl_context: str, code_context: CodeContext) -> None:
        """Analyze REPL input context for comments and code patterns."""
        try:
            lines = repl_context.split("\n")
            for idx, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # Look for comments
                if line.startswith("#"):
                    comment_text = line.lstrip("#").strip()
                    if comment_text:  # Only add non-empty comments
                        code_context.comments.append(comment_text)
                elif "#" in line:
                    # Inline comment
                    comment_part = line.split("#", 1)[1].strip()
                    if comment_part:  # Only add non-empty comments
                        code_context.inline_comments.append(comment_part)

                # Store surrounding code for analysis (non-comment lines)
                if not line.startswith("#"):
                    code_context.surrounding_code.append(line)
                    code_context.surrounding_code_line_numbers.append(idx + 1)

            # Set the current line as the last non-empty code line
            for rev_idx, line in enumerate(reversed(code_context.surrounding_code)):
                if line:
                    code_context.current_line = line
                    code_context.current_line_number = len(code_context.surrounding_code) - rev_idx
                    break

            self.debug(
                f"Extracted from REPL context: {len(code_context.comments)} comments, {len(code_context.inline_comments)} inline comments"
            )

        except Exception as e:
            self.debug(f"Error analyzing REPL input context: {e}")

    def _extract_variable_context(self, context: Any, code_context: CodeContext, variable_name: str | None) -> None:
        """Extract context about variables from the execution context."""
        try:
            if not hasattr(context, "_state") or not context._state:
                return

            # Look for variables in the execution context
            for key, value in context._state.items():
                if key.startswith("local."):
                    var_name = key.split(".", 1)[1]
                    code_context.variable_context[var_name] = {"value_type": type(value).__name__, "in_scope": True}

        except Exception as e:
            self.debug(f"Error extracting variable context: {e}")

    def format_context_for_llm(self, original_prompt: str, code_context: CodeContext, expected_type: Any = None) -> str:
        """
        Format the extracted context for LLM analysis and decision-making.

        Args:
            original_prompt: The original prompt text
            code_context: Extracted code context
            expected_type: Expected return type (if available)

        Returns:
            Enhanced prompt with structured context for LLM analysis
        """
        if not code_context.has_context() and not expected_type:
            return original_prompt

        # Build context information for the LLM
        context_parts = []

        # Add type information (high confidence signal)
        if expected_type:
            context_parts.append(f"Expected output type: {expected_type}")

        if code_context.type_hints:
            type_info = ", ".join([f"{k}: {v}" for k, v in code_context.type_hints.items()])
            context_parts.append(f"Variable type hints: {type_info}")

        # Add comments (let LLM interpret)
        if code_context.comments:
            relevant_comments = [c for c in code_context.comments if len(c) > 5]
            if relevant_comments:
                context_parts.append(f"Code comments: {' | '.join(relevant_comments[:3])}")

        if code_context.inline_comments:
            context_parts.append(f"Inline comments: {' | '.join(code_context.inline_comments[:2])}")

        # Add surrounding code context (let LLM interpret)
        if code_context.surrounding_code:
            relevant_code = [line for line in code_context.surrounding_code if len(line.strip()) > 5]
            if relevant_code:
                context_parts.append(f"Surrounding code context: {' | '.join(relevant_code[:3])}")

        # Add variable context
        if code_context.variable_context:
            var_names = list(code_context.variable_context.keys())
            if var_names:
                context_parts.append(f"Variables in scope: {', '.join(var_names[:5])}")

        if context_parts:
            enhanced_prompt = f"""Please analyze this request with the provided context:

Request: {original_prompt}

Context:
{chr(10).join(f"- {part}" for part in context_parts)}

Based on this context, please:
1. Determine the most appropriate domain (financial, medical, legal, technical, business, data, creative, or general)
2. Identify the task type (extraction, analysis, validation, transformation, generation, classification, or general)
3. Provide the requested response optimized for the context and expected type"""

            return enhanced_prompt

        return original_prompt

    def get_optimization_hints_from_types(self, expected_type: Any, code_context: CodeContext) -> list[str]:
        """
        Get optimization hints based on type information (high confidence signals).

        Args:
            expected_type: Expected return type
            code_context: Extracted code context

        Returns:
            List of optimization hints based on reliable type information
        """
        hints = []

        # Process expected type (very reliable)
        if expected_type == float or expected_type == int:
            hints.append("numerical_precision")
            hints.append("extract_numbers_only")
        elif expected_type == bool:
            hints.append("binary_decision")
            hints.append("clear_yes_no")
        elif expected_type == dict:
            hints.append("structured_output")
            hints.append("json_format")
        elif expected_type == list:
            hints.append("list_format")
            hints.append("multiple_items")
        elif expected_type == str:
            hints.append("text_format")
            hints.append("clean_formatting")

        # Process type hints from code (also reliable)
        for var_name, type_name in code_context.type_hints.items():
            if type_name.lower() in ["float", "int"]:
                hints.append("numerical_context")
            elif type_name.lower() == "bool":
                hints.append("boolean_context")
            elif type_name.lower() in ["dict", "list"]:
                hints.append("structured_data_context")

        return list(set(hints))  # Remove duplicates
