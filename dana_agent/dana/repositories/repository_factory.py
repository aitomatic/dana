from enum import StrEnum
from typing import TypeVar

from dana.config.storage_config import FileStorageConfig, StorageConfig

from .local_file_repository import LocalEventRepository, LocalLearningRepository, LocalPromptRepository, LocalTimelineRepository
from .repository_protocol import EventRepositoryProtocol, LearningRepositoryProtocol, PromptRepositoryProtocol, TimelineRepositoryProtocol


RepositoryProtocol = TypeVar(
    "RepositoryProtocol", PromptRepositoryProtocol, TimelineRepositoryProtocol, EventRepositoryProtocol, LearningRepositoryProtocol
)


class RepositoryType(StrEnum):
    PROMPT = "prompt"
    TIMELINE = "timeline"
    EVENT = "event"
    LEARNING = "learning"


class RepositoryFactory:
    def __init__(self):
        self._creators = {
            RepositoryType.PROMPT: (LocalPromptRepository, FileStorageConfig()),
            RepositoryType.TIMELINE: (LocalTimelineRepository, FileStorageConfig()),
            RepositoryType.EVENT: (LocalEventRepository, FileStorageConfig()),
            RepositoryType.LEARNING: (LocalLearningRepository, FileStorageConfig()),
        }

    def register(self, type: RepositoryType, creator: type[RepositoryProtocol], storage_config: StorageConfig) -> None:
        self._creators[type] = (creator, storage_config)

    def create(self, type: RepositoryType, **kwargs) -> RepositoryProtocol:
        creator, storage_config = self._creators[type]
        return creator.instantiate(storage_config, **kwargs)


DEFAULT_REPOSITORY_FACTORY = RepositoryFactory()
