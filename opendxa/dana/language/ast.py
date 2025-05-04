"""DANA Abstract Syntax Tree (AST) nodes.

This module defines the AST nodes used to represent DANA programs.
"""

from dataclasses import dataclass
from typing import List, Union  # Removed Any, Dict

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
    """Represents a literal value in DANA."""

    value: Union[int, str]


@dataclass
class LiteralExpression(Expression):
    """Represents a literal expression in DANA."""

    literal: Literal


@dataclass
class Identifier:
    """Represents an identifier in DANA."""

    name: str


# --- Statements ---
@dataclass
class Assignment(Statement):
    """Represents an assignment statement in DANA."""

    target: Identifier
    value: LiteralExpression


@dataclass
class LogStatement(Statement):
    """Represents a log statement in DANA."""

    message: LiteralExpression


# --- Program Structure ---
@dataclass
class Program(ASTNode):
    """Represents a complete DANA program."""

    statements: List[Union[Assignment, LogStatement]]

    def __init__(self, statements):
        self.statements = statements
