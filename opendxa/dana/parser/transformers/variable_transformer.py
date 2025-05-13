"""Variable transformer for DANA language parsing."""

from lark import Token

from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.parser.ast import Identifier
from opendxa.dana.parser.transformers.base_transformer import BaseTransformer


class VariableTransformer(BaseTransformer):
    """Transformer for variable and identifier-related AST nodes."""

    def variable(self, items):
        # variable: scoped_var | simple_name | dotted_access
        return self._unwrap_tree(items[0])

    def simple_name(self, items):
        # simple_name: NAME
        name = items[0].value if isinstance(items[0], Token) else str(items[0])
        # Add local scope if not present
        if name not in RuntimeScopes.ALL:
            name = self._insert_local_scope(name)
        return Identifier(name=name)

    def dotted_access(self, items):
        # dotted_access: simple_name ("." NAME)+
        parts = []
        for item in items:
            if isinstance(item, Token):
                parts.append(item.value)
            elif isinstance(item, Identifier):
                parts.append(item.name)
            else:
                parts.append(str(item))
        name = ".".join(parts)
        return Identifier(name=name)

    def scoped_var(self, items):
        # scoped_var: scope_prefix ":" (simple_name | dotted_access)
        scope = items[0].value if isinstance(items[0], Token) else str(items[0])
        var = items[1]
        if isinstance(var, Identifier):
            name = var.name
        elif isinstance(var, Token):
            name = var.value
        else:
            name = str(var)
        # Prepend scope
        name = f"{scope}.{name}"
        return Identifier(name=name)

    def identifier(self, items):
        # identifier: handles both simple and dotted names, with optional scope
        parts = []
        for item in items:
            if isinstance(item, Token):
                parts.append(item.value)
        # If no scope prefix, add local
        if parts and parts[0] not in RuntimeScopes.ALL:
            if len(parts) == 1:
                parts = ["local"] + parts
        name = ".".join(parts)
        return Identifier(name=name)
