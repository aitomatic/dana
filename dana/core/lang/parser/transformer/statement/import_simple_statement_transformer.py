"""
Import and simple statement transformer for Dana language parsing.

This module handles all import and simple statement transformations, including:
- Import statements (import, from import)
- Simple statements (return, break, continue, pass, raise, assert)
- Expression statements
- Argument handling utilities

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from lark import Token, Tree

from dana.core.lang.ast import (
    ImportFromStatement,
    ImportStatement,
)
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer
from dana.core.lang.parser.transformer.statement.statement_helpers import SimpleStatementHelper


class ImportSimpleStatementTransformer(BaseTransformer):
    """
    Handles import and simple statement transformations for the Dana language.
    Converts import/simple statement parse trees into corresponding AST nodes.
    """

    def __init__(self, main_transformer):
        """Initialize with reference to main transformer for shared utilities."""
        super().__init__()
        self.main_transformer = main_transformer
        self.expression_transformer = main_transformer.expression_transformer

    # === Simple Statements ===

    def expr_stmt(self, items):
        """Transform a bare expression statement (expr_stmt) into an Expression AST node."""
        return self.expression_transformer.expression(items)

    def return_stmt(self, items):
        """Transform a return statement rule into a ReturnStatement node."""
        return SimpleStatementHelper.create_return_statement(items, self.expression_transformer)

    def break_stmt(self, items):
        """Transform a break statement rule into a BreakStatement node."""
        return SimpleStatementHelper.create_break_statement()

    def continue_stmt(self, items):
        """Transform a continue statement rule into a ContinueStatement node."""
        return SimpleStatementHelper.create_continue_statement()

    def pass_stmt(self, items):
        """Transform a pass statement rule into a PassStatement node."""
        return SimpleStatementHelper.create_pass_statement()

    def raise_stmt(self, items):
        """Transform a raise statement rule into a RaiseStatement node."""
        return SimpleStatementHelper.create_raise_statement(items, self.expression_transformer)

    def assert_stmt(self, items):
        """Transform an assert statement rule into an AssertStatement node."""
        return SimpleStatementHelper.create_assert_statement(items, self.expression_transformer)

    # === Import Statements ===

    def import_stmt(self, items):
        """Transform an import statement rule into an ImportStatement or ImportFromStatement node."""
        # The import_stmt rule now delegates to either simple_import or from_import
        return items[0]

    def simple_import(self, items):
        """Transform a simple_import rule into an ImportStatement node.

        Grammar:
            simple_import: IMPORT module_path ["as" NAME]
            module_path: NAME ("." NAME)*
        """
        # Get the module_path (first item, IMPORT token is already consumed by grammar)
        module_path = items[0]

        # Extract the module path from the Tree
        if isinstance(module_path, Tree) and getattr(module_path, "data", None) == "module_path":
            parts = []
            for child in module_path.children:
                if isinstance(child, Token):
                    parts.append(child.value)
                elif hasattr(child, "value"):
                    parts.append(child.value)
            module = ".".join(parts)
        elif isinstance(module_path, Token):
            module = module_path.value
        else:
            # Fallback to string representation
            module = str(module_path)

        # Handle alias: if we have AS token, the alias is the next item
        alias = None
        if len(items) > 1:
            # Check if items[1] is the AS token
            if isinstance(items[1], Token) and items[1].type == "AS":
                # The alias name should be in items[2]
                if len(items) > 2 and hasattr(items[2], "value"):
                    alias = items[2].value
                elif len(items) > 2:
                    alias = str(items[2])
            else:
                # Fallback: treat items[1] as the alias directly
                if hasattr(items[1], "value"):
                    alias = items[1].value
                elif items[1] is not None:
                    alias = str(items[1])

        return ImportStatement(module=module, alias=alias)

    def from_import(self, items):
        """Transform a from_import rule into an ImportFromStatement node.

        Grammar:
            from_import: FROM (relative_module_path | module_path) IMPORT (import_name_list | STAR)
            import_name_list: import_name ("," import_name)*
            import_name: NAME ["as" NAME]
            module_path: NAME ("." NAME)*
            relative_module_path: DOT+ [module_path]

        Parse tree structure: [FROM, module_path_or_relative, IMPORT, import_name_list_tree_or_star]
        """
        # Get the module_path or relative_module_path (first item, FROM token already consumed)
        module_path_item = items[0]

        # Handle relative_module_path (starts with dots)
        if isinstance(module_path_item, Tree) and getattr(module_path_item, "data", None) == "relative_module_path":
            # Extract dots and optional module path
            dots = []
            module_parts = []

            for child in module_path_item.children:
                if isinstance(child, Token) and child.type == "DOT":
                    dots.append(".")
                elif isinstance(child, Tree) and getattr(child, "data", None) == "module_path":
                    # Extract module path parts
                    for subchild in child.children:
                        if isinstance(subchild, Token):
                            module_parts.append(subchild.value)
                        elif hasattr(subchild, "value"):
                            module_parts.append(subchild.value)
                elif isinstance(child, Token):
                    module_parts.append(child.value)

            # Build relative module name
            module = "".join(dots)
            if module_parts:
                module += ".".join(module_parts)
        else:
            # Handle absolute module_path (existing logic)
            if isinstance(module_path_item, Tree) and getattr(module_path_item, "data", None) == "module_path":
                parts = []
                for child in module_path_item.children:
                    if isinstance(child, Token):
                        parts.append(child.value)
                    elif hasattr(child, "value"):
                        parts.append(child.value)
                module = ".".join(parts)
            elif isinstance(module_path_item, Token):
                module = module_path_item.value
            else:
                # Fallback to string representation
                module = str(module_path_item)

        # Get the import_name_list or STAR (third item after FROM and module_path)
        # Structure: [module_path_or_relative, import_name_list_tree_or_star]
        import_names = []
        is_star_import = False

        if len(items) >= 2:
            import_item = items[1]

            # Check if it's a star import
            if isinstance(import_item, Token) and import_item.type == "STAR":
                is_star_import = True
                import_names = []  # Empty list for star imports
            elif isinstance(import_item, Tree) and getattr(import_item, "data", None) == "import_name_list":
                # Extract all import names from the list
                for child in import_item.children:
                    if isinstance(child, Tree) and getattr(child, "data", None) == "import_name":
                        # Extract name and optional alias from import_name
                        name = ""
                        alias = None

                        for subchild in child.children:
                            if isinstance(subchild, Token) and subchild.type == "NAME":
                                if name == "":  # First NAME token is the import name
                                    name = subchild.value
                                else:  # Second NAME token (after AS) is the alias
                                    alias = subchild.value
                            elif isinstance(subchild, Token) and subchild.type == "AS":
                                # AS token, next token will be the alias
                                pass

                        if name:  # Only add if we found a valid name
                            import_names.append((name, alias))
            else:
                # Fallback: treat as single import (backward compatibility)
                if isinstance(import_item, Token) and import_item.type == "NAME":
                    import_names.append((import_item.value, None))

        # If no names were extracted and not a star import, create a default empty list
        if not import_names and not is_star_import:
            import_names = [("", None)]

        return ImportFromStatement(module=module, names=import_names, is_star_import=is_star_import)

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
