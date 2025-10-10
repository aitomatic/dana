from .cache import AbstractCache, BaseCache, JsonFileCache, PickleFileCache
from .rag_resource import RAGResource
from .rag_resource_v2 import RAGResourceV2

_global_rag_resource = None


def get_global_rag_resource():
    global _global_rag_resource
    if _global_rag_resource is None:
        _global_rag_resource = RAGResourceV2(sources=[])
    return _global_rag_resource


__all__ = ["RAGResource", "BaseCache", "AbstractCache", "PickleFileCache", "JsonFileCache"]
