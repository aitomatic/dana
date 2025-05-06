"""DANA Abstract Syntax Tree (AST) nodes.

This module defines the AST nodes used to represent DANA programs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# Forward references not strictly needed for Iteration 1 AST structure itself
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from opendxa.dana.state.context import RuntimeContext
#     from opendxa.dana.runtime.interpreter import Interpreter

# Forward references for type hints
Expression = Union["LiteralExpression", "Identifier", "BinaryExpression", "FunctionCall"]
Statement = Union["Assignment", "LogStatement", "Conditional", "WhileLoop", "LogLevelSetStatement", "ReasonStatement", "FunctionCall", "PrintStatement"]


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

    value: Union[int, float, str, bool, None, "FStringExpression", List[Any]]
    location: Optional[Location] = None
    
    @property
    def type(self):
        """Get the type of this literal.
        
        This is used during type checking to determine the type of literals.
        """
        # Need to check bool first since True and False are also instances of int
        if isinstance(self.value, bool):
            return "bool"
        elif isinstance(self.value, str):
            return "string"
        elif isinstance(self.value, int):
            return "int"
        elif isinstance(self.value, float):
            return "float"
        elif self.value is None:
            return "null"
        elif hasattr(self.value, "__class__") and self.value.__class__.__name__ == "FStringExpression":
            return "string"
        elif isinstance(self.value, list):
            return "array"
        else:
            return "any"


@dataclass
class LiteralExpression:
    """Represents a literal expression in DANA."""

    literal: Literal
    location: Optional[Location] = None
    
    @property
    def value(self):
        """Get the value of this literal expression.
        
        This is a convenience property that delegates to the literal's value.
        """
        return None if self.literal is None else self.literal.value
    
    @property
    def type(self):
        """Get the type of this literal expression.
        
        This is used during type checking to determine the type of literals.
        """
        if self.literal is None:
            return None
            
        value = self.literal.value
        
        # Need to check bool first since True and False are also instances of int
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif value is None:
            return "null"
        elif hasattr(value, "__class__") and value.__class__.__name__ == "FStringExpression":
            return "string"
        elif isinstance(value, list):
            return "array"
        else:
            return "any"


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
class PrintStatement:
    """Represents a print statement in DANA."""

    message: Expression
    location: Optional[Location] = None


@dataclass
class Conditional:
    """Represents a conditional statement in DANA."""

    condition: Expression
    body: List[Union[Assignment, LogStatement, "Conditional", "WhileLoop", "LogLevelSetStatement", "ReasonStatement", FunctionCall]]
    line_num: int  # Line number where this conditional was defined
    location: Optional[Location] = None
    else_body: List[Union[Assignment, LogStatement, "Conditional", "WhileLoop", "LogLevelSetStatement", "ReasonStatement", FunctionCall]] = field(default_factory=list)


@dataclass
class WhileLoop:
    """Represents a while loop statement in DANA."""

    condition: Expression
    body: List[Union[Assignment, LogStatement, "Conditional", "WhileLoop", "LogLevelSetStatement", "ReasonStatement", FunctionCall]]
    line_num: int  # Line number where this while loop was defined
    location: Optional[Location] = None


@dataclass
class LogLevelSetStatement:
    """Represents a log level setting statement in DANA."""

    level: LogLevel
    location: Optional[Location] = None


@dataclass
class ReasonStatement:
    """Represents a reasoning statement in DANA.
    
    This statement calls the LLM to reason about the provided prompt,
    optionally accessing contextual data from the DANA state.
    """

    prompt: Expression  # The reasoning prompt - can be a string literal or an expression
    context: Optional[List[Identifier]] = None  # Optional list of context variables to include
    target: Optional[Identifier] = None  # Optional target variable to store the result
    options: Optional[Dict[str, Any]] = None  # Additional options like temperature, format, etc.
    location: Optional[Location] = None


# --- Program Structure ---
@dataclass
class Program:
    """Represents a complete DANA program."""

    statements: List[Union[Assignment, LogStatement, Conditional, WhileLoop, ReasonStatement, LogLevelSetStatement, FunctionCall]]
    source_text: str = ""  # Store the original program text
    location: Optional[Location] = None

    def __init__(self, statements, source_text: str = ""):
        self.statements = statements
        self.source_text = source_text
