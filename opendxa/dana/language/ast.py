"""DANA Abstract Syntax Tree (AST) nodes.

This module defines the AST nodes used to represent DANA programs.

A statement is a unit of code that performs an action (e.g., assignment, function call, loop).
An expression is a unit of code that evaluates to a value (e.g., literal, identifier, binary operation).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# Forward references for type hints

#
# An Expression is any node that can be evaluated to a value, e.g.,
# a literal, an identifier, a binary expression, a function call, etc.
#
Expression = Union[
    "LiteralExpression",  # 42, "hello", True, [1, 2, 3]
    "Identifier",  # x, my_function, math
    "BinaryExpression",  # 1 + 2, x * y, a and b
    "FunctionCall",  # my_function(1, 2, 3), math.sqrt(16)
    "FStringExpression",  # f"Hello, {name}!"
    "UnaryExpression",  # -x, not y
    "AttributeAccess",  # obj.attr
    "SubscriptExpression",  # a[0], a["key"]
    "DictLiteral",  # {"key1": "value1", "key2": "value2"}
    "SetLiteral",  # {1, 2, 3}
]

#
# A Statement is any node that performs an action, e.g.,
# an assignment, a conditional, a while loop, a for loop, a try/except block,
# a function definition, an import statement, etc.
#
Statement = Union[
    "Assignment",  # x = 42, y = x + 1
    "Conditional",  # if x > 0: print("Positive") else: print("Negative")
    "WhileLoop",  # while x > 0: x = x - 1
    "ForLoop",  # for i in range(10): print(i)
    "TryBlock",  # try: x = 1 / 0 except ZeroDivisionError as e: print("Error:", e)
    "FunctionDefinition",  # def my_function(x, y): return x + y
    "ImportStatement",  # import math
    "ImportFromStatement",  # from math import sqrt
    "FunctionCall",  # my_function(1, 2, 3)
    "PrintStatement",  # print("Hello, world!")
    "Expression",  # x + y, 42, "hello"
]

# Define a type alias for all AST node types
ASTNode = Union[Expression, Statement]


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


@dataclass(frozen=True)
class Location:
    """Represents a source code location (line, column, source)."""

    line: int
    column: int
    source: str


# --- Literals and Identifiers ---
@dataclass
class LiteralExpression:
    """Represents a literal expression in DANA.

    A literal expression is an expression that evaluates to a constant value.
    Examples:
        - 42 (int)
        - 3.14 (float)
        - "hello" (string)
        - True (bool)
        - None (null)
        - [1, 2, 3] (list)
    """

    value: Union[int, float, str, bool, None, "FStringExpression", List[Any]]
    location: Optional[Location] = None

    @property
    def type(self):
        """Get the type of this literal expression."""
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
class FStringExpression:
    """Represents an f-string expression in DANA.

    An f-string expression is a string literal that can contain embedded expressions.
    Example:
        - f"Hello, {name}!"
    """

    parts: List[Union[str, Expression]]  # Either literal strings or expressions to evaluate
    location: Optional[Location] = None


@dataclass
class Identifier:
    """Represents an identifier in DANA.

    An identifier is a name that refers to a variable, function, or module.
    Example:
        - x
        - my_function
        - math
    """

    name: str
    location: Optional[Location] = None


# --- Expressions ---
@dataclass
class FunctionCall:
    """Represents a function call in DANA.

    A function call is an expression that calls a function with arguments.
    Example:
        - my_function(1, 2, 3)
        - math.sqrt(16)
    """

    name: str
    args: Dict[str, Any]
    location: Optional[Location] = None


@dataclass
class BinaryExpression:
    """Represents a binary expression in DANA.

    A binary expression is an expression that combines two expressions with an operator.
    Example:
        - 1 + 2
        - x * y
        - a and b
    """

    left: Union[LiteralExpression, Identifier, "BinaryExpression", FunctionCall]
    operator: BinaryOperator
    right: Union[LiteralExpression, Identifier, "BinaryExpression", FunctionCall]
    location: Optional[Location] = None


# --- Statements ---
@dataclass
class Assignment:
    """Represents an assignment statement in DANA.

    An assignment statement assigns a value to a variable.
    Example:
        - x = 42
        - y = x + 1
    """

    target: Identifier
    value: Union[LiteralExpression, Identifier, BinaryExpression, FunctionCall]
    location: Optional[Location] = None


@dataclass
class PrintStatement:
    """Represents a print statement in DANA.

    A print statement prints a value to the console.
    Example:
        - print("Hello, world!")
        - print(x)
    """

    message: Expression
    location: Optional[Location] = None


@dataclass
class Conditional:
    """Represents a conditional statement in DANA.

    A conditional statement executes a block of code if a condition is true.
    Example:
        - if x > 0:
              print("Positive")
          else:
              print("Negative")
    """

    condition: Expression
    body: List[Union[Assignment, "Conditional", "WhileLoop", FunctionCall]]
    line_num: int  # Line number where this conditional was defined
    else_body: List[Union[Assignment, "Conditional", "WhileLoop", FunctionCall]] = field(default_factory=list)
    location: Optional[Location] = None


@dataclass
class WhileLoop:
    """Represents a while loop statement in DANA.

    A while loop statement executes a block of code repeatedly while a condition is true.
    Example:
        - while x > 0:
              x = x - 1
    """

    condition: Expression
    body: List[Union[Assignment, "Conditional", "WhileLoop", FunctionCall]]
    line_num: int  # Line number where this while loop was defined
    location: Optional[Location] = None


# --- Unary Expressions ---
@dataclass
class UnaryExpression:
    """Represents a unary expression in DANA."""

    operator: str  # e.g., "-", "not"
    operand: Expression
    location: Optional[Location] = None


# --- Attribute Access ---
@dataclass
class AttributeAccess:
    """Represents an attribute access expression in DANA."""

    object: Expression  # e.g., obj
    attribute: str  # e.g., attr
    location: Optional[Location] = None


# --- Subscript Expressions ---
@dataclass
class SubscriptExpression:
    """Represents a subscript expression in DANA."""

    object: Expression  # e.g., a
    index: Expression  # e.g., 0 or "key"
    location: Optional[Location] = None


# --- Dict and Set Literals ---
@dataclass
class DictLiteral:
    """Represents a dictionary literal in DANA."""

    items: List[Tuple[Expression, Expression]]  # List of (key, value) pairs
    location: Optional[Location] = None


@dataclass
class SetLiteral:
    """Represents a set literal in DANA."""

    items: List[Expression]  # List of items
    location: Optional[Location] = None


# --- Program Structure ---
@dataclass
class Program:
    """Represents a complete DANA program.

    A program is a list of statements.
    Example:
        - x = 42
        - print(x)
    """

    statements: List[Union[Assignment, FunctionCall]]
    source_text: str = ""  # Store the original program text
    location: Optional[Location] = None

    def __init__(self, statements, source_text: str = ""):
        self.statements = statements
        self.source_text = source_text


# --- For Loops ---
@dataclass
class ForLoop:
    """Represents a for loop in DANA.

    A for loop iterates over a sequence (e.g., a list, a range).
    Example:
        - for i in range(10):
              print(i)
    """

    target: Identifier  # e.g., i
    iterable: Expression  # e.g., range(10)
    body: List[Statement]  # List of statements in the loop body
    location: Optional[Location] = None


# --- Try/Except Blocks ---
@dataclass
class TryBlock:
    """Represents a try block in DANA.

    A try block attempts to execute a block of code and handles exceptions.
    Example:
        - try:
              x = 1 / 0
          except ZeroDivisionError as e:
              print("Error:", e)
    """

    body: List[Statement]  # List of statements in the try block
    except_blocks: List["ExceptBlock"]  # List of except blocks
    finally_block: Optional[List[Statement]] = None  # Optional finally block
    location: Optional[Location] = None


@dataclass
class ExceptBlock:
    """Represents an except block in DANA.

    An except block handles exceptions raised in a try block.
    Example:
        - except ZeroDivisionError as e:
              print("Error:", e)
    """

    body: List[Statement]  # List of statements in the except block
    location: Optional[Location] = None
    exception_type: Optional[Identifier] = None  # e.g., ValueError
    exception_name: Optional[Identifier] = None  # e.g., e


# --- Function Definitions ---
@dataclass
class FunctionDefinition:
    """Represents a function definition in DANA.

    A function definition defines a function with a name, parameters, and a body.
    Example:
        - def my_function(x, y):
              return x + y
    """

    name: Identifier  # e.g., my_function
    parameters: List[Identifier]  # List of parameter names
    body: List[Statement]  # List of statements in the function body
    location: Optional[Location] = None


# --- Import Statements ---
@dataclass
class ImportStatement:
    """Represents an import statement in DANA.

    An import statement imports a module.
    Example:
        - import math
        - import math as m
    """

    module: str  # e.g., "math"
    alias: Optional[str] = None  # e.g., "m" for "import math as m"
    location: Optional[Location] = None


@dataclass
class ImportFromStatement:
    """Represents an import from statement in DANA.

    An import from statement imports specific names from a module.
    Example:
        - from math import sqrt
        - from math import sqrt as s
    """

    module: str  # e.g., "math"
    names: List[Tuple[str, Optional[str]]]  # List of (name, alias) tuples
    location: Optional[Location] = None
