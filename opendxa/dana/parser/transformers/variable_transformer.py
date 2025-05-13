"""Variable transformer for DANA language parsing.

Handles variable, identifier, and access patterns as defined in the DANA grammar.
Covers:
    - variable: scoped_var | simple_name | dotted_access
    - simple_name: NAME
    - dotted_access: simple_name ("." NAME)+
    - scoped_var: scope_prefix ":" (simple_name | dotted_access)
    - scope_prefix: "local" | "private" | "public" | "system"

Follows the style and best practices of StatementTransformer and ExpressionTransformer.
"""

from lark import Token, Tree

from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.parser.ast import Identifier
from opendxa.dana.parser.transformers.base_transformer import BaseTransformer


class VariableTransformer(BaseTransformer):
    """
    Transforms variable and identifier-related parse tree nodes into AST Identifier nodes.

    Handles all variable access patterns in the DANA grammar, including scoped, simple, and dotted variables.
    Methods are grouped by grammar hierarchy for clarity and maintainability.
    """

    # === Entry Point ===
    def variable(self, items):
        """
        Transform a variable rule into an Identifier node.
        Grammar: variable: scoped_var | simple_name | dotted_access
        """
        return self.get_leaf_node(items[0])

    # === Grammar Rule Methods ===
    def scoped_var(self, items):
        """
        Transform a scoped variable (e.g., 'private:x' or 'system:foo.bar') into an Identifier node.
        Grammar: scoped_var: scope_prefix ":" (simple_name | dotted_access)
        Example: private:x -> Identifier(name='private.x')
                 system:foo.bar -> Identifier(name='system.foo.bar')
        """
        scope_item = items[0]
        var = items[1]
        # Extract the scope string from the first child token of scope_prefix
        if isinstance(scope_item, Tree) and scope_item.children and hasattr(scope_item.children[0], "value"):
            scope = scope_item.children[0].value
        else:
            scope = self._extract_name(scope_item)

        # Extract the raw variable name, bypassing _insert_scope_if_missing
        def raw_name(item):
            if isinstance(item, Identifier):
                # Remove any leading 'local.'
                return item.name[6:] if item.name.startswith("local.") else item.name
            if isinstance(item, Token):
                return item.value
            if isinstance(item, Tree):
                # Recursively extract from first child
                if item.children:
                    return raw_name(item.children[0])
                return str(item)
            return str(item)

        var_name = raw_name(var)
        name = f"{scope}.{var_name}"
        return Identifier(name=name)

    def simple_name(self, items):
        """
        Transform a simple variable name (NAME) into an Identifier node, inserting local scope if missing.
        Grammar: simple_name: NAME
        Example: x -> Identifier(name='local.x')
        """
        name = self._extract_name(items[0])
        name = self._insert_scope_if_missing(name)
        return Identifier(name=name)

    def dotted_access(self, items):
        """
        Transform a dotted access chain (e.g., 'foo.bar.baz') into an Identifier node, inserting local scope if missing.
        Grammar: dotted_access: simple_name ("." NAME)+
        Example: foo.bar -> Identifier(name='local.foo.bar')
        """
        parts = [self._extract_name(items[0])] + [self._extract_name(item) for item in items[1:]]
        name = self._join_dotted(parts)
        name = self._insert_scope_if_missing(name)
        return Identifier(name=name)

    # === Utility/Compatibility Method ===
    def identifier(self, items):
        """
        Transform an identifier (simple or dotted, with optional scope) into an Identifier node.
        This is a utility for compatibility with other transformers.
        If no scope prefix is present, inserts local scope.
        Example: foo -> Identifier(name='local.foo')
                 private:foo.bar -> Identifier(name='private.foo.bar')
        """
        parts = [self._extract_name(item) for item in items]
        name = self._join_dotted(parts)
        name = self._insert_scope_if_missing(name)
        return Identifier(name=name)

    # === Helper Methods ===
    def _extract_name(self, item):
        """
        Extract the string name from a Token, Identifier, str, or Tree.
        Handles Tree nodes for scope_prefix by extracting the value from their first Token child.
        """
        if isinstance(item, Token):
            return item.value
        if isinstance(item, Identifier):
            return item.name
        if isinstance(item, Tree):
            # If this is a scope_prefix or similar, extract the value from the first Token child
            for child in item.children:
                if isinstance(child, Token):
                    return child.value
                if isinstance(child, Identifier):
                    return child.name
                if isinstance(child, Tree):
                    return self._extract_name(child)
            return str(item)
        return str(item)

    def _join_dotted(self, parts):
        """
        Join a list of name parts with dots, e.g., ['foo', 'bar'] -> 'foo.bar'.
        """
        return ".".join(parts)

    def _insert_scope_if_missing(self, name):
        """
        Insert 'local.' scope prefix if name does not already start with a known scope.
        """
        if not any(name.startswith(prefix + ".") for prefix in RuntimeScopes.ALL):
            return f"local.{name}"
        return name
