from abc import ABC, abstractmethod

from dana.common.utils.misc import Misc, ParsedArgKwargsResults


class BaseTransport(ABC):
    """Abstract base class for MCP transport implementations."""

    @abstractmethod
    def __init__(self):
        """Initialize the transport."""
        pass

    @classmethod
    def parse_init_params(cls, *args, **kwargs) -> ParsedArgKwargsResults:
        """Get the initialization parameters for this transport."""
        return Misc.parse_args_kwargs(cls.__init__, *args, **kwargs)
