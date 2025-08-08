from abc import ABC, abstractmethod


class AbstractHandler(ABC):
    @abstractmethod
    def handle(self, *args, **kwargs) -> str:
        pass
