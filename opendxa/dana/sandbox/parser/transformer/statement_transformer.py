"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Statement transformers for DANA language parsing.
"""

from typing import Union, cast

from lark import Token, Tree

from opendxa.dana.sandbox.parser.ast import (
    AssertStatement,
    Assignment,
    AttributeAccess,
    BinaryExpression,
    BreakStatement,
    Conditional,
    ContinueStatement,
    DictLiteral,
    ForLoop,
    FStringExpression,
    FunctionCall,
    FunctionDefinition,
    Identifier,
    ImportFromStatement,
    ImportStatement,
    LiteralExpression,
    PassStatement,
    PrintStatement,
    Program,
    RaiseStatement,
    ReturnStatement,
    SetLiteral,
    SubscriptExpression,
    TryBlock,
    TupleLiteral,
    WhileLoop,
)
from opendxa.dana.sandbox.parser.transformer.base_transformer import BaseTransformer
from opendxa.dana.sandbox.parser.transformer.expression_transformer import ExpressionTransformer
from opendxa.dana.sandbox.parser.transformer.variable_transformer import VariableTransformer

# Allowed types for Assignment.value
AllowedAssignmentValue = Union[
    LiteralExpression,
    Identifier,
    BinaryExpression,
    FunctionCall,
    TupleLiteral,
    DictLiteral,
    SetLiteral,
    SubscriptExpression,
    AttributeAccess,
    FStringExpression,
]


class StatementTransformer(BaseTransformer):
    """
    Converts DANA statement parse trees into AST nodes.
    Handles all statement types: assignments, control flow, function definitions, imports, try/except, and bare expressions.
    Methods are grouped by grammar hierarchy for clarity and maintainability.
    """

    def __init__(self):
        """Initialize the statement transformer and its expression transformer."""
        super().__init__()
        self.expression_transformer = ExpressionTransformer()

    # === Program and Statement Entry ===
    def program(self, items):
        """Transform the program rule into a Program node."""
        # Flatten any nested statement lists or Trees
        statements = []
        for item in items:
            if isinstance(item, list):
                statements.extend(item)
            elif hasattr(item, "data") and getattr(item, "data", None) == "statements":
                # Lark Tree node for 'statements'
                statements.extend(item.children)
            elif item is not None:
                statements.append(item)
        return Program(statements=statements)

    def statement(self, items):
        """Transform a statement rule (returns the first non-None AST node)."""
        for item in items:
            # Unwrap Tree or list wrappers
            while isinstance(item, (list, Tree)):
                if isinstance(item, list):
                    item = item[0] if item else None
                elif isinstance(item, Tree) and item.children:
                    item = item.children[0]
                else:
                    break
            if item is not None:
                return item
        return None

    # === Compound Statements ===
    def conditional(self, items):
        """Transform a conditional (if) rule into a Conditional node."""
        if_part = items[0]
        else_body = items[1] if len(items) > 1 and items[1] is not None else []
        condition = if_part[0]
        if_body = if_part[1:]
        line_num = getattr(condition, "line", 0) or 0
        return Conditional(condition=condition, body=if_body, else_body=else_body, line_num=line_num)

    def if_part(self, items):
        """Transform if part of conditional into a list with condition first, then body statements."""
        condition = items[0]
        body = self._filter_body(items[1:])
        return [condition] + body

    def else_part(self, items):
        """Transform else part of conditional into a list of body statements."""
        return self._filter_body(items)

    def while_stmt(self, items):
        """Transform a while statement rule into a WhileLoop node."""
        condition = items[0]
        body = self._transform_block(items[1:])
        line_num = getattr(condition, "line", 0) or 0
        return WhileLoop(condition=condition, body=body, line_num=line_num)

    def for_stmt(self, items):
        """Transform a for loop rule into a ForLoop node."""
        from opendxa.dana.sandbox.parser.ast import Expression, Identifier

        target = Identifier(name=items[0].value if isinstance(items[0], Token) else str(items[0]))
        iterable = self.expression_transformer.expression([items[1]])
        if isinstance(iterable, tuple):
            raise TypeError(f"For loop iterable cannot be a tuple: {iterable}")
        # Ensure iterable is Expression
        iterable_expr = cast(Expression, iterable)
        body = items[2] if len(items) > 2 else []
        return ForLoop(target=target, iterable=iterable_expr, body=body)

    def function_def(self, items):
        """Transform a function definition rule into a FunctionDefinition node."""
        name = Identifier(name=items[0].value if hasattr(items[0], "value") else str(items[0]))
        parameters = items[1] if len(items) > 2 else []
        body = self._transform_block(items[-1]) if items else []
        return FunctionDefinition(name=name, parameters=parameters, body=body)

    def try_stmt(self, items):
        """Transform a try statement rule into a TryBlock node."""
        body = self._transform_block(items[0])
        except_blocks = self._transform_block(items[1]) if len(items) > 1 else []
        finally_block = self._transform_block(items[2]) if len(items) > 2 else []
        return TryBlock(body=body, except_blocks=except_blocks, finally_block=finally_block)

    def if_stmt(self, items):
        """Transform an if_stmt rule into a Conditional AST node, handling if/elif/else blocks."""
        from lark import Tree

        from opendxa.dana.sandbox.parser.ast import Conditional

        def transform_elif_blocks(blocks):
            # Recursively transform Tree nodes to Conditional nodes
            result = []
            for b in self._transform_block(blocks):
                if isinstance(b, Tree) and hasattr(self, b.data):
                    method = getattr(self, b.data, None)
                    if method:
                        transformed = method(b.children)
                        result.append(transformed)
                    else:
                        result.append(b)
                else:
                    result.append(b)
            return result

        condition = items[0]
        if_body = self._transform_block(items[1])
        else_body = []
        if len(items) == 3:
            third = items[2]
            # Could be else or elifs
            if isinstance(third, list) or (isinstance(third, Tree) and getattr(third, "data", None) == "elif_stmts"):
                elif_blocks = transform_elif_blocks(third)
                else_body = elif_blocks
            else:
                else_body = self._transform_block(third)
        elif len(items) == 4:
            elif_blocks = transform_elif_blocks(items[2])
            else_block = self._transform_block(items[3])

            def nest_elif_blocks(blocks, final_else):
                if not blocks:
                    return final_else
                head, *tail = blocks
                # Only nest if head is a Conditional, else treat as terminal else_body
                if not hasattr(head, "condition") or not hasattr(head, "body"):
                    return [head] + (nest_elif_blocks(tail, final_else) if tail else final_else)
                nested = Conditional(
                    condition=head.condition,
                    body=head.body,
                    else_body=nest_elif_blocks(tail, final_else),
                    line_num=getattr(head.condition, "line", 0) or 0,
                )
                return [nested]

            else_body = self._transform_block(nest_elif_blocks(elif_blocks, else_block))
        line_num = getattr(condition, "line", 0) or 0
        return Conditional(condition=condition, body=if_body, else_body=else_body, line_num=line_num)

    # === Simple Statements ===
    def assignment(self, items):
        """
        Transform an assignment rule into an Assignment node.
        Always use VariableTransformer to transform the target, and never attempt to re-scope or re-stringify an Identifier.
        """
        from opendxa.dana.sandbox.parser.ast import (
            AttributeAccess,
            BinaryExpression,
            DictLiteral,
            FStringExpression,
            FunctionCall,
            Identifier,
            LiteralExpression,
            SetLiteral,
            SubscriptExpression,
            TupleLiteral,
        )

        target_tree = items[0]
        # Always use VariableTransformer to get a clean Identifier
        target = VariableTransformer().variable([target_tree])
        if not isinstance(target, Identifier):
            raise TypeError(f"Assignment target must be Identifier, got {type(target)}")
        value_tree = items[1]
        ast_types = (
            LiteralExpression,
            Identifier,
            BinaryExpression,
            FunctionCall,
            TupleLiteral,
            DictLiteral,
            SetLiteral,
            SubscriptExpression,
            AttributeAccess,
            FStringExpression,
        )
        if isinstance(value_tree, tuple):
            raise TypeError(f"Assignment value cannot be a tuple: {value_tree}")
        if not isinstance(value_tree, ast_types):
            value = self.expression_transformer.expression([value_tree])
        else:
            value = value_tree
        value_expr = cast(AllowedAssignmentValue, value)
        return Assignment(target=target, value=value_expr)

    def expr_stmt(self, items):
        """Transform a bare expression statement (expr_stmt) into an Expression AST node."""
        return self.expression_transformer.expression(items)

    def return_stmt(self, items):
        """Transform a return statement rule into a ReturnStatement node."""
        value = self.expression_transformer.expression(items) if items else None
        if isinstance(value, tuple):
            raise TypeError(f"Return value cannot be a tuple: {value}")
        return ReturnStatement(value=value)

    def break_stmt(self, items):
        """Transform a break statement rule into a BreakStatement node."""
        return BreakStatement()

    def continue_stmt(self, items):
        """Transform a continue statement rule into a ContinueStatement node."""
        return ContinueStatement()

    def pass_stmt(self, items):
        """Transform a pass statement rule into a PassStatement node."""
        return PassStatement()

    def raise_stmt(self, items):
        """Transform a raise statement rule into a RaiseStatement node."""
        value = self.expression_transformer.expression([items[0]]) if items else None
        from_value = self.expression_transformer.expression([items[1]]) if len(items) > 1 else None
        if isinstance(value, tuple) or isinstance(from_value, tuple):
            raise TypeError(f"Raise statement values cannot be tuples: {value}, {from_value}")
        return RaiseStatement(value=value, from_value=from_value)

    def assert_stmt(self, items):
        """Transform an assert statement rule into an AssertStatement node."""
        from opendxa.dana.sandbox.parser.ast import Expression

        condition = self.expression_transformer.expression([items[0]])
        message = self.expression_transformer.expression([items[1]]) if len(items) > 1 else None
        if isinstance(condition, tuple) or isinstance(message, tuple):
            raise TypeError(f"Assert statement values cannot be tuples: {condition}, {message}")
        # Ensure condition and message are Expression or None
        condition_expr = cast(Expression, condition)
        message_expr = cast(Expression, message) if message is not None else None
        return AssertStatement(condition=condition_expr, message=message_expr)

    def print_statement(self, items):
        """Transform a print statement rule into a PrintStatement node."""
        message = items[0]
        return PrintStatement(message=message)

    # === Import Statements ===
    def import_stmt(self, items):
        """Transform an import statement rule into an ImportStatement or ImportFromStatement node."""
        if items[0] == "import":
            module = items[1]
            alias = items[2] if len(items) > 2 else None
            return ImportStatement(module=module, alias=alias)
        elif items[0] == "from":
            module = items[1]
            name = items[2]
            alias = items[3] if len(items) > 3 else None
            return ImportFromStatement(module=module, names=[(name, alias)])
        else:
            raise ValueError(f"Unknown import statement: {items}")

    # === Argument Handling ===
    def arg_list(self, items):
        """Transform an argument list into a list of arguments."""
        return items

    def positional_args(self, items):
        """Transform positional arguments into a list."""
        return items

    def named_args(self, items):
        """Transform named arguments into a dictionary."""
        args = {}
        for item in items:
            if isinstance(item, tuple):
                key, value = item
                args[key] = value
        return args

    def named_arg(self, items):
        """Transform a named argument into a tuple of (name, value)."""
        name = items[0].value
        value = items[1]
        return (name, value)

    # === Utility ===
    def _filter_body(self, items):
        """
        Utility to filter out Token and None from a list of items.
        Used to clean up statement bodies extracted from parse trees, removing indentation tokens and empty lines.
        """
        return [item for item in items if not (isinstance(item, Token) or item is None)]

    def identifier(self, items):
        """This method is now handled by VariableTransformer."""
        raise NotImplementedError("identifier is handled by VariableTransformer")

    def _transform_block(self, block):
        """Recursively transform a block (list, Tree, or node) into a flat list of AST nodes."""
        from lark import Tree

        result = []
        if block is None:
            return result
        if isinstance(block, list):
            for item in block:
                result.extend(self._transform_block(item))
        elif isinstance(block, Tree):
            # If this is a block or statements node, flatten children
            if getattr(block, "data", None) in {"block", "statements"}:
                for child in block.children:
                    result.extend(self._transform_block(child))
            else:
                # Try to dispatch to a transformer method if available
                method = getattr(self, block.data, None)
                if method:
                    transformed = method(block.children)
                    # If the result is a list, flatten it
                    if isinstance(transformed, list):
                        result.extend(self._transform_block(transformed))
                    else:
                        result.append(transformed)
                else:
                    # Fallback: treat as leaf
                    result.append(block)
        else:
            result.append(block)
        return result
