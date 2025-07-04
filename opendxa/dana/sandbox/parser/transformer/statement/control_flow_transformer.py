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

from dana.core.lang.parser.ast import (
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

        from dana.core.lang.parser.ast import Conditional

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

        from dana.core.lang.parser.ast import Expression

        # Filter out irrelevant items (None, comments, etc.)
        relevant_items = self.main_transformer._filter_relevant_items(items)

        # Get the loop variable (target)
        target = Identifier(name=relevant_items[0].value if isinstance(relevant_items[0], Token) else str(relevant_items[0]))

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

        # Find except and finally blocks
        except_block_statements = []
        finally_block_statements = []
        exception_type = None

        # Look for except block (should be the second or third relevant item)
        if len(relevant_items) >= 2:
            # Check if we have an exception type expression
            # If items[1] is not a block-like structure, it might be an exception type
            second_item = relevant_items[1]
            if hasattr(second_item, "data") and second_item.data == "block":
                # No exception type, this is the except block
                except_block_statements = self.main_transformer._transform_block(second_item)
            else:
                # This might be an exception type, except block should be next
                exception_type = second_item
                if len(relevant_items) >= 3:
                    except_block_statements = self.main_transformer._transform_block(relevant_items[2])

        # Look for finally block
        finally_index = 3 if exception_type else 2
        if len(relevant_items) > finally_index:
            finally_block_statements = self.main_transformer._transform_block(relevant_items[finally_index])

        # Create ExceptBlock object
        except_blocks = []
        if except_block_statements:
            except_block = ExceptBlock(body=except_block_statements, exception_type=exception_type, location=None)
            except_blocks.append(except_block)

        return TryBlock(
            body=try_body,
            except_blocks=except_blocks,
            finally_block=finally_block_statements if finally_block_statements else None,
        )
