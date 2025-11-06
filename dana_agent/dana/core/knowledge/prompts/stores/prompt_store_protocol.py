from abc import abstractmethod
from typing import Protocol

from dana.common.schemas import PromptVersionSnapshot
from dana.config.storage_config import StorageConfig


class PromptStoreProtocol(Protocol):
    def __init__(self, config: StorageConfig):
        ...


    @abstractmethod
    def version_exists(self) -> bool: ...
    
    @property
    @abstractmethod
    def version(self) -> str: ...

    @abstractmethod
    def get_active(self, error_if_not_found: bool = True) -> PromptVersionSnapshot | None: ...

    @abstractmethod
    def list_versions(self) -> list[str]: ...

    @abstractmethod
    def load_snapshot(self, version: str, error_if_not_found: bool = True) -> PromptVersionSnapshot | None: ...

    @abstractmethod
    def set_active(self, version: str) -> None: ...

    @abstractmethod
    def create_snapshot(self, content: str, provenance: dict, metrics: dict) -> PromptVersionSnapshot: ...