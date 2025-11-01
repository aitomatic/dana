
from threading import Lock

from dana.config.storage_config import FileStorageConfig, StorageConfig

from .abstract_storage import AbstractStorage
from .file_storage import FileStorage


class StorageFactory:
    """Factory for creating and managing storage instances."""
    
    _instance: AbstractStorage | None = None
    _storage_cls: type[AbstractStorage] | None = None
    _config: StorageConfig | None = None
    _lock: Lock = Lock()
    
    @classmethod
    def configure(cls, storage_cls: type[AbstractStorage], config: StorageConfig) -> None:
        """
        Configure the storage factory with type and parameters.
        """
        with cls._lock:
            cls._config = config
            cls._storage_cls = storage_cls
            cls._create_storage()
    
    @classmethod
    def get_storage(cls) -> AbstractStorage:
        """Get or create the storage instance (singleton)."""
        if cls._instance is None:
            with cls._lock:
                # Second check with lock (ensure only one thread creates instance)
                if cls._instance is None:
                    cls._instance = cls._create_storage()
        return cls._instance
    
    @classmethod
    def _create_storage(cls) -> AbstractStorage:
        """
        Create a storage instance based on configuration.
        Use lock to avoid race conditions when creating the storage instance.
        """
        if cls._storage_cls and cls._config:
            # Default to file storage
            return cls._storage_cls(config=cls._config)
        return FileStorage(config=FileStorageConfig())
            
    
    @classmethod
    def set_storage(cls, storage: AbstractStorage) -> AbstractStorage | None:
        """Manually set storage instance (useful for testing)."""
        with cls._lock:
            old = cls._instance
            cls._instance = storage
            cls._storage_cls = type(storage)
            cls._config = storage._config
        return old
    
    @classmethod
    def reset(cls) -> None:
        """Reset factory to initial state."""
        with cls._lock:
            cls._instance = None
            cls._storage_cls = None
            cls._config = None