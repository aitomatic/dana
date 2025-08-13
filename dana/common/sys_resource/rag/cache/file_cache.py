import json
import os
import pickle
from typing import override

from dana.common.sys_resource.rag.cache.base_cache import AbstractCache
from dana.common.utils.misc import Misc


class AbstractFileCache(AbstractCache):
    def __init__(self, cache_folder: str):
        super().__init__()
        self.cache_folder = cache_folder
        os.makedirs(self.cache_folder, exist_ok=True)

    def _get_cache_file_path(self, key: str):
        hash_key = Misc.get_hash(key)
        return os.path.join(self.cache_folder, f"{hash_key}.cache")

    def __contains__(self, key: str):
        cache_file_path = self._get_cache_file_path(key)
        return os.path.exists(cache_file_path)

    def clear(self):
        for file in os.listdir(self.cache_folder):
            os.remove(os.path.join(self.cache_folder, file))


class PickleFileCache(AbstractFileCache):
    @override
    def get(self, key: str):
        try:
            cache_file_path = self._get_cache_file_path(key)
            if os.path.exists(cache_file_path):
                with open(cache_file_path, "rb") as file:
                    return pickle.load(file)
        except Exception as e:
            self.logger.error(f"Error getting cache for key {key}: {e}")
        return None

    @override
    def set(self, key: str, value):
        if value is None:
            return
        try:
            cache_file_path = self._get_cache_file_path(key)
            with open(cache_file_path, "wb") as file:
                pickle.dump(value, file)
        except Exception as e:
            self.logger.error(f"Error setting cache for key {key}: {e}")


class JsonFileCache(AbstractFileCache):
    @override
    def get(self, key: str):
        try:
            cache_file_path = self._get_cache_file_path(key)
            if os.path.exists(cache_file_path):
                with open(cache_file_path) as file:
                    return json.load(file)
        except Exception as e:
            self.logger.error(f"Error getting cache for key {key}: {e}")
        return None

    @override
    def set(self, key: str, value):
        if value is None:
            return
        try:
            cache_file_path = self._get_cache_file_path(key)
            with open(cache_file_path, "w") as file:
                json.dump(value, file)
        except Exception as e:
            self.logger.error(f"Error setting cache for key {key}: {e}")
