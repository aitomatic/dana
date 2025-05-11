"""Type checker for DANA programs.

This module provides type checking functionality for DANA programs.
"""

from typing import Any, Dict, Optional

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    Conditional,
    Expression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    LogLevelSetStatement,
    LogStatement,
    Program,
    ReasonStatement,
    WhileLoop,
)


class DanaType:
    """Represents a type in DANA."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DanaType):
            return False
        return self.name == other.name


class TypeEnvironment:
    """Environment for type checking."""

    def __init__(self, parent: Optional["TypeEnvironment"] = None):
        self.types: Dict[str, DanaType] = {}
        self.parent = parent

    def get(self, name: str) -> Optional[DanaType]:
        """Get a type from the environment."""
        if name in self.types:
            return self.types[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name: str, type_: DanaType) -> None:
        """Set a type in the environment."""
        self.types[name] = type_


class TypeChecker:
    """Type checker for DANA programs."""

    def __init__(self):
        self.environment = TypeEnvironment()

    def check_program(self, program: Program) -> None:
        """Check a program for type errors."""
        for statement in program.statements:
            self.check_statement(statement)

    def check_statement(self, statement: Any) -> None:
        """Check a statement for type errors."""
        if isinstance(statement, Assignment):
            self.check_assignment(statement)
        elif isinstance(statement, LogStatement):
            self.check_log_statement(statement)
        elif isinstance(statement, LogLevelSetStatement):
            self.check_log_level_set_statement(statement)
        elif isinstance(statement, Conditional):
            self.check_conditional(statement)
        elif isinstance(statement, WhileLoop):
            self.check_while_loop(statement)
        elif isinstance(statement, ReasonStatement):
            self.check_reason_statement(statement)
        elif isinstance(statement, FunctionCall):
            self.check_function_call(statement)
        else:
            raise RuntimeError(f"Unsupported statement type: {type(statement).__name__}")

    def check_assignment(self, node: Assignment) -> None:
        """Check an assignment for type errors."""
        value_type = self.check_expression(node.value)
        self.environment.set(node.target.name, value_type)

    def check_log_statement(self, node: LogStatement) -> None:
        """Check a log statement for type errors."""
        self.check_expression(node.message)

    def check_log_level_set_statement(self, node: LogLevelSetStatement) -> None:
        """Check a log level set statement for type errors."""
        pass  # No type checking needed

    def check_conditional(self, node: Conditional) -> None:
        """Check a conditional for type errors."""
        condition_type = self.check_expression(node.condition)
        if condition_type != DanaType("bool"):
            raise RuntimeError(f"Condition must be boolean, got {condition_type}")

        for statement in node.body:
            self.check_statement(statement)
        for statement in node.else_body:
            self.check_statement(statement)

    def check_while_loop(self, node: WhileLoop) -> None:
        """Check a while loop for type errors."""
        condition_type = self.check_expression(node.condition)
        if condition_type != DanaType("bool"):
            raise RuntimeError(f"Loop condition must be boolean, got {condition_type}")

        for statement in node.body:
            self.check_statement(statement)

    def check_reason_statement(self, node: ReasonStatement) -> None:
        """Check a reason statement for type errors."""
        prompt_type = self.check_expression(node.prompt)
        if prompt_type != DanaType("string"):
            raise RuntimeError(f"Reason prompt must be string, got {prompt_type}")

    def check_function_call(self, node: FunctionCall) -> None:
        """Check a function call for type errors."""
        # TODO: Implement function call type checking
        pass

    def check_expression(self, expression: Expression) -> DanaType:
        """Check an expression for type errors."""
        if isinstance(expression, LiteralExpression):
            return self.check_literal_expression(expression)
        elif isinstance(expression, Identifier):
            return self.check_identifier(expression)
        elif isinstance(expression, BinaryExpression):
            return self.check_binary_expression(expression)
        elif isinstance(expression, FunctionCall):
            return self.check_function_call(expression)
        else:
            raise RuntimeError(f"Unsupported expression type: {type(expression).__name__}")

    def check_literal_expression(self, node: LiteralExpression) -> DanaType:
        """Check a literal expression for type errors."""
        return DanaType(node.literal.type)

    def check_identifier(self, node: Identifier) -> DanaType:
        """Check an identifier for type errors."""
        type_ = self.environment.get(node.name)
        if type_ is None:
            raise RuntimeError(f"Undefined variable: {node.name}")
        return type_

    def check_binary_expression(self, node: BinaryExpression) -> DanaType:
        """Check a binary expression for type errors."""
        left_type = self.check_expression(node.left)
        right_type = self.check_expression(node.right)

        # TODO: Implement proper type checking for binary operations
        return DanaType("any")  # For now, return any type

    @staticmethod
    def check_types(program: Program) -> None:
        """Check types in a DANA program (static utility)."""
        checker = TypeChecker()
        checker.check_program(program)
