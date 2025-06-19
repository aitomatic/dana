from abc import ABC, abstractmethod

from opendxa.common.utils.misc import Misc, ParsedArgKwargsResults


class BaseTransport(ABC):
    @classmethod
    def parse_init_params(cls, *args, **kwargs) -> ParsedArgKwargsResults:
        """Get the initialization parameters for this transport."""
        return Misc.parse_args_kwargs(cls.__init__, *args, **kwargs)

    @abstractmethod
    def connect(self) -> None:
        """Connect to the transport."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the transport."""
        pass
