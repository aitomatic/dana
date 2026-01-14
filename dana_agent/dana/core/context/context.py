"""Context dataclass for assembled LLM context.

Represents the result of context assembly from multiple sources,
tracking token usage and which sources contributed.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Context:
    """Assembled context ready for LLM.

    Attributes:
        text: The assembled context text
        tokens_used: Number of tokens in the assembled context
        sources_used: Names of sources that contributed to the context
        budget: The token budget that was used for assembly
    """

    text: str
    tokens_used: int
    sources_used: list[str]
    budget: int
