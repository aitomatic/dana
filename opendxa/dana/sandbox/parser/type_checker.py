"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Type checker for DANA programs.

This module provides type checking functionality for DANA programs.
"""

from typing import Any, Dict, Optional

from opendxa.dana.common.exceptions import TypeError
from opendxa.dana.sandbox.parser.ast import (
    Assignment,
    AttributeAccess,
    BinaryExpression,
    Conditional,
    DictLiteral,
    ExceptBlock,
    Expression,
    ForLoop,
    FunctionCall,
    FunctionDefinition,
    Identifier,
    ImportFromStatement,
    ImportStatement,
    LiteralExpression,
    Program,
    SetLiteral,
    SubscriptExpression,
    TryBlock,
    UnaryExpression,
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
        elif isinstance(statement, FunctionCall):
            self.check_function_call(statement)
        elif isinstance(statement, Conditional):
            self.check_conditional(statement)
        elif isinstance(statement, WhileLoop):
            self.check_while_loop(statement)
        elif isinstance(statement, ForLoop):
            self.check_for_loop(statement)
        elif isinstance(statement, TryBlock):
            self.check_try_block(statement)
        elif isinstance(statement, FunctionDefinition):
            self.check_function_definition(statement)
        elif isinstance(statement, ImportStatement):
            self.check_import_statement(statement)
        elif isinstance(statement, ImportFromStatement):
            self.check_import_from_statement(statement)
        else:
            raise TypeError(f"Unsupported statement type: {type(statement).__name__}", statement)

    def check_assignment(self, node: Assignment) -> None:
        """Check an assignment for type errors."""
        value_type = self.check_expression(node.value)
        self.environment.set(node.target.name, value_type)

    def check_conditional(self, node: Conditional) -> None:
        """Check a conditional for type errors."""
        condition_type = self.check_expression(node.condition)
        if condition_type != DanaType("bool"):
            raise TypeError(f"Condition must be boolean, got {condition_type}", node)

        for statement in node.body:
            self.check_statement(statement)
        for statement in node.else_body:
            self.check_statement(statement)

    def check_while_loop(self, node: WhileLoop) -> None:
        """Check a while loop for type errors."""
        condition_type = self.check_expression(node.condition)
        if condition_type != DanaType("bool"):
            raise TypeError(f"Loop condition must be boolean, got {condition_type}", node)

        for statement in node.body:
            self.check_statement(statement)

    def check_for_loop(self, node: ForLoop) -> None:
        """Check a for loop for type errors."""
        iterable_type = self.check_expression(node.iterable)
        # Assuming iterable is a list or range
        if iterable_type != DanaType("array") and iterable_type != DanaType("range"):
            raise TypeError(f"For loop iterable must be a list or range, got {iterable_type}", node)

        for statement in node.body:
            self.check_statement(statement)

    def check_try_block(self, node: TryBlock) -> None:
        """Check a try block for type errors."""
        for statement in node.body:
            self.check_statement(statement)
        for except_block in node.except_blocks:
            self.check_except_block(except_block)
        if node.finally_block:
            for statement in node.finally_block:
                self.check_statement(statement)

    def check_except_block(self, node: ExceptBlock) -> None:
        """Check an except block for type errors."""
        for statement in node.body:
            self.check_statement(statement)

    def check_function_definition(self, node: FunctionDefinition) -> None:
        """Check a function definition for type errors."""
        # Assuming all functions return 'any' for now
        for statement in node.body:
            self.check_statement(statement)

    def check_import_statement(self, node: ImportStatement) -> None:
        """Check an import statement for type errors."""
        pass  # No type checking needed

    def check_import_from_statement(self, node: ImportFromStatement) -> None:
        """Check an import from statement for type errors."""
        pass  # No type checking needed

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
        elif isinstance(expression, UnaryExpression):
            return self.check_unary_expression(expression)
        elif isinstance(expression, AttributeAccess):
            return self.check_attribute_access(expression)
        elif isinstance(expression, SubscriptExpression):
            return self.check_subscript_expression(expression)
        elif isinstance(expression, DictLiteral):
            return self.check_dict_literal(expression)
        elif isinstance(expression, SetLiteral):
            return self.check_set_literal(expression)
        else:
            raise TypeError(f"Unsupported expression type: {type(expression).__name__}", expression)

    def check_literal_expression(self, node: LiteralExpression) -> DanaType:
        """Check a literal expression for type errors."""
        return DanaType(node.literal.type)

    def check_identifier(self, node: Identifier) -> DanaType:
        """Check an identifier for type errors."""
        type_ = self.environment.get(node.name)
        if type_ is None:
            raise TypeError(f"Undefined variable: {node.name}", node)
        return type_

    def check_binary_expression(self, node: BinaryExpression) -> DanaType:
        """Check a binary expression for type errors.

        This is a simple implementation that checks that the left and right operands
        are of the same type and returns that type.
        """
        left_type = self.check_expression(node.left)
        right_type = self.check_expression(node.right)

        if left_type != right_type:
            raise TypeError(f"Binary expression operands must be of the same type, got {left_type} and {right_type}", node)

        return left_type

    def check_unary_expression(self, node: UnaryExpression) -> DanaType:
        """Check a unary expression for type errors."""
        operand_type = self.check_expression(node.operand)
        if node.operator == "-" and operand_type != DanaType("int") and operand_type != DanaType("float"):
            raise TypeError(f"Unary operator '-' requires int or float, got {operand_type}", node)
        elif node.operator == "not" and operand_type != DanaType("bool"):
            raise TypeError(f"Unary operator 'not' requires bool, got {operand_type}", node)
        return operand_type

    def check_attribute_access(self, node: AttributeAccess) -> DanaType:
        """Check an attribute access for type errors."""
        object_type = self.check_expression(node.object)
        # Assuming all objects have attributes
        # In a real implementation, you would check if the object has the attribute
        return object_type

    def check_subscript_expression(self, node: SubscriptExpression) -> DanaType:
        """Check a subscript expression for type errors."""
        object_type = self.check_expression(node.object)
        index_type = self.check_expression(node.index)
        if object_type != DanaType("array") and object_type != DanaType("dict"):
            raise TypeError(f"Subscript requires array or dict, got {object_type}", node)
        if object_type == DanaType("array") and index_type != DanaType("int"):
            raise TypeError(f"Array subscript requires int, got {index_type}", node)
        if object_type == DanaType("dict") and index_type != DanaType("string"):
            raise TypeError(f"Dict subscript requires string, got {index_type}", node)
        return DanaType("any")

    def check_dict_literal(self, node: DictLiteral) -> DanaType:
        """Check a dictionary literal for type errors."""
        for key, value in node.items:
            key_type = self.check_expression(key)
            _ = self.check_expression(value)
            if key_type != DanaType("string"):
                raise TypeError(f"Dict key must be string, got {key_type}", node)
        return DanaType("dict")

    def check_set_literal(self, node: SetLiteral) -> DanaType:
        """Check a set literal for type errors."""
        for item in node.items:
            _ = self.check_expression(item)
        return DanaType("set")

    @staticmethod
    def check_types(program: Program) -> None:
        """Check types in a DANA program (static utility)."""
        checker = TypeChecker()
        checker.check_program(program)
