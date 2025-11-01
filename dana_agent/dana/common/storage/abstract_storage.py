from abc import ABC, abstractmethod

from dana.config.storage_config import StorageConfig


class AbstractStorage(ABC):
    def __init__(self, config: StorageConfig):
        self._config = config

    @abstractmethod
    def load(self, key: str) -> str | None:
        pass

    @abstractmethod
    def persist(self, key: str, value: str) -> bool:
        pass