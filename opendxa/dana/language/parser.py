"""Grammar-based parser for DANA language.

This module provides a robust parser for DANA using the Lark parsing library.
It offers good extensibility, error reporting, and maintainability.

The parser uses a modular design with specialized transformer components
for different language constructs, improving maintainability and testability.
"""

import logging
import os
from pathlib import Path
from typing import List, NamedTuple, Optional

try:
    from lark import Lark, Token, Tree
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
    
    class Indenter:
        pass
    
    class LarkError(Exception):
        pass
    
    class UnexpectedInput(Exception):
        pass

from opendxa.dana.exceptions import ParseError
from opendxa.dana.language.ast import Program
from opendxa.dana.language.error_utils import handle_parse_error
from opendxa.dana.language.transformer_module import get_transformer_class

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
                    debug=True,
                )
                
                # Get the transformer from the modular implementation
                TransformerClass = get_transformer_class()
                self.transformer = TransformerClass()
                logger.debug(f"Using transformer class: {TransformerClass.__name__}")
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
                program=Program(statements=[]), 
                errors=[ParseError("Lark parser is not available. Install with 'pip install lark-parser'")]
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
            # Use error handling utility
            empty_program, errors = handle_parse_error(e, program_text)
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
            program=Program(statements=[]), 
            errors=[ParseError("Parser is not available. Please install the lark-parser package.")]
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
                return ParseResult(
                    program=Program(statements=[], source_text=code), 
                    errors=[ParseError(error_msg, i + 1, line)]
                )
    
    # Parse the code
    result = _parser.parse(code)
    
    # Perform type checking if enabled and parsing was successful
    if do_type_check and result.is_valid:
        type_errors = check_types(result.program)
        if type_errors:
            # Add type errors to the result
            result = ParseResult(program=result.program, errors=list(result.errors) + type_errors)
    
    return result