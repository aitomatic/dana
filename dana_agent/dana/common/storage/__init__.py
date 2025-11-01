from dana.config.storage_config import FileStorageConfig

from .abstract_storage import AbstractStorage
from .file_storage import FileStorage
from .storage_factory import StorageFactory


# DEFAULT STORAGE CONFIGURATION
StorageFactory.configure(storage_cls=FileStorage, config=FileStorageConfig())

__all__ = ["AbstractStorage", "FileStorage", "StorageFactory"]