"""Abstract Syntax Tree (AST) node definitions for the DANA language."""

from typing import List, Union  # Removed Optional, Any, Dict
from dataclasses import dataclass

# Forward references not strictly needed for Iteration 1 AST structure itself
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from opendxa.dana.state.context import RuntimeContext
#     from opendxa.dana.runtime.interpreter import Interpreter

# Base class for all AST nodes (optional, but can be useful)
@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    pass

# --- Base Nodes ---
@dataclass
class Statement(ASTNode):
    """Base class for all statements."""
    pass

@dataclass
class Expression(ASTNode):
    """Base class for all expressions."""
    pass

# --- Literals and Identifiers ---
@dataclass
class Literal:
    """Represents a literal value (string, integer, etc.)."""
    value: Union[str, int]  # Assuming only int and str for now

@dataclass
class LiteralExpression(Expression):
    """Wraps a Literal for use in expressions."""
    literal: Literal

@dataclass
class Identifier:
    """Represents an identifier, potentially with a scope (e.g., 'temp.x')."""
    name: str

# --- Statements ---
@dataclass
class Assignment(Statement):
    """Assigns a value (result of an expression) to a context variable."""
    target: Identifier      # The variable to assign to (e.g., Identifier(name="temp.x"))
    value: Expression       # The value to assign (e.g., LiteralExpression(Literal(value=10)))

@dataclass
class LogStatement(Statement):
    """Represents a log statement: log(message_expression)."""
    # For now, we'll assume the argument is a simple string literal expression
    message: LiteralExpression

# --- Program Structure ---
@dataclass
class Program(ASTNode):
    """Represents a complete DANA program as a sequence of statements."""
    statements: List[Statement]

    def __init__(self, statements):
        self.statements = statements