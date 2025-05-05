"""DANA Abstract Syntax Tree (AST) nodes.

This module defines the AST nodes used to represent DANA programs.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# Forward references not strictly needed for Iteration 1 AST structure itself
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from opendxa.dana.state.context import RuntimeContext
#     from opendxa.dana.runtime.interpreter import Interpreter

# Forward references for type hints
Expression = Union["LiteralExpression", "Identifier", "BinaryExpression", "FunctionCall"]
Statement = Union["Assignment", "LogStatement", "Conditional", "WhileLoop", "LogLevelSetStatement"]


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
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"


class LogLevel(Enum):
    """Log levels supported in DANA."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


# Location is stored as (line, column, source_text)
Location = Tuple[int, int, str]


# --- Literals and Identifiers ---
@dataclass
class Literal:
    """Represents a literal value in DANA."""

    value: Union[int, float, str, bool, None, "FStringExpression"]
    location: Optional[Location] = None


@dataclass
class LiteralExpression:
    """Represents a literal expression in DANA."""

    literal: Literal
    location: Optional[Location] = None


@dataclass
class FStringExpression:
    """Represents an f-string expression in DANA."""

    parts: List[Union[str, Expression]]  # Either literal strings or expressions to evaluate
    location: Optional[Location] = None


@dataclass
class Identifier:
    """Represents an identifier in DANA."""

    name: str
    location: Optional[Location] = None


# --- Expressions ---
@dataclass
class FunctionCall:
    """Represents a function call in DANA."""

    name: str
    args: Dict[str, Any]
    location: Optional[Location] = None


@dataclass
class BinaryExpression:
    """Represents a binary expression in DANA."""

    left: Union[LiteralExpression, Identifier, "BinaryExpression", FunctionCall]
    operator: BinaryOperator
    right: Union[LiteralExpression, Identifier, "BinaryExpression", FunctionCall]
    location: Optional[Location] = None


# --- Statements ---
@dataclass
class Assignment:
    """Represents an assignment statement in DANA."""

    target: Identifier
    value: Union[LiteralExpression, Identifier, BinaryExpression, FunctionCall]
    location: Optional[Location] = None


@dataclass
class LogStatement:
    """Represents a log statement in DANA."""

    message: Union[LiteralExpression, Identifier, BinaryExpression, FunctionCall]
    level: LogLevel = LogLevel.INFO  # Default to INFO level
    location: Optional[Location] = None


@dataclass
class Conditional:
    """Represents a conditional statement in DANA."""

    condition: Expression
    body: List[Union[Assignment, LogStatement, "Conditional", "WhileLoop", "LogLevelSetStatement"]]
    line_num: int  # Line number where this conditional was defined
    location: Optional[Location] = None


@dataclass
class WhileLoop:
    """Represents a while loop statement in DANA."""

    condition: Expression
    body: List[Union[Assignment, LogStatement, "Conditional", "WhileLoop", "LogLevelSetStatement"]]
    line_num: int  # Line number where this while loop was defined
    location: Optional[Location] = None


@dataclass
class LogLevelSetStatement:
    """Represents a log level setting statement in DANA."""

    level: LogLevel
    location: Optional[Location] = None


# --- Program Structure ---
@dataclass
class Program:
    """Represents a complete DANA program."""

    statements: List[Union[Assignment, LogStatement, Conditional, WhileLoop]]
    source_text: str = ""  # Store the original program text
    location: Optional[Location] = None

    def __init__(self, statements, source_text: str = ""):
        self.statements = statements
        self.source_text = source_text
