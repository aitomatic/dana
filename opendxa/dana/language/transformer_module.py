"""Transformer module for DANA language parsing.

This module provides access to the transformer classes used by the DANA parser.
"""

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.language.transformers.main_transformer import DanaTransformerNew


class TransformerModule(Loggable):
    """Module for accessing DANA language transformers."""

    def __init__(self):
        """Initialize the transformer module."""
        super().__init__(prefix="dana.transformer")

    def get_transformer_class(self):
        """Get the transformer class for DANA language parsing."""
        return DanaTransformerNew


# Create a singleton instance
transformer_module = TransformerModule()


def get_transformer_class():
    """Get the transformer class for DANA language parsing."""
    return transformer_module.get_transformer_class()
