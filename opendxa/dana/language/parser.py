"""Grammar-based parser for DANA language.

This module provides a robust parser for DANA using the Lark parsing library.
It offers good extensibility, error reporting, and maintainability.
"""

import logging
import os
from pathlib import Path
from typing import List, NamedTuple, Optional

try:
    from lark import Lark, Token, Transformer, Tree
    from lark.exceptions import LarkError, UnexpectedInput
    from lark.indenter import Indenter

    LARK_AVAILABLE = True
except ImportError:
    # Define compatibility stubs so the module can load without Lark
    LARK_AVAILABLE = False

    class Token:
        pass

    class Tree:
        pass

    class Lark:
        pass

    class Transformer:
        pass

    class Indenter:
        pass

    class LarkError(Exception):
        pass

    class UnexpectedInput(Exception):
        pass


from opendxa.dana.exceptions import ParseError
from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    FStringExpression,
    FunctionCall,
    Identifier,
    Literal,
    LiteralExpression,
    LogLevel,
    LogLevelSetStatement,
    LogStatement,
    PrintStatement,
    Program,
    ReasonStatement,
    WhileLoop,
)

# Create a logger for dana
logger = logging.getLogger("dana")


class ParseResult(NamedTuple):
    """Result of parsing a DANA program."""

    program: Program
    errors: List[ParseError] = []

    @property
    def is_valid(self) -> bool:
        """Check if parsing was successful (no errors)."""
        return len(self.errors) == 0

    @property
    def error(self) -> Optional[ParseError]:
        """Get the first error if any exist, for backward compatibility."""
        return self.errors[0] if self.errors else None


# Environment variable for controlling type checking
ENV_TYPE_CHECK = "DANA_TYPE_CHECK"
ENABLE_TYPE_CHECK = os.environ.get(ENV_TYPE_CHECK, "1").lower() in ["1", "true", "yes", "y"]


class DanaIndenter(Indenter):
    """Indenter for DANA language.

    Handles Python-style indentation for blocks.
    """

    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "INDENT"
    DEDENT_type = "DEDENT"
    tab_len = 8


class DanaTransformer(Transformer):
    """Transforms Lark parse tree nodes into DANA AST nodes."""

    def start(self, items):
        """Transform the start rule into a Program node."""
        # Filter out None items (e.g., from comments or empty lines)
        statements = [item for item in items if item is not None]
        return Program(statements=statements)

    def statement(self, items):
        """Transform a statement rule."""
        # Return the first non-None item
        for item in items:
            if item is not None:
                return item
        return None

    def assignment(self, items):
        """Transform an assignment rule into an Assignment node."""
        target = items[0]
        value = items[1]
        return Assignment(target=target, value=value)

    def log_statement(self, items):
        """Transform a log statement rule into a LogStatement node."""
        # Default level is INFO
        level = LogLevel.INFO

        # Filter out None values
        items = [item for item in items if item is not None]

        if not items:
            return None

        # If level is specified, use it
        if len(items) > 1 and hasattr(items[0], "value"):
            level_str = items[0].value.upper()
            level = LogLevel[level_str]
            message = items[1]
        else:
            message = items[0]

        return LogStatement(message=message, level=level)

    def level(self, items):
        """Transform a log level into a string."""
        return items[0]

    def DEBUG(self, _):
        return Token("LEVEL", "DEBUG")

    def INFO(self, _):
        return Token("LEVEL", "INFO")

    def WARN(self, _):
        return Token("LEVEL", "WARN")

    def ERROR(self, _):
        return Token("LEVEL", "ERROR")

    def conditional(self, items):
        """Transform a conditional rule into a Conditional node."""
        if_part = items[0]
        else_body = []

        # If we have an else part, extract the else body
        if len(items) > 1 and items[1] is not None:
            else_body = items[1]

        # Extract condition and if body from if_part
        condition = if_part[0]
        if_body = if_part[1:]

        # Use line info from the parse tree if available
        line_num = getattr(condition, "line", 0) or 0
        return Conditional(condition=condition, body=if_body, else_body=else_body, line_num=line_num)

    def if_part(self, items):
        """Transform if part of conditional into a list with condition first, then body statements."""
        # First item is the condition, rest are the body statements
        condition = items[0]

        # Filter out INDENT/DEDENT tokens and None values from the body
        body = [item for item in items[1:] if not (isinstance(item, Token) or item is None)]

        return [condition] + body

    def else_part(self, items):
        """Transform else part of conditional into a list of body statements."""
        # Filter out INDENT/DEDENT tokens and None values
        return [item for item in items if not (isinstance(item, Token) or item is None)]

    def while_loop(self, items):
        """Transform a while loop rule into a WhileLoop node."""
        condition = items[0]
        # Filter out INDENT/DEDENT tokens and None values from the body
        body = [item for item in items[1:] if not (isinstance(item, Token) or item is None)]
        # Use line info from the parse tree if available
        line_num = getattr(condition, "line", 0) or 0
        return WhileLoop(condition=condition, body=body, line_num=line_num)

    def reason_statement(self, items):
        """Transform a reason statement rule into a ReasonStatement node."""
        # Filter out None values
        items = [item for item in items if item is not None]

        # Check if we have a target variable
        if items and isinstance(items[0], Identifier):
            target = items[0]
            # Get the prompt from the next item
            prompt = items[1] if len(items) > 1 else LiteralExpression(literal=Literal(value=""))
            rest = items[2:]
        else:
            target = None
            # Get the prompt from the first item
            prompt = items[0] if items else LiteralExpression(literal=Literal(value=""))
            rest = items[1:]

        # Make sure we have a valid prompt
        if prompt is None:
            prompt = LiteralExpression(literal=Literal(value=""))
        elif isinstance(prompt, Token):
            # Convert token to LiteralExpression
            value = (
                prompt.value.strip("\"'") if prompt.type in ("STRING", "DOUBLE_QUOTE_STRING", "SINGLE_QUOTE_STRING") else str(prompt.value)
            )
            prompt = LiteralExpression(literal=Literal(value=value))

        # Process optional context and options
        context = None
        options = {}

        # Process named arguments
        for item in rest:
            if isinstance(item, tuple):
                # Named argument
                arg_name, arg_value = item
                if arg_name == "context":
                    # Handle context special case
                    if isinstance(arg_value, Identifier):
                        context = [arg_value]
                    elif isinstance(arg_value, list):
                        context = arg_value
                    elif hasattr(arg_value, "literal") and isinstance(arg_value.literal.value, list):
                        # Handle array literal
                        context = arg_value.literal.value
                else:
                    # Other options
                    options[arg_name] = arg_value
            elif isinstance(item, list):
                # List of named arguments
                for sub_item in item:
                    if isinstance(sub_item, tuple):
                        arg_name, arg_value = sub_item
                        if arg_name == "context":
                            # Handle context special case
                            if isinstance(arg_value, Identifier):
                                context = [arg_value]
                            elif isinstance(arg_value, list):
                                context = arg_value
                            elif hasattr(arg_value, "literal") and isinstance(arg_value.literal.value, list):
                                # Handle array literal
                                context = arg_value.literal.value
                        else:
                            # Other options
                            options[arg_name] = arg_value

        # If options is empty, set it to None
        if not options:
            options = None

        return ReasonStatement(prompt=prompt, target=target, context=context, options=options)

    def context_arg(self, items):
        """Transform a context argument into a list of identifiers."""
        if len(items) == 1 and isinstance(items[0], list):
            return items[0]  # Already a list of identifiers
        elif len(items) == 1 and isinstance(items[0], Identifier):
            return [items[0]]  # Single identifier
        return []  # Empty context

    def identifier_list(self, items):
        """Transform an identifier list into a list."""
        return items

    def options(self, items):
        """Transform options into a dictionary."""
        result = {}
        for item in items:
            key, value = item
            result[key] = value
        return result

    def key_value(self, items):
        """Transform a key-value pair into a tuple."""
        key = items[0].value
        value = items[1]
        return (key, value)

    def log_level_set_statement(self, items):
        """Transform a log level set statement into a LogLevelSetStatement node."""
        if not items:
            return None

        # Check what type of item we have
        item = items[0]

        # Handle string literal (log.setLevel("INFO"))
        if isinstance(item, Token) and item.type == "STRING":
            level_str = item.value.strip("\"'")
            try:
                level = LogLevel[level_str.upper()]
                return LogLevelSetStatement(level=level)
            except KeyError:
                # Return None for invalid log levels, handled in parser
                return None

        # Handle level token (log.setLevel(INFO))
        elif hasattr(item, "value"):
            level_str = item.value.upper()
            try:
                level = LogLevel[level_str]
                return LogLevelSetStatement(level=level)
            except KeyError:
                # Return None for invalid log levels, handled in parser
                return None

        # If we got here, something went wrong
        return None

    def print_statement(self, items):
        """Transform a print statement rule into a PrintStatement node."""
        message = items[0]
        return PrintStatement(message=message)

    def function_call(self, items):
        """Transform a function call into a FunctionCall node."""
        name = items[0].name  # Identifier node

        # Process arguments
        args = {}
        if len(items) > 1:
            # We have arguments
            arg_items = items[1:]

            # Filter out None values
            arg_items = [item for item in arg_items if item is not None]

            # Check if we have positional or named arguments or both
            for arg in arg_items:
                if isinstance(arg, tuple):
                    # Named argument
                    key, value = arg
                    args[key] = value
                elif isinstance(arg, list):
                    # List of named arguments or positional arguments
                    for sub_arg in arg:
                        if isinstance(sub_arg, tuple):
                            # Named argument
                            key, value = sub_arg
                            args[key] = value
                        else:
                            # Positional argument - use a numeric key
                            args[f"arg{len(args)}"] = sub_arg
                else:
                    # Positional argument - use a numeric key
                    args[f"arg{len(args)}"] = arg

        # For direct reason() function calls, handle special case
        if name == "reason" and "arg0" in args:
            # This is a special case for reason() statements without assignment
            prompt = args["arg0"]

            # Convert string tokens to LiteralExpression
            if isinstance(prompt, Token) and prompt.type in ("STRING", "DOUBLE_QUOTE_STRING", "SINGLE_QUOTE_STRING"):
                value = prompt.value.strip("\"'")
                prompt = LiteralExpression(literal=Literal(value=value))

            context = None
            options = {}

            # Process context and options from other args
            for key, value in args.items():
                if key == "arg0":
                    # Skip prompt, handled above
                    continue
                elif key == "context":
                    # Handle context special case
                    if isinstance(value, Identifier):
                        context = [value]
                    elif isinstance(value, list):
                        context = value
                    elif hasattr(value, "literal") and isinstance(value.literal.value, list):
                        # Handle array literal
                        context = value.literal.value
                else:
                    # Other options
                    options[key] = value

            # If options is empty, set it to None
            if not options:
                options = None

            # Create and return a ReasonStatement instead of a FunctionCall
            return ReasonStatement(prompt=prompt, target=None, context=context, options=options)

        return FunctionCall(name=name, args=args)

    def arg_list(self, items):
        """Transform an argument list into a list of arguments."""
        return items

    def positional_args(self, items):
        """Transform positional arguments into a list."""
        return items

    def named_args(self, items):
        """Transform named arguments into a list of tuples."""
        return items

    def named_arg(self, items):
        """Transform a named argument into a tuple of (name, value)."""
        name = items[0].value
        value = items[1]
        return (name, value)

    def expression(self, items):
        """Transform an expression rule into an Expression node."""
        # Pass through to the or_expr rule
        return items[0]

    def or_expr(self, items):
        """Transform an or expression into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Build a left-associative tree of binary expressions
        result = items[0]
        for i in range(1, len(items)):
            result = BinaryExpression(left=result, operator=BinaryOperator.OR, right=items[i])
        return result

    def and_expr(self, items):
        """Transform an and expression into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Build a left-associative tree of binary expressions
        result = items[0]
        for i in range(1, len(items)):
            result = BinaryExpression(left=result, operator=BinaryOperator.AND, right=items[i])
        return result

    def comparison(self, items):
        """Transform a comparison into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Items alternate between expressions and operators
        result = items[0]
        for i in range(1, len(items), 2):
            operator = self._get_binary_operator(items[i].value)
            right = items[i + 1]
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def comp_op(self, items):
        """Transform a comparison operator token into a string."""
        return items[0]

    def EQ(self, _):
        return Token("COMP_OP", "==")

    def NEQ(self, _):
        return Token("COMP_OP", "!=")

    def LT(self, _):
        return Token("COMP_OP", "<")

    def GT(self, _):
        return Token("COMP_OP", ">")

    def LTE(self, _):
        return Token("COMP_OP", "<=")

    def GTE(self, _):
        return Token("COMP_OP", ">=")

    def sum_expr(self, items):
        """Transform a sum expression into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Items alternate between expressions and operators
        result = items[0]
        for i in range(1, len(items), 2):
            operator = self._get_binary_operator(items[i].value)
            right = items[i + 1]
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def add_op(self, items):
        """Transform an addition operator token into a string."""
        return items[0]

    def PLUS(self, _):
        return Token("ADD_OP", "+")

    def MINUS(self, _):
        return Token("ADD_OP", "-")

    def product(self, items):
        """Transform a product expression into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Items alternate between expressions and operators
        result = items[0]
        for i in range(1, len(items), 2):
            operator = self._get_binary_operator(items[i].value)
            right = items[i + 1]
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def mul_op(self, items):
        """Transform a multiplication operator token into a string."""
        return items[0]

    def MULT(self, _):
        return Token("MUL_OP", "*")

    def DIV(self, _):
        return Token("MUL_OP", "/")

    def MOD(self, _):
        return Token("MUL_OP", "%")

    def atom(self, items):
        """Transform an atom rule into an Expression node."""
        return items[0]

    def TRUE(self, _):
        """Transform a TRUE token into a LiteralExpression with value True."""
        return LiteralExpression(literal=Literal(value=True))

    def FALSE(self, _):
        """Transform a FALSE token into a LiteralExpression with value False."""
        return LiteralExpression(literal=Literal(value=False))

    def array_literal(self, items):
        """Transform an array literal into a LiteralExpression node."""
        # If empty array, return empty list
        if len(items) == 0:
            return LiteralExpression(literal=Literal(value=[]))

        # If we have array items, extract them
        array_items = items[0] if len(items) > 0 else []

        # Convert to a Literal node with a list value
        return LiteralExpression(literal=Literal(value=array_items))

    def array_items(self, items):
        """Transform array items into a list."""
        return items

    def identifier(self, items):
        """Transform an identifier rule into an Identifier node."""
        # Join parts with dots for nested identifiers (e.g., "a.b.c")
        if len(items) == 1:
            name = items[0].value
        else:
            name = ".".join(item.value for item in items)
        return Identifier(name=name)

    def literal(self, items):
        """Transform a literal rule into a LiteralExpression node."""
        return LiteralExpression(literal=self._create_literal(items[0]))

    def f_string(self, items):
        """Transform an f-string rule into a LiteralExpression node with FStringExpression."""
        # Remove the 'f' and quotes
        s = items[0].value
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]  # Remove quotes
        elif s.startswith("'") and s.endswith("'"):
            s = s[1:-1]  # Remove quotes

        # Parse f-string for {expression} placeholders
        parts = []
        current_text = ""
        i = 0
        while i < len(s):
            if s[i] == "{" and (i == 0 or s[i - 1] != "\\"):
                # Found start of expression
                if current_text:
                    parts.append(current_text)
                    current_text = ""

                # Find the matching closing brace
                brace_level = 1
                start_idx = i + 1
                expr_text = ""

                i += 1
                while i < len(s) and brace_level > 0:
                    if s[i] == "{" and s[i - 1] != "\\":
                        brace_level += 1
                    elif s[i] == "}" and s[i - 1] != "\\":
                        brace_level -= 1

                    if brace_level > 0:
                        expr_text += s[i]

                    i += 1

                if expr_text:
                    expr_text = expr_text.strip()

                    # Handle complex expressions and operations
                    if "+" in expr_text:
                        # Simple addition
                        left, right = expr_text.split("+", 1)
                        left = left.strip()
                        right = right.strip()
                        left_expr = (
                            Identifier(name=left) if "." in left or left.isalnum() else LiteralExpression(literal=self._parse_literal(left))
                        )
                        right_expr = (
                            Identifier(name=right)
                            if "." in right or right.isalnum()
                            else LiteralExpression(literal=self._parse_literal(right))
                        )
                        parts.append(BinaryExpression(left=left_expr, operator=BinaryOperator.ADD, right=right_expr))
                    elif "-" in expr_text and not expr_text.startswith("-"):
                        # Simple subtraction (not negative number)
                        left, right = expr_text.split("-", 1)
                        left = left.strip()
                        right = right.strip()
                        left_expr = (
                            Identifier(name=left) if "." in left or left.isalnum() else LiteralExpression(literal=self._parse_literal(left))
                        )
                        right_expr = (
                            Identifier(name=right)
                            if "." in right or right.isalnum()
                            else LiteralExpression(literal=self._parse_literal(right))
                        )
                        parts.append(BinaryExpression(left=left_expr, operator=BinaryOperator.SUBTRACT, right=right_expr))
                    elif "*" in expr_text:
                        # Simple multiplication
                        left, right = expr_text.split("*", 1)
                        left = left.strip()
                        right = right.strip()
                        left_expr = (
                            Identifier(name=left) if "." in left or left.isalnum() else LiteralExpression(literal=self._parse_literal(left))
                        )
                        right_expr = (
                            Identifier(name=right)
                            if "." in right or right.isalnum()
                            else LiteralExpression(literal=self._parse_literal(right))
                        )
                        parts.append(BinaryExpression(left=left_expr, operator=BinaryOperator.MULTIPLY, right=right_expr))
                    elif "/" in expr_text:
                        # Simple division
                        left, right = expr_text.split("/", 1)
                        left = left.strip()
                        right = right.strip()
                        left_expr = (
                            Identifier(name=left) if "." in left or left.isalnum() else LiteralExpression(literal=self._parse_literal(left))
                        )
                        right_expr = (
                            Identifier(name=right)
                            if "." in right or right.isalnum()
                            else LiteralExpression(literal=self._parse_literal(right))
                        )
                        parts.append(BinaryExpression(left=left_expr, operator=BinaryOperator.DIVIDE, right=right_expr))
                    else:
                        # Default to identifier
                        parts.append(Identifier(name=expr_text))

            else:
                current_text += s[i]
                i += 1

        if current_text:
            parts.append(current_text)

        # For a more reliable solution, add a special marker for the original string
        # This works better with our interpreter's visit_fstring_expression method
        if not parts:
            parts = [f"F-STRING-PLACEHOLDER:{s}"]
        elif len(parts) == 1 and isinstance(parts[0], str):
            # Very likely we have a simple string that needs variable substitution
            parts = [f"F-STRING-PLACEHOLDER:{s}"]

        # Create the f-string expression
        fstring_expr = FStringExpression(parts=parts)

        # For reason statements especially, ensure we have a proper f-string expression
        # Set a special flag attribute to help with proper evaluation
        setattr(fstring_expr, "_is_fstring", True)
        setattr(fstring_expr, "_original_text", s)

        return LiteralExpression(literal=Literal(value=fstring_expr))

    def _parse_literal(self, text):
        """Parse a simple literal value from text."""
        text = text.strip()

        # Try numbers first
        try:
            if "." in text:
                return Literal(value=float(text))
            else:
                return Literal(value=int(text))
        except ValueError:
            pass

        # Try boolean
        if text.lower() == "true":
            return Literal(value=True)
        elif text.lower() == "false":
            return Literal(value=False)

        # Try string (with quotes)
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            return Literal(value=text[1:-1])

        # Default to string
        return Literal(value=text)

    def _create_literal(self, token):
        """Create a Literal node from a token."""
        token_type = token.type
        value = token.value

        if token_type == "STRING":
            # Remove quotes (either single or double)
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            return Literal(value=value)
        elif token_type == "NUMBER":
            # Check if it's an integer or float
            if "." in value:
                return Literal(value=float(value))
            else:
                return Literal(value=int(value))
        elif token_type == "BOOL":
            return Literal(value=value.lower() == "true")
        elif value == "null":
            return Literal(value=None)

        # Fallback
        return Literal(value=value)

    def _get_binary_operator(self, op_str):
        """Convert an operator string to a BinaryOperator enum value."""
        op_map = {
            "+": BinaryOperator.ADD,
            "-": BinaryOperator.SUBTRACT,
            "*": BinaryOperator.MULTIPLY,
            "/": BinaryOperator.DIVIDE,
            "%": BinaryOperator.MODULO,
            "<": BinaryOperator.LESS_THAN,
            ">": BinaryOperator.GREATER_THAN,
            "<=": BinaryOperator.LESS_EQUALS,
            ">=": BinaryOperator.GREATER_EQUALS,
            "==": BinaryOperator.EQUALS,
            "!=": BinaryOperator.NOT_EQUALS,
            "and": BinaryOperator.AND,
            "or": BinaryOperator.OR,
        }

        return op_map.get(op_str, BinaryOperator.EQUALS)  # Default to equals if unknown


class GrammarParser:
    """Grammar-based parser for DANA language.

    Uses Lark to parse DANA programs into AST nodes based on a formal grammar.
    """

    def __init__(self):
        """Initialize the parser with the DANA grammar."""
        # Path to the grammar file (relative to this file)
        grammar_path = Path(__file__).parent / "dana_grammar.lark"

        if not grammar_path.exists():
            # If grammar file doesn't exist, use the embedded grammar
            # This is useful for testing without requiring the external file
            from . import dana_grammar_embedded

            self.grammar = dana_grammar_embedded.GRAMMAR
        else:
            # Load grammar from file
            with open(grammar_path) as f:
                self.grammar = f.read()

        # Only create parser if Lark is available
        self.parser = None
        self.transformer = None

        if LARK_AVAILABLE:
            try:
                # Create the parser with the DanaIndenter
                self.parser = Lark(
                    self.grammar,
                    parser="lalr",
                    postlex=DanaIndenter(),
                    start="start",
                    # Enable better error reporting and recovery
                    debug=True,
                )

                # Create the transformer
                self.transformer = DanaTransformer()
            except Exception as e:
                logger.error(f"Failed to initialize Lark parser: {e}")

    def is_available(self) -> bool:
        """Check if the Lark parser is available and initialized."""
        return LARK_AVAILABLE and self.parser is not None

    def parse(self, program_text: str) -> ParseResult:
        """Parse a DANA program string into an AST.

        Args:
            program_text: The program text to parse

        Returns:
            A ParseResult containing the parsed program and any errors
        """
        if not self.is_available():
            return ParseResult(
                program=Program(statements=[]), errors=[ParseError("Lark parser is not available. Install with 'pip install lark-parser'")]
            )

        errors = []

        try:
            # Parse the program
            parse_tree = self.parser.parse(program_text)

            # Transform the parse tree into AST nodes
            program = self.transformer.transform(parse_tree)

            # Set the source text on the program
            program.source_text = program_text

            return ParseResult(program=program, errors=errors)

        except UnexpectedInput as e:
            # Create a detailed error message with location information
            error_line = program_text.split("\n")[e.line - 1] if e.line > 0 and e.line <= len(program_text.split("\n")) else ""

            # Improve error position reporting for assignment errors
            column = e.column
            adjusted_message = e.get_context(program_text)

            # If there's an equals sign in the line and error is after it
            if "=" in error_line:
                equals_pos = error_line.find("=")
                if column > equals_pos and "#" in error_line[equals_pos:]:
                    # It's likely a missing expression after equals sign
                    # Adjust the error position to just after the equals sign
                    comment_pos = error_line.find("#", equals_pos)
                    if comment_pos > equals_pos and (comment_pos - equals_pos <= 3):
                        column = equals_pos + 1
                        adjusted_message = error_line + "\n" + " " * equals_pos + "^ Missing expression after equals sign"

            error_msg = f"Syntax error at line {e.line}, column {column}: {adjusted_message}"
            errors.append(ParseError(error_msg, e.line, error_line))

            # Create an empty program as a fallback
            empty_program = Program(statements=[], source_text=program_text)
            return ParseResult(program=empty_program, errors=errors)

        except LarkError as e:
            # Handle other Lark errors
            errors.append(ParseError(f"Parsing error: {str(e)}", 0, program_text.split("\n")[0] if program_text else ""))

            # Create an empty program as a fallback
            empty_program = Program(statements=[], source_text=program_text)
            return ParseResult(program=empty_program, errors=errors)

        except Exception as e:
            # Handle any other errors
            errors.append(ParseError(f"Unexpected error during parsing: {str(e)}", 0, program_text.split("\n")[0] if program_text else ""))

            # Create an empty program as a fallback
            empty_program = Program(statements=[], source_text=program_text)
            return ParseResult(program=empty_program, errors=errors)


# Import for type checking
from opendxa.dana.language.type_checker import check_types

# Create a singleton instance of the grammar parser
_parser = GrammarParser()


def parse(code: str, type_check: bool = None) -> ParseResult:
    """Parse a DANA program string into an AST.

    Args:
        code: The DANA code to parse
        type_check: Whether to perform type checking. If None, uses the environment default.

    Returns:
        A ParseResult containing the parsed program and any errors
    """
    # Resolve type checking flag
    do_type_check = ENABLE_TYPE_CHECK if type_check is None else type_check

    if not _parser.is_available():
        logger.error("Parser is not available. Please install the lark-parser package.")
        return ParseResult(
            program=Program(statements=[]), errors=[ParseError("Parser is not available. Please install the lark-parser package.")]
        )

    # Pre-check for common syntax errors
    lines = code.split("\n")
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # Skip empty lines and comments
        if not line_stripped or line_stripped.startswith("#"):
            continue

        # Check for assignment with missing expression
        if "=" in line_stripped and not line_stripped.endswith(":"):
            pos = line.find("=")
            rest = line[pos + 1 :].strip()
            if not rest or rest.startswith("#"):
                # Found a missing expression
                error_msg = f"Syntax error at line {i+1}, column {pos+2}: Missing expression after equals sign"
                error_line = line + "\n" + " " * pos + "^ Missing expression here"
                return ParseResult(program=Program(statements=[], source_text=code), errors=[ParseError(error_msg, i + 1, line)])

    # Parse the code
    result = _parser.parse(code)

    # Perform type checking if enabled and parsing was successful
    if do_type_check and result.is_valid:
        type_errors = check_types(result.program)
        if type_errors:
            # Add type errors to the result
            result = ParseResult(program=result.program, errors=list(result.errors) + type_errors)

    return result
