"""Grammar-based parser for DANA language.

This module provides a robust parser for DANA using the Lark parsing library.
It offers good extensibility, error reporting, and maintainability.

The parser uses a modular design with specialized transformer components
for different language constructs, improving maintainability and testability.
"""

from ast import parse
import os
from pathlib import Path
from typing import Any, NamedTuple, Sequence

from lark.indenter import PythonIndenter

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.parser.transformers.dana_transformer import DanaTransformer

try:
    from lark import Lark, Tree

    LARK_AVAILABLE = True
except ImportError:
    raise ImportError("The lark-parser package is required. Install it with 'pip install lark-parser'")

# Create a shared logger for the parser module
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.common.exceptions import ParseError
from opendxa.dana.parser.ast import (
    Identifier,
    Program,
)
from opendxa.dana.parser.type_checker import TypeChecker, TypeEnvironment

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


class DanaIndenter(PythonIndenter):
    """Custom indenter for DANA language."""

    NL_type = "_NL"
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"


class DanaParser(Lark, Loggable):
    """Grammar-based parser for DANA language.

    Uses Lark to parse DANA programs into AST nodes based on a formal grammar.
    """

    def __init__(self):
        """Initialize the parser with the DANA grammar."""
        # Initialize type environment
        self.type_environment = TypeEnvironment()

        # Path to the grammar file (relative to this file)
        grammar_path = Path(__file__).parent / "dana_grammar.lark"

        if not grammar_path.exists():
            # If grammar file doesn't exist, use the embedded grammar
            raise FileNotFoundError(f"Grammar file not found: {grammar_path}")

        # Load grammar from file
        with open(grammar_path) as f:
            self.grammar = f.read()
        self.debug(f"Loaded grammar from {grammar_path}")

        super().__init__(
            grammar=self.grammar,
            parser="lalr",
            postlex=DanaIndenter(),
            start="program",
            lexer="contextual",
            debug=False,
        )

        self.transformer = DanaTransformer()
        self.program_text = ""

    def parse(self, program_text: str, do_transform: bool = False, do_type_check: bool = False) -> Any:
        """Parse a DANA program string into an AST.

        Args:
            program_text: The program text to parse
            do_transform: Whether to perform transformation.
            do_type_check: Whether to perform type checking.

        Returns:
            A parse tree
        """

        # Make sure the program text ends with a newline
        if not program_text.endswith("\n"):
            program_text += "\n"

        self.program_text = program_text
        parse_tree = super().parse(program_text)  # a parse tree
        if do_transform:
            ast = self.transform(parse_tree, do_type_check)
            return ast
        else:
            return parse_tree

    def transform(self, parse_tree: Tree, do_type_check: bool = False) -> Program:
        """Transform a parse tree into an AST."""
        # Transform the parse tree into AST nodes
        self.debug("Transforming parse tree to AST")
        ast = self.transformer.transform(parse_tree)

        # Set the source text on the program
        ast.source_text = self.program_text

        self.debug(f"Successfully parsed program with {len(ast.statements)} statements")

        # Perform type checking if enabled and parsing was successful
        if do_type_check and ast.is_valid:
            TypeChecker.check_types(ast)

        return ast

    def _deprecated_transform_identifier(self, node: Tree) -> Identifier:
        """Transform an identifier node.

        Args:
            node: The identifier node to transform

        Returns:
            The transformed identifier
        """
        name = str(node.children[0])
        return Identifier(name=name, location=self._get_location(node))
