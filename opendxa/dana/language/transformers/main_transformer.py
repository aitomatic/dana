"""Main transformer integrating all specialized transformers for DANA language parsing."""

from lark import Transformer

from opendxa.dana.language.transformers.expression_transformer import ExpressionTransformer
from opendxa.dana.language.transformers.fstring_transformer import FStringTransformer
from opendxa.dana.language.transformers.statement_transformer import StatementTransformer


class DanaTransformerNew(Transformer):
    """New main transformer class that delegates to specialized transformers.

    This transformer integrates all the specialized transformers and
    delegates method calls to the appropriate specialized transformer.
    """

    def __init__(self):
        """Initialize all specialized transformers."""
        super().__init__()
        self._statement_transformer = StatementTransformer()
        self._expression_transformer = ExpressionTransformer()
        self._fstring_transformer = FStringTransformer()

    def __getattr__(self, name):
        """Delegate method calls to the appropriate specialized transformer."""
        # Try to find the method in the specialized transformers
        for transformer in [self._statement_transformer, self._expression_transformer, self._fstring_transformer]:
            if hasattr(transformer, name):
                return getattr(transformer, name)

        # If method not found, raise AttributeError
        raise AttributeError(f"'DanaTransformerNew' has no attribute '{name}'")
