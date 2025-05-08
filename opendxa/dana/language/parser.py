"""Grammar-based parser for DANA language.

This module provides a robust parser for DANA using the Lark parsing library.
It offers good extensibility, error reporting, and maintainability.

The parser uses a modular design with specialized transformer components
for different language constructs, improving maintainability and testability.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, Optional, Sequence

from opendxa.common.mixins.loggable import Loggable

try:
    from lark import Lark, Tree
    from lark.exceptions import LarkError, UnexpectedInput
    from lark.indenter import Indenter

    LARK_AVAILABLE = True
except ImportError:
    raise ImportError("The lark-parser package is required. Install it with 'pip install lark-parser'")

# Create a shared logger for the parser module
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.exceptions import ParseError
from opendxa.dana.language.ast import (
    Identifier,
    Program,
)
from opendxa.dana.language.error_utils import handle_parse_error
from opendxa.dana.language.transformer_module import get_transformer_class
from opendxa.dana.language.type_checker import TypeCheckVisitor, TypeEnvironment
from opendxa.dana.language.visitor import accept

parser_logger = DXA_LOGGER.getLogger("opendxa.dana.language.parser")


class ParseResult(NamedTuple):
    """Result of parsing a DANA program."""

    program: Program
    errors: Sequence[ParseError] = ()

    @property
    def is_valid(self) -> bool:
        """Check if parsing was successful (no errors)."""
        return len(self.errors) == 0


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

    # Token types that should always be accepted
    always_accept = {NL_type, INDENT_type, DEDENT_type}


if TYPE_CHECKING:
    from typing import Optional

    from lark import Tree
    from lark.indenter import Indenter


class GrammarParser(Loggable):
    """Grammar-based parser for DANA language.

    Uses Lark to parse DANA programs into AST nodes based on a formal grammar.
    """

    def __init__(self):
        """Initialize the parser with the DANA grammar."""
        # Initialize Loggable
        super().__init__()

        # Path to the grammar file (relative to this file)
        grammar_path = Path(__file__).parent / "dana_grammar.lark"

        if not grammar_path.exists():
            # If grammar file doesn't exist, use the embedded grammar
            from . import dana_grammar_embedded

            self.grammar = dana_grammar_embedded.GRAMMAR
            self.debug("Using embedded grammar")
        else:
            # Load grammar from file
            with open(grammar_path) as f:
                self.grammar = f.read()
            self.debug(f"Loaded grammar from {grammar_path}")

        # Create parser
        try:
            # Create the parser with the DanaIndenter
            self.parser = Lark(
                self.grammar,  # type: ignore[arg-type]
                parser="lalr",
                postlex=DanaIndenter(),
                start="start",
                debug=False,
            )

            # Get the transformer from the modular implementation
            TransformerClass = get_transformer_class()
            self.transformer = TransformerClass()
            self.debug(f"Using transformer class: {TransformerClass.__name__}")
        except Exception as e:
            self.error(f"Failed to initialize Lark parser: {e}")
            raise

    def parse(self, program_text: str) -> ParseResult:
        """Parse a DANA program string into an AST.

        Args:
            program_text: The program text to parse

        Returns:
            A ParseResult containing the parsed program and any errors
        """
        errors = []

        try:
            # Parse the program
            self.debug("Parsing DANA program text")
            parse_tree = self.parser.parse(program_text)

            # Transform the parse tree into AST nodes
            self.debug("Transforming parse tree to AST")
            program = self.transformer.transform(parse_tree)

            # Set the source text on the program
            program.source_text = program_text

            self.debug(f"Successfully parsed program with {len(program.statements)} statements")
            return ParseResult(program=program, errors=errors)

        except UnexpectedInput as e:
            # Use error handling utility
            self.debug(f"Unexpected input during parsing: {str(e)}")
            empty_program, errors = handle_parse_error(e, program_text)
            return ParseResult(program=empty_program, errors=errors)

        except LarkError as e:
            # Handle other Lark errors
            self.error(f"Lark parsing error: {str(e)}")
            errors.append(ParseError(f"Parsing error: {str(e)}", 0, program_text.split("\n")[0] if program_text else ""))

            # Create an empty program as a fallback
            empty_program = Program(statements=[], source_text=program_text)
            return ParseResult(program=empty_program, errors=errors)

        except Exception as e:
            # Handle any other errors
            self.error(f"Unexpected error during parsing: {str(e)}")
            errors.append(ParseError(f"Unexpected error during parsing: {str(e)}", 0, program_text.split("\n")[0] if program_text else ""))

            # Create an empty program as a fallback
            empty_program = Program(statements=[], source_text=program_text)
            return ParseResult(program=empty_program, errors=errors)

    def transform_identifier(self, node: Tree) -> Identifier:
        """Transform an identifier node.

        Args:
            node: The identifier node to transform

        Returns:
            The transformed identifier
        """
        name = str(node.children[0])
        return Identifier(name=name, location=self._get_location(node))


# Create a persistent type environment
_type_environment = TypeEnvironment()

# Create a singleton instance of the grammar parser
_parser = GrammarParser()


def parse(code: str, type_check: Optional[bool] = None) -> ParseResult:
    """Parse a DANA program string into an AST.

    Args:
        code: The DANA code to parse
        type_check: Whether to perform type checking. If None, uses the environment default.

    Returns:
        A ParseResult containing the parsed program and any errors
    """
    # Resolve type checking flag
    do_type_check = ENABLE_TYPE_CHECK if type_check is None else bool(type_check)

    # Parse the code
    result = _parser.parse(code)

    # Perform type checking if enabled and parsing was successful
    if do_type_check and result.is_valid:
        visitor = TypeCheckVisitor(_type_environment)
        accept(result.program, visitor)
        if visitor.errors:
            # Convert type errors to parse errors
            parse_errors = []
            for error in visitor.errors:
                line = 0
                if hasattr(error, "location") and error.location is not None:
                    line = getattr(error.location, "line", 0)
                parse_errors.append(ParseError(str(error), line))

            # Add type errors to the result
            result = ParseResult(program=result.program, errors=list(result.errors) + parse_errors)

    return result
