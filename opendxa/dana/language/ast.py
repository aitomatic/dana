"""DANA Abstract Syntax Tree (AST) nodes.

This module defines the AST nodes used to represent DANA programs.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Union

# Forward references not strictly needed for Iteration 1 AST structure itself
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from opendxa.dana.state.context import RuntimeContext
#     from opendxa.dana.runtime.interpreter import Interpreter


class BinaryOperator(Enum):
    """Binary operators supported in DANA."""

    EQUALS = "=="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_EQUALS = "<="
    GREATER_EQUALS = ">="
    AND = "and"
    OR = "or"
    IN = "in"


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

    value: Union[int, str, bool]


@dataclass
class LiteralExpression(Expression):
    """Represents a literal expression in DANA."""

    literal: Literal


@dataclass
class Identifier(Expression):
    """Represents an identifier in DANA."""

    name: str


# --- Expressions ---
@dataclass
class BinaryExpression(Expression):
    """Represents a binary expression in DANA."""

    left: Expression
    operator: BinaryOperator
    right: Expression


@dataclass
class FunctionCall(Expression):
    """Represents a function call in DANA."""

    name: str
    args: Dict[str, Any]


# --- Statements ---
@dataclass
class Assignment(Statement):
    """Represents an assignment statement in DANA."""

    target: Identifier
    value: Expression


@dataclass
class LogStatement(Statement):
    """Represents a log statement in DANA."""

    message: LiteralExpression


@dataclass
class Conditional(Statement):
    """Represents a conditional statement in DANA."""

    condition: Expression
    body: List[Statement]


# --- Program Structure ---
@dataclass
class Program(ASTNode):
    """Represents a complete DANA program."""

    statements: List[Statement]

    def __init__(self, statements):
        self.statements = statements
