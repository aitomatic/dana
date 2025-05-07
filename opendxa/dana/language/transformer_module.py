"""Transformer module for DANA language parsing.

This module provides access to the transformer classes used by the DANA parser.
"""

import logging

from opendxa.dana.language.transformers.main_transformer import DanaTransformerNew

logger = logging.getLogger("dana")

def get_transformer_class():
    """Get the transformer class for DANA language parsing."""
    return DanaTransformerNew