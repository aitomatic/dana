"""Parser implementation for DANA using Lark.

This module provides an alternative parser for DANA based on Lark grammar.
It can be used instead of the regex-based parser for better extensibility.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

# Note: Lark would need to be added as a dependency
try:
    import lark
    from lark import Lark, Token, Tree
    from lark.exceptions import LarkError, UnexpectedInput
    LARK_AVAILABLE = True
except ImportError:
    # Define compatibility stubs so the module can load without Lark
    LARK_AVAILABLE = False
    class Token: pass
    class Tree: pass
    class Lark: pass
    class LarkError(Exception): pass
    class UnexpectedInput(Exception): pass

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
    Program,
)
from opendxa.dana.language.parser import ParseResult
from opendxa.dana.language.types import validate_identifier

# Feature flag for enabling Lark parser
USE_LARK_PARSER = False

# DANA Grammar in Lark format
DANA_GRAMMAR = r"""
    ?start: program
    
    program: statement*
    
    ?statement: assignment
              | log_statement
              | log_level_statement
              | conditional
    
    assignment: identifier "=" expression
    
    log_statement: "log" ["." log_level] "(" expression ")"
    
    log_level_statement: "log.setLevel" "(" STRING ")"
    
    conditional: "if" expression ":" statement_block
    
    statement_block: _NEWLINE _INDENT statement+ _DEDENT
    
    ?expression: literal
               | identifier
               | binary_expr
               | function_call
               | "(" expression ")"
    
    binary_expr: expression binary_op expression
    
    function_call: IDENTIFIER "(" [arguments] ")"
    
    arguments: argument ("," argument)*
    
    argument: IDENTIFIER "=" expression
    
    binary_op: "+"  -> add
             | "-"  -> subtract
             | "*"  -> multiply
             | "/"  -> divide
             | "==" -> equals
             | "!=" -> not_equals
             | "<"  -> less_than
             | ">"  -> greater_than
             | "<=" -> less_equals
             | ">=" -> greater_equals
             | "and" -> and_op
             | "or"  -> or_op
             | "in"  -> in_op
    
    ?literal: NUMBER           -> number
           | STRING            -> string
           | BOOLEAN           -> boolean
           | f_string          -> f_string
    
    identifier: qualified_name
    
    qualified_name: IDENTIFIER ("." IDENTIFIER)*
    
    f_string: "f" STRING
    
    log_level: "debug" | "info" | "warn" | "error"
    
    BOOLEAN: "true" | "false"
    
    // Terminals
    NUMBER: /-?\d+(\.\d+)?/
    STRING: /"[^"]*"|'[^']*'/
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
    
    // Imports
    %import common.WS
    %import common.NEWLINE -> _NEWLINE
    %import common.INDENT -> _INDENT
    %import common.DEDENT -> _DEDENT
    
    // Ignore whitespace
    %ignore WS
    // Ignore comments
    %ignore /\s*#[^\n]*/
"""


class LarkParser:
    """Parser for DANA based on Lark.
    
    This parser uses the Lark parsing library to parse DANA programs into AST nodes.
    It serves as an alternative to the regex-based parser for better extensibility.
    """
    
    def __init__(self):
        """Initialize the Lark parser if available."""
        self._parser = None
        if LARK_AVAILABLE:
            try:
                self._parser = Lark(DANA_GRAMMAR, parser="lalr", lexer="contextual")
            except Exception as e:
                print(f"Failed to initialize Lark parser: {e}")
    
    def is_available(self) -> bool:
        """Check if the Lark parser is available.
        
        Returns:
            True if Lark is installed and the parser is initialized, False otherwise
        """
        return LARK_AVAILABLE and self._parser is not None
    
    def parse(self, code: str) -> ParseResult:
        """Parse a DANA program string into an AST.
        
        Args:
            code: The DANA program to parse
            
        Returns:
            A ParseResult containing the parsed program and any errors
            
        Raises:
            ImportError: If Lark is not installed
        """
        if not LARK_AVAILABLE:
            raise ImportError("Lark is not installed. Install it with 'pip install lark'.")
        
        if not self._parser:
            return ParseResult(
                program=Program(statements=[]), 
                errors=[ParseError("Lark parser is not initialized")]
            )
        
        try:
            # Parse the program with Lark
            parse_tree = self._parser.parse(code)
            
            # Transform the Lark parse tree into a DANA AST
            program = self._transform_tree_to_ast(parse_tree)
            
            return ParseResult(program=program)
        except LarkError as e:
            # Handle parsing errors and convert to DANA ParseError
            if isinstance(e, UnexpectedInput):
                line, col = e.line, e.column
                error_msg = f"Syntax error at line {line}, column {col}: {e}"
                return ParseResult(
                    program=Program(statements=[]),
                    errors=[ParseError(error_msg, line, code.splitlines()[line-1] if line <= len(code.splitlines()) else "")]
                )
            else:
                return ParseResult(
                    program=Program(statements=[]),
                    errors=[ParseError(f"Parsing error: {e}")]
                )
    
    def _transform_tree_to_ast(self, tree: Tree) -> Program:
        """Transform a Lark parse tree into a DANA AST.
        
        Args:
            tree: The Lark parse tree to transform
            
        Returns:
            A DANA Program AST node
        """
        # For now, return an empty program - the actual transformation would be implemented here
        # This is a placeholder for the real implementation
        return Program(statements=[])


# Create a singleton parser
_lark_parser = LarkParser()


def parse_with_lark(code: str) -> ParseResult:
    """Parse a DANA program string using the Lark parser.
    
    Args:
        code: The DANA program to parse
        
    Returns:
        A ParseResult containing the parsed program and any errors
    """
    if not _lark_parser.is_available():
        from opendxa.dana.language.parser import parse as regex_parse
        return regex_parse(code)
    
    return _lark_parser.parse(code)


def parse(code: str) -> ParseResult:
    """Parse a DANA program string, using either Lark or regex-based parser.
    
    Args:
        code: The DANA program to parse
        
    Returns:
        A ParseResult containing the parsed program and any errors
    """
    if USE_LARK_PARSER:
        return parse_with_lark(code)
    else:
        from opendxa.dana.language.parser import parse as regex_parse
        return regex_parse(code)