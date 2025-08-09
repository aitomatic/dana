"""
Control flow transformer for Dana language parsing.

This module handles all control flow statement transformations, including:
- Conditional statements (if/elif/else)
- Loop statements (while/for)
- Exception handling (try/except/finally)

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import cast

from lark import Token, Tree

from dana.core.lang.ast import (
    Conditional,
    ExceptBlock,
    Expression,
    ForLoop,
    Identifier,
    TryBlock,
    WhileLoop,
)
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer


class ControlFlowTransformer(BaseTransformer):
    """
    Handles control flow statement transformations for the Dana language.
    Converts control flow parse trees into corresponding AST nodes.
    """

    def __init__(self, main_transformer):
        """Initialize with reference to main transformer for shared utilities."""
        super().__init__()
        self.main_transformer = main_transformer
        self.expression_transformer = main_transformer.expression_transformer

    # === Conditional Statements ===

    def conditional(self, items):
        """Transform a conditional (if) rule into a Conditional node."""
        if_part = items[0]
        else_body = items[1] if len(items) > 1 and items[1] is not None else []
        condition = if_part[0]
        if_body = if_part[1:]
        line_num = getattr(condition, "line", 0) or 0
        condition_expr = cast(Expression, condition)
        return Conditional(condition=condition_expr, body=if_body, else_body=else_body, line_num=line_num)

    def if_part(self, items):
        """Transform if part of conditional into a list with condition first, then body statements."""
        condition = items[0]
        body = self.main_transformer._filter_body(items[1:])
        return [condition] + body

    def else_part(self, items):
        """Transform else part of conditional into a list of body statements."""
        return self.main_transformer._filter_body(items)

    def if_stmt(self, items):
        """Transform an if_stmt rule into a Conditional AST node, handling if/elif/else blocks."""

        from dana.core.lang.ast import Conditional

        relevant_items = self.main_transformer._filter_relevant_items(items)

        # Extract main if condition and body
        condition = self.expression_transformer.expression([relevant_items[0]])
        if_body = self.main_transformer._transform_block(relevant_items[1])
        line_num = getattr(condition, "line", 0) or 0

        # Default: no else or elif
        else_body = []

        # Handle additional clauses (elif/else)
        # Based on debugging: relevant_items[2] contains the elif list, relevant_items[3] is the final else block
        if len(relevant_items) >= 3 and relevant_items[2] is not None:
            # Check if we have elif statements (should be a list of Conditional objects)
            elif_item = relevant_items[2]
            if isinstance(elif_item, list) and elif_item and isinstance(elif_item[0], Conditional):
                # We have elif statements
                else_body = elif_item

                # Check if we also have a final else block
                if len(relevant_items) >= 4 and relevant_items[3] is not None:
                    final_else_block = self.main_transformer._transform_block(relevant_items[3])

                    # Add the final else block to the last elif conditional
                    if else_body and isinstance(else_body[-1], Conditional):
                        # Find the deepest nested conditional and set its else_body
                        last_cond = else_body[-1]
                        while (
                            isinstance(last_cond.else_body, list)
                            and last_cond.else_body
                            and isinstance(last_cond.else_body[0], Conditional)
                        ):
                            last_cond = last_cond.else_body[0]
                        last_cond.else_body = final_else_block
            elif isinstance(elif_item, Tree) and getattr(elif_item, "data", None) == "block":
                # No elif, just a direct else block
                else_body = self.main_transformer._transform_block(elif_item)
            elif isinstance(elif_item, Tree) and getattr(elif_item, "data", None) == "elif_stmts":
                # Transform elif_stmts into a proper AST node (fallback case)
                else_body = self.elif_stmts(elif_item.children)

        return Conditional(condition=cast(Expression, condition), body=if_body, else_body=else_body, line_num=line_num)

    def elif_stmts(self, items):
        """Transform a sequence of elif statements into a single nested Conditional structure."""
        if not items:
            return []

        # Process elif statements in reverse order to build nested structure from inside out
        conditionals = []
        for item in items:
            if hasattr(item, "data") and item.data == "elif_stmt":
                cond = self.elif_stmt(item.children)
                conditionals.append(cond)
            elif isinstance(item, Conditional):
                conditionals.append(item)
            else:
                self.warning(f"Unexpected elif_stmts item: {item}")

        if not conditionals:
            return []

        # Build nested structure: each elif becomes the else_body of the previous one
        # Start with the last elif and work backwards
        result = conditionals[-1]  # Start with the last elif

        # Nest each previous elif as the outer conditional
        for i in range(len(conditionals) - 2, -1, -1):
            current_elif = conditionals[i]
            current_elif.else_body = [result]  # Set the nested conditional as else_body
            result = current_elif

        return [result]  # Return a single-item list containing the root conditional

    def elif_stmt(self, items):
        """Transform a single elif statement into a Conditional node."""
        relevant_items = self.main_transformer._filter_relevant_items(items)
        condition = self.expression_transformer.expression([relevant_items[0]])
        body = self.main_transformer._transform_block(relevant_items[1])
        line_num = getattr(condition, "line", 0) or 0
        return Conditional(condition=cast(Expression, condition), body=body, else_body=[], line_num=line_num)

    # === Loop Statements ===

    def while_stmt(self, items):
        """Transform a while statement rule into a WhileLoop node."""
        relevant_items = self.main_transformer._filter_relevant_items(items)
        condition = relevant_items[0]
        body = self.main_transformer._transform_block(relevant_items[1:])
        line_num = getattr(condition, "line", 0) or 0
        condition_expr = cast(Expression, condition)
        return WhileLoop(condition=condition_expr, body=body, line_num=line_num)

    def for_stmt(self, items):
        """Transform a for loop rule into a ForLoop node."""

        from dana.core.lang.ast import Expression

        # Filter out irrelevant items (None, comments, etc.)
        relevant_items = self.main_transformer._filter_relevant_items(items)

        # Get the loop variable(s) (target)
        target_str = relevant_items[0].value if isinstance(relevant_items[0], Token) else str(relevant_items[0])

        # Handle tuple unpacking: check if target_str contains commas
        if "," in target_str:
            # Multiple targets: create list of Identifiers
            target_names = [name.strip() for name in target_str.split(",")]
            target = [Identifier(name=name) for name in target_names]
        else:
            # Single target: create single Identifier
            target = Identifier(name=target_str)

        # Transform the iterable expression
        iterable = self.expression_transformer.expression([relevant_items[1]])
        if isinstance(iterable, tuple):
            raise TypeError(f"For loop iterable cannot be a tuple: {iterable}")

        # Ensure iterable is Expression type
        iterable_expr = cast(Expression, iterable)

        # The block should be the third relevant item
        # Grammar: "for" NAME "in" expr ":" [COMMENT] block
        # After filtering: [NAME, expr, block]
        body_items = []
        if len(relevant_items) >= 3:
            block_item = relevant_items[2]

            # Handle if body is a Tree (block node)
            if isinstance(block_item, Tree) and getattr(block_item, "data", None) == "block":
                body_items = self.main_transformer._transform_block(block_item)
            # If body is a list, transform each item
            elif isinstance(block_item, list):
                for item in block_item:
                    transformed = self.main_transformer._transform_item(item)
                    if transformed is not None:
                        body_items.append(transformed)
            # Otherwise, try to transform the item
            else:
                transformed = self.main_transformer._transform_item(block_item)
                if transformed is not None:
                    if isinstance(transformed, list):
                        body_items.extend(transformed)
                    else:
                        body_items.append(transformed)

        return ForLoop(target=target, iterable=iterable_expr, body=body_items)

    # === Exception Handling ===

    def try_stmt(self, items):
        """Transform a try-except-finally statement into a TryBlock node."""
        relevant_items = self.main_transformer._filter_relevant_items(items)

        # First item is always the try body
        try_body = self.main_transformer._transform_block(relevant_items[0])

        # Find except clauses and finally block
        except_blocks = []
        finally_block_statements = None

        # Process remaining items
        for item in relevant_items[1:]:
            if isinstance(item, ExceptBlock):
                # Already transformed except clause
                except_blocks.append(item)
            elif hasattr(item, "data") and item.data == "block":
                # This is the finally block
                finally_block_statements = self.main_transformer._transform_block(item)
            elif hasattr(item, "data") and item.data == "except_clause":
                # Transform except clause
                except_block = self.except_clause(item.children)
                except_blocks.append(except_block)

        return TryBlock(
            body=try_body,
            except_blocks=except_blocks,
            finally_block=finally_block_statements,
        )

    def except_clause(self, items):
        """Transform an except clause into an ExceptBlock node."""
        relevant_items = self.main_transformer._filter_relevant_items(items)

        exception_type = None
        variable_name = None
        body = []

        # Process items to extract exception spec and body
        for item in relevant_items:
            if hasattr(item, "data") and item.data == "block":
                # This is the except body
                body = self.main_transformer._transform_block(item)
            elif hasattr(item, "data") and item.data == "except_spec":
                # Process exception specification
                exception_type, variable_name = self.except_spec(item.children)

        return ExceptBlock(body=body, exception_type=exception_type, variable_name=variable_name, location=None)

    def except_spec(self, items):
        """Transform exception specification into (exception_type, variable_name)."""
        relevant_items = self.main_transformer._filter_relevant_items(items)

        exception_type = None
        variable_name = None

        for _i, item in enumerate(relevant_items):
            if isinstance(item, Token) and item.type == "NAME":
                # This is the variable name from 'as NAME'
                variable_name = item.value
            elif hasattr(item, "data") and item.data == "exception_type":
                # Transform exception type
                exception_type = self.exception_type(item.children)
            else:
                # Direct expression for exception type
                exception_type = self.expression_transformer.expression([item])

        return exception_type, variable_name

    def exception_type(self, items):
        """Transform exception type (single expr or tuple of exprs)."""
        relevant_items = self.main_transformer._filter_relevant_items(items)

        if len(relevant_items) == 1:
            # Single exception type
            return self.expression_transformer.expression([relevant_items[0]])
        else:
            # Multiple exception types in parentheses
            # Look for exception_list
            for item in relevant_items:
                if hasattr(item, "data") and item.data == "exception_list":
                    return self.exception_list(item.children)

            # Fallback: transform as expression
            return self.expression_transformer.expression(relevant_items)

    def exception_list(self, items):
        """Transform a list of exception types into a TupleLiteral."""
        from dana.core.lang.ast import TupleLiteral

        relevant_items = self.main_transformer._filter_relevant_items(items)
        exception_types = []

        for item in relevant_items:
            if isinstance(item, Token) and item.type == "COMMA":
                continue
            exception_types.append(self.expression_transformer.expression([item]))

        return TupleLiteral(items=exception_types)
