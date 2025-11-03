from abc import abstractmethod
from typing import Protocol


class Persistable(Protocol):

    @abstractmethod
    def persist(self) -> None:
        pass

    @abstractmethod
    def load(self) -> str | None:
        pass