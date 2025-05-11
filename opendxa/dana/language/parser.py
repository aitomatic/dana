"""Grammar-based parser for DANA language.

This module provides a robust parser for DANA using the Lark parsing library.
It offers good extensibility, error reporting, and maintainability.

The parser uses a modular design with specialized transformer components
for different language constructs, improving maintainability and testability.
"""

import os
from pathlib import Path
from typing import NamedTuple, Optional, Sequence

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
from opendxa.dana.common.exceptions import ParseError
from opendxa.dana.language.ast import (
    Identifier,
    Program,
)
from opendxa.dana.language.error_utils import ErrorUtils
from opendxa.dana.language.transformer_module import get_transformer_class
from opendxa.dana.language.type_checker import TypeChecker, TypeEnvironment

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


class GrammarParser(Loggable):
    """Grammar-based parser for DANA language.

    Uses Lark to parse DANA programs into AST nodes based on a formal grammar.
    """

    def __init__(self):
        """Initialize the parser with the DANA grammar."""
        # Initialize Loggable
        super().__init__()

        # Initialize type environment
        self.type_environment = TypeEnvironment()

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

    def parse(self, program_text: str, type_check: Optional[bool] = None) -> ParseResult:
        """Parse a DANA program string into an AST.

        Args:
            program_text: The program text to parse
            type_check: Whether to perform type checking. If None, uses the environment default.

        Returns:
            A ParseResult containing the parsed program and any errors
        """
        errors: list[ParseError] = []

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
            result = ParseResult(program=program, errors=errors)

            # Perform type checking if enabled and parsing was successful
            do_type_check = ENABLE_TYPE_CHECK if type_check is None else bool(type_check)
            if do_type_check and result.is_valid:
                TypeChecker.check_types(program)

            return result

        except UnexpectedInput as e:
            # Use error handling utility
            self.debug(f"Unexpected input during parsing: {str(e)}")
            empty_program, errors = ErrorUtils.handle_parse_error(e, program_text)
            return ParseResult(program=empty_program, errors=errors)

        except LarkError as e:
            # Handle other Lark errors
            self.debug(f"Lark parsing error: {str(e)}")
            empty_program, errors = ErrorUtils.handle_parse_error(e, program_text)
            return ParseResult(program=empty_program, errors=errors)

        except Exception as e:
            # Handle any other errors
            self.error(f"Unexpected error during parsing: {str(e)}")
            empty_program, errors = ErrorUtils.handle_parse_error(e, program_text)
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
