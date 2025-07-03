from abc import ABC

from opendxa.common.utils.misc import Misc, ParsedArgKwargsResults


class BaseTransport(ABC):
    @classmethod
    def parse_init_params(cls, *args, **kwargs) -> ParsedArgKwargsResults:
        """Get the initialization parameters for this transport."""
        return Misc.parse_args_kwargs(cls.__init__, *args, **kwargs)
