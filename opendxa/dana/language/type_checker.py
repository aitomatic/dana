"""Type checker for DANA language.

This module provides a type checker for DANA programs to catch type errors
at parse time rather than runtime.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from opendxa.dana.exceptions import TypeError
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
    LogLevelSetStatement,
    LogStatement,
    Program,
    ReasonStatement,
    WhileLoop,
)
from opendxa.dana.language.visitor import ASTVisitor


class DanaType(Enum):
    """Types supported in DANA."""

    ANY = "any"  # Used for type variables or unknown types
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    NUMBER = "number"  # Represents either INT or FLOAT
    BOOL = "bool"
    NULL = "null"
    FUNCTION = "function"
    OBJECT = "object"


class TypeEnvironment:
    """Type environment for tracking variable types.

    The type environment keeps track of the types of variables during type checking.
    """

    def __init__(self):
        """Initialize an empty type environment."""
        self._types: Dict[str, DanaType] = {}

    def get(self, name: str) -> Optional[DanaType]:
        """Get the type of a variable.

        Args:
            name: The name of the variable

        Returns:
            The type of the variable, or None if not found
        """
        return self._types.get(name)

    def set(self, name: str, type_: DanaType) -> None:
        """Set the type of a variable.

        Args:
            name: The name of the variable
            type_: The type to assign to the variable
        """
        self._types[name] = type_

    def __contains__(self, name: str) -> bool:
        """Check if a variable is in the environment.

        Args:
            name: The name of the variable

        Returns:
            True if the variable is in the environment, False otherwise
        """
        return name in self._types


class TypeCheckVisitor(ASTVisitor):
    """Visitor for type checking DANA programs.

    This visitor traverses the AST and checks types at each node.
    """

    def __init__(self, env: Optional[TypeEnvironment] = None):
        """Initialize the type checker with an optional environment.

        Args:
            env: The type environment to use (creates a new one if None)
        """
        self.env = env or TypeEnvironment()
        self.errors: List[TypeError] = []

    def is_valid(self) -> bool:
        """Check if type checking found no errors.

        Returns:
            True if no errors were found, False otherwise
        """
        return len(self.errors) == 0

    def visit_program(self, node: Program, context=None) -> DanaType:
        """Visit a Program node and type check all statements.

        Args:
            node: The Program node to check
            context: Additional context data (unused)

        Returns:
            The type of the program (always ANY)
        """
        for stmt in node.statements:
            self.visit_node(stmt)
        return DanaType.ANY

    def visit_assignment(self, node: Assignment, context=None) -> DanaType:
        """Visit an Assignment node and check types.

        Args:
            node: The Assignment node to check
            context: Additional context data (unused)

        Returns:
            The type of the assigned value
        """
        value_type = self.visit_node(node.value)

        # If the variable already has a type, check that the new type is compatible
        if node.target.name in self.env:
            existing_type = self.env.get(node.target.name)
            if existing_type is not None and not self._are_types_compatible(existing_type, value_type):
                self.errors.append(
                    TypeError(
                        f"Type mismatch in assignment to '{node.target.name}': " f"expected {existing_type.value}, got {value_type.value}",
                        node.location,
                    )
                )

        # Set the variable's type
        self.env.set(node.target.name, value_type)

        return value_type

    def visit_log_statement(self, node: LogStatement, context=None) -> DanaType:
        """Visit a LogStatement node and check types.

        Args:
            node: The LogStatement node to check
            context: Additional context data (unused)

        Returns:
            The type of the log statement (always ANY)
        """
        # Any expression can be logged, so we don't need to check the type
        self.visit_node(node.message)
        return DanaType.ANY

    def visit_log_level_set_statement(self, node: LogLevelSetStatement, context=None) -> DanaType:
        """Visit a LogLevelSetStatement node.

        Args:
            node: The LogLevelSetStatement node to check
            context: Additional context data (unused)

        Returns:
            The type of the statement (always ANY)
        """
        # No type checking needed for log level set
        return DanaType.ANY

    def visit_conditional(self, node: Conditional, context=None) -> DanaType:
        """Visit a Conditional node and check types.

        Args:
            node: The Conditional node to check
            context: Additional context data (unused)

        Returns:
            The type of the conditional (always ANY)
        """
        # Check that the condition is a boolean
        condition_type = self.visit_node(node.condition)
        if condition_type != DanaType.BOOL and condition_type != DanaType.ANY:
            self.errors.append(TypeError(f"Condition must be a boolean, got {condition_type.value}", node.location))

        # Check all statements in the body
        for stmt in node.body:
            self.visit_node(stmt)

        return DanaType.ANY

    def visit_binary_expression(self, node: BinaryExpression, context=None) -> DanaType:
        """Visit a BinaryExpression node and check types.

        Args:
            node: The BinaryExpression node to check
            context: Additional context data (unused)

        Returns:
            The type of the expression
        """
        left_type = self.visit_node(node.left)
        right_type = self.visit_node(node.right)

        # Check operator-specific type rules
        if node.operator in [BinaryOperator.ADD, BinaryOperator.SUBTRACT, BinaryOperator.MULTIPLY, BinaryOperator.DIVIDE]:
            # Arithmetic operators
            if node.operator == BinaryOperator.ADD and (left_type == DanaType.STRING or right_type == DanaType.STRING):
                # String concatenation is allowed with any type
                return DanaType.STRING

            if left_type not in [DanaType.INT, DanaType.FLOAT, DanaType.NUMBER, DanaType.ANY]:
                self.errors.append(
                    TypeError(f"Left operand of '{node.operator.value}' must be a number, got {left_type.value}", node.location)
                )

            if right_type not in [DanaType.INT, DanaType.FLOAT, DanaType.NUMBER, DanaType.ANY]:
                self.errors.append(
                    TypeError(f"Right operand of '{node.operator.value}' must be a number, got {right_type.value}", node.location)
                )

            # If both are ints, result is int
            if left_type == DanaType.INT and right_type == DanaType.INT:
                return DanaType.INT
            # Otherwise, result is float
            return DanaType.FLOAT

        elif node.operator in [BinaryOperator.EQUALS, BinaryOperator.NOT_EQUALS]:
            # Equality operators can compare any types
            return DanaType.BOOL

        elif node.operator in [
            BinaryOperator.LESS_THAN,
            BinaryOperator.GREATER_THAN,
            BinaryOperator.LESS_EQUALS,
            BinaryOperator.GREATER_EQUALS,
        ]:
            # Comparison operators
            if left_type not in [DanaType.INT, DanaType.FLOAT, DanaType.NUMBER, DanaType.ANY]:
                self.errors.append(
                    TypeError(f"Left operand of '{node.operator.value}' must be a number, got {left_type.value}", node.location)
                )

            if right_type not in [DanaType.INT, DanaType.FLOAT, DanaType.NUMBER, DanaType.ANY]:
                self.errors.append(
                    TypeError(f"Right operand of '{node.operator.value}' must be a number, got {right_type.value}", node.location)
                )

            return DanaType.BOOL

        elif node.operator in [BinaryOperator.AND, BinaryOperator.OR]:
            # Logical operators
            if left_type != DanaType.BOOL and left_type != DanaType.ANY:
                self.errors.append(
                    TypeError(f"Left operand of '{node.operator.value}' must be a boolean, got {left_type.value}", node.location)
                )

            if right_type != DanaType.BOOL and right_type != DanaType.ANY:
                self.errors.append(
                    TypeError(f"Right operand of '{node.operator.value}' must be a boolean, got {right_type.value}", node.location)
                )

            return DanaType.BOOL

        elif node.operator == BinaryOperator.IN:
            # IN operator
            if right_type not in [DanaType.STRING, DanaType.OBJECT, DanaType.ANY]:
                self.errors.append(TypeError(f"Right operand of 'in' must be a string or object, got {right_type.value}", node.location))

            return DanaType.BOOL

        # Unknown operator
        return DanaType.ANY

    def visit_literal_expression(self, node: LiteralExpression, context=None) -> DanaType:
        """Visit a LiteralExpression node and determine its type.

        Args:
            node: The LiteralExpression node to check
            context: Additional context data (unused)

        Returns:
            The type of the literal
        """
        return self.visit_node(node.literal)

    def visit_identifier(self, node: Identifier, context=None) -> DanaType:
        """Visit an Identifier node and check if it's defined.

        Args:
            node: The Identifier node to check
            context: Additional context data (unused)

        Returns:
            The type of the identifier
        """
        # If the identifier is not in the environment, it's a type error
        if node.name not in self.env:
            # Don't report errors for identifiers that come from scopes
            # or for bare variable names (which can be auto-scoped at runtime)
            if "." not in node.name:
                # Instead of raising an error, return ANY type for bare variables
                # This allows them to be auto-scoped at runtime
                return DanaType.ANY
            self.errors.append(TypeError(f"Undefined variable: {node.name}", node.location))
            return DanaType.ANY

        # Get the type from environment, defaulting to ANY if not found
        return self.env.get(node.name) or DanaType.ANY

    def visit_function_call(self, node: FunctionCall, context=None) -> DanaType:
        """Visit a FunctionCall node and check its types.

        Args:
            node: The FunctionCall node to check
            context: Additional context data (unused)

        Returns:
            The return type of the function (always ANY for now)
        """
        # Check each argument
        for arg_name, arg_value in node.args.items():
            if isinstance(arg_value, (LiteralExpression, Identifier, BinaryExpression, FunctionCall)):
                self.visit_node(arg_value)

        # For now, we don't know the return types of functions
        return DanaType.ANY

    def visit_literal(self, node: Literal, context=None) -> DanaType:
        """Visit a Literal node and determine its type.

        Args:
            node: The Literal node to check
            context: Additional context data (unused)

        Returns:
            The type of the literal
        """
        value = node.value

        # Need to check bool first since True and False are also instances of int
        if isinstance(value, bool):
            return DanaType.BOOL
        elif isinstance(value, str):
            return DanaType.STRING
        elif isinstance(value, int):
            return DanaType.INT
        elif isinstance(value, float):
            return DanaType.FLOAT
        elif value is None:
            return DanaType.NULL
        elif isinstance(value, FStringExpression):
            return DanaType.STRING

        # Unknown literal type
        return DanaType.ANY

    def visit_fstring_expression(self, node: FStringExpression, context=None) -> DanaType:
        """Visit an FStringExpression node and check its parts.

        Args:
            node: The FStringExpression node to check
            context: Additional context data (unused)

        Returns:
            The type of the f-string (always STRING)
        """
        # Check each expression part
        for part in node.parts:
            if not isinstance(part, str):
                self.visit_node(part)

        return DanaType.STRING

    def visit_while_loop(self, node: WhileLoop, context=None) -> DanaType:
        """Visit a WhileLoop node and check types.

        Args:
            node: The WhileLoop node to check
            context: Additional context data (unused)

        Returns:
            The type of the while loop (always ANY)
        """
        # Check that the condition is a boolean
        condition_type = self.visit_node(node.condition)
        if condition_type != DanaType.BOOL and condition_type != DanaType.ANY:
            self.errors.append(TypeError(f"While loop condition must be a boolean, got {condition_type.value}", node.location))

        # Check all statements in the body
        for stmt in node.body:
            self.visit_node(stmt)

        return DanaType.ANY

    def visit_reason_statement(self, node: ReasonStatement, context=None) -> DanaType:
        """Visit a ReasonStatement node and check types.

        Args:
            node: The ReasonStatement node to check
            context: Additional context data (unused)

        Returns:
            The type of the reason statement result (STRING or OBJECT depending on format)
        """
        # Check the prompt expression
        self.visit_node(node.prompt)

        # Check context variables if present
        if node.context:
            for ident in node.context:
                self.visit_node(ident)

        # Determine the return type based on format option
        if node.options and "format" in node.options and node.options["format"] == "json":
            return DanaType.OBJECT

        # Default return type is string
        return DanaType.STRING

    def visit_node(self, node: Any, context=None) -> DanaType:
        """Visit any node and dispatch to the appropriate method.

        Args:
            node: The node to check
            context: Additional context data (unused)

        Returns:
            The type of the node
        """
        if isinstance(node, Program):
            return self.visit_program(node, context)
        elif isinstance(node, Assignment):
            return self.visit_assignment(node, context)
        elif isinstance(node, LogStatement):
            return self.visit_log_statement(node, context)
        elif isinstance(node, LogLevelSetStatement):
            return self.visit_log_level_set_statement(node, context)
        elif isinstance(node, Conditional):
            return self.visit_conditional(node, context)
        elif isinstance(node, WhileLoop):
            return self.visit_while_loop(node, context)
        elif isinstance(node, ReasonStatement):
            return self.visit_reason_statement(node, context)
        elif isinstance(node, BinaryExpression):
            return self.visit_binary_expression(node, context)
        elif isinstance(node, LiteralExpression):
            return self.visit_literal_expression(node, context)
        elif isinstance(node, Identifier):
            return self.visit_identifier(node, context)
        elif isinstance(node, FunctionCall):
            return self.visit_function_call(node, context)
        elif isinstance(node, Literal):
            return self.visit_literal(node, context)
        elif isinstance(node, FStringExpression):
            return self.visit_fstring_expression(node, context)

        # Unknown node type
        return DanaType.ANY

    def _are_types_compatible(self, expected: DanaType, actual: DanaType) -> bool:
        """Check if two types are compatible for assignment.

        Args:
            expected: The expected type
            actual: The actual type

        Returns:
            True if the types are compatible, False otherwise
        """
        # ANY is compatible with anything
        if expected == DanaType.ANY or actual == DanaType.ANY:
            return True

        # NUMBER is compatible with INT and FLOAT
        if expected == DanaType.NUMBER and actual in [DanaType.INT, DanaType.FLOAT]:
            return True

        if actual == DanaType.NUMBER and expected in [DanaType.INT, DanaType.FLOAT]:
            return True

        # INT can be implicitly converted to FLOAT
        if expected == DanaType.FLOAT and actual == DanaType.INT:
            return True

        # Otherwise, types must match exactly
        return expected == actual


def check_types(program: Program) -> List[TypeError]:
    """Check types in a DANA program.

    Args:
        program: The program to check

    Returns:
        A list of type errors found during checking
    """
    visitor = TypeCheckVisitor()
    visitor.visit_program(program)
    return visitor.errors
