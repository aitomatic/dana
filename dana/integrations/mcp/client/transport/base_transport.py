from abc import ABC

from dana.common.utils.misc import Misc, ParsedArgKwargsResults


class BaseTransport(ABC):
    """Abstract base class for MCP transport implementations."""

    # Removed abstract __init__ method as it creates an unclear API contract.

    @classmethod
    def parse_init_params(cls, *args, **kwargs) -> ParsedArgKwargsResults:
        """Get the initialization parameters for this transport."""
        return Misc.parse_args_kwargs(cls.__init__, *args, **kwargs)
