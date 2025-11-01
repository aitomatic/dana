from abc import abstractmethod
from typing import Protocol

from dana.common.storage import AbstractStorage, StorageFactory


class Persistable(Protocol):
    def __init__(self, **kwargs):
        _storage = kwargs.get("storage")
        if _storage is None or not isinstance(_storage, AbstractStorage):
            _storage = StorageFactory.get_storage()
        self._storage = _storage

    @abstractmethod
    def persist(self) -> None:
        pass

    @abstractmethod
    def load(self) -> str | None:
        pass