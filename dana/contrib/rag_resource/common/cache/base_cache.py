from abc import ABC, abstractmethod

from dana.common.mixins import Loggable


class AbstractCache(ABC, Loggable):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value):
        pass


class BaseCache(AbstractCache):
    def __init__(self):
        super().__init__()
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value):
        if value is None:
            return
        self._cache[key] = value

    def clear(self):
        self._cache.clear()

    def __contains__(self, key):
        return key in self._cache
