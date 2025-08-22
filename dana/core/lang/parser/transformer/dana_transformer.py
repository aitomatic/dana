"""Main transformer integrating all specialized transformers for Dana language parsing."""

from lark import Transformer

from dana.core.lang.parser.transformer.expression_transformer import ExpressionTransformer
from dana.core.lang.parser.transformer.fstring_transformer import FStringTransformer
from dana.core.lang.parser.transformer.statement_transformer import StatementTransformer
from dana.core.lang.parser.transformer.variable_transformer import VariableTransformer


class DanaTransformer(Transformer):
    """Main transformer that delegates to specialized transformers for different rule types."""

    def __init__(self):
        """Initialize the main transformer and its specialized components.

        DanaTransformer acts as a facade that routes transformation requests to appropriate
        specialized transformers. Each major category of the Dana grammar (statements, expressions,
        variables) is handled by its own class, and DanaTransformer delegates to them as needed.
        """
        super().__init__()
        # Initialize expression transformer first
        self.expression_transformer = ExpressionTransformer(self)
        # Initialize statement transformer with reference to this main transformer
        self.statement_transformer = StatementTransformer(self)
        self.fstring_transformer = FStringTransformer()
        self.variable_transformer = VariableTransformer()
        self.current_filename = None  # Track current filename for error reporting

    def set_filename(self, filename: str | None) -> None:
        """Set the current filename for all transformers."""
        self.current_filename = filename
        # Propagate to all sub-transformers
        if hasattr(self.statement_transformer, "set_filename"):
            self.statement_transformer.set_filename(filename)
        if hasattr(self.expression_transformer, "set_filename"):
            self.expression_transformer.set_filename(filename)
        if hasattr(self.fstring_transformer, "set_filename"):
            self.fstring_transformer.set_filename(filename)
        if hasattr(self.variable_transformer, "set_filename"):
            self.variable_transformer.set_filename(filename)

    def transform(self, tree):
        """Transform the parse tree with filename context."""
        return super().transform(tree)

    def __getattr__(self, name):
        """
        Delegate method calls to the appropriate specialized transformer. When a transformation method
        is called on DanaTransformer that it doesn't directly implement, this method looks for it
        in the specialized transformers.
        """
        # Prefer function-definition transformer first (many statement rules land there)
        possible_transformers = []
        # Some rules are implemented on the statement transformer's function sub-transformer
        if hasattr(self.statement_transformer, "function_definition_transformer"):
            possible_transformers.append(self.statement_transformer.function_definition_transformer)
        # Then check other transformers
        possible_transformers.extend(
            [
                self.statement_transformer,
                self.expression_transformer,
                self.fstring_transformer,
                self.variable_transformer,
            ]
        )

        for transformer in possible_transformers:
            if hasattr(transformer, name):
                return getattr(transformer, name)

        # If method not found, raise AttributeError
        raise AttributeError(f"'DanaTransformer' has no attribute '{name}'")
