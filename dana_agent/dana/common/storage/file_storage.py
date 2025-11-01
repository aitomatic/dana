from collections import defaultdict
from pathlib import Path
from threading import Lock

from dana.config import MAIN_CFG
from dana.config.storage_config import FileStorageConfig

from .abstract_storage import AbstractStorage


class FileStorage(AbstractStorage):
    _locks: dict[str, Lock] = defaultdict(Lock)

    def __init__(self, config: FileStorageConfig):
        self._config = config
        self._workspace_folder = Path(self._config.workspace_folder)
        with self._locks[str(self._workspace_folder)]:
            if not self._workspace_folder.exists():
                self._workspace_folder.mkdir(parents=True, exist_ok=True)

    def load(self, key: str) -> str | None:
        target_path = self._workspace_folder / key
        if not target_path.exists():
            return None
        return target_path.read_text()

    def persist(self, key: str, value: str) -> bool:
        # Thread-safe operation to avoid race conditions when writing to the same file
        with self._locks[key]:
            target_path = self._workspace_folder / key
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(value)
            return True