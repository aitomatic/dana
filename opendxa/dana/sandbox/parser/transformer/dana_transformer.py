"""Main transformer integrating all specialized transformers for Dana language parsing."""

from lark import Transformer

from dana.core.lang.parser.transformer.expression_transformer import ExpressionTransformer
from dana.core.lang.parser.transformer.fstring_transformer import FStringTransformer
from dana.core.lang.parser.transformer.statement_transformer import StatementTransformer
from dana.core.lang.parser.transformer.variable_transformer import VariableTransformer


class DanaTransformer(Transformer):
    """
    Unified Dana AST transformer that delegates to specialized transformers for statements, expressions,
    f-strings, and variables.

    When Lark calls a transformation method (e.g., assignment, expr, f_string, variable), this class
    automatically forwards the call to the appropriate specialized transformer. This keeps grammar logic
    modular and maintainable, while providing a single entry point for parsing.
    """

    def __init__(self):
        """
        Initialize all specialized transformers. Each grammar domain (statements, expressions, f-strings,
        variables) is handled by its own class, and DanaTransformer delegates to them as needed.
        """
        super().__init__()
        self._statement_transformer = StatementTransformer()
        self._expression_transformer = ExpressionTransformer()
        self._fstring_transformer = FStringTransformer()
        self._variable_transformer = VariableTransformer()

    def __getattr__(self, name):
        """
        Delegate method calls to the appropriate specialized transformer. When a transformation method
        is not found directly on DanaTransformer, this will search each sub-transformer in order and
        return the first match.
        """
        # Check each specialized transformer to see if it implements the requested method.
        # If found, delegate the call to that transformer. This enables seamless routing of
        # transformation methods (e.g., assignment, expr, f_string, variable) to the correct handler.
        for transformer in [
            self._statement_transformer,
            self._expression_transformer,
            self._fstring_transformer,
            self._variable_transformer,
        ]:
            if hasattr(transformer, name):
                return getattr(transformer, name)

        # If method not found, raise AttributeError
        raise AttributeError(f"'DanaTransformer' has no attribute '{name}'")
