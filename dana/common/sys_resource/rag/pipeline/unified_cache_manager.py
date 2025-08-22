import asyncio
import os
from pathlib import Path
from typing import cast

from llama_index.core import Document, VectorStoreIndex, load_index_from_storage
from llama_index.core.storage.storage_context import StorageContext

from dana.common.mixins.loggable import Loggable
from dana.common.sys_resource.rag.cache import JsonFileCache
from dana.common.utils.misc import Misc


class UnifiedCacheManager(Loggable):
    def __init__(self, cache_dir: str = ".cache/rag"):
        super().__init__()
        self.cache_dir = cache_dir
        self.doc_cache = self.create_cache(self.cache_dir, "documents")
        self.indices_cache_path = os.path.join(self.cache_dir, "indices")
        Path(self.indices_cache_path).mkdir(parents=True, exist_ok=True)
        self.combined_index_cache_path = os.path.join(self.cache_dir, "combined_index")
        Path(self.combined_index_cache_path).mkdir(parents=True, exist_ok=True)

    def create_cache(self, cache_dir: str, cache_name: str):
        cache_path = Path(cache_dir) / cache_name
        if not cache_path.exists():
            cache_path.mkdir(parents=True, exist_ok=True)
        return JsonFileCache(str(cache_path))

    async def set_docs_by_source(self, docs_by_source: dict[str, list[Document]]):
        tasks = []
        for source, docs in docs_by_source.items():
            tasks.append(asyncio.to_thread(self.doc_cache.set, source, [doc.to_dict() for doc in docs]))
        await asyncio.gather(*tasks)

    async def get_docs_by_source(self, sources: list[str]) -> dict[str, list[Document | None] | None]:
        try:
            tasks = []
            for source in sources:
                tasks.append(asyncio.to_thread(self.doc_cache.get, source))
            results = await asyncio.gather(*tasks)
            return {
                source: [Document.from_dict(doc) for doc in docs] if docs is not None else None
                for source, docs in zip(sources, results, strict=False)
            }
        except Exception as e:
            self.error(f"Error getting documents from {sources}: {e}")
            return {source: None for source in sources}

    async def set_indicies_by_source(self, indices_by_source: dict[str, VectorStoreIndex]):
        tasks = []
        for source, index in indices_by_source.items():
            hash_key = Misc.get_hash(source)
            tasks.append(asyncio.to_thread(index.storage_context.persist, persist_dir=os.path.join(self.indices_cache_path, hash_key)))
        await asyncio.gather(*tasks)

    async def get_indicies_by_source(self, sources: list[str]) -> dict[str, VectorStoreIndex | None]:
        def _load_index(path: str) -> VectorStoreIndex | None:
            try:
                if not os.path.exists(path):
                    return None
                storage_context = StorageContext.from_defaults(persist_dir=path)
                return cast(VectorStoreIndex, load_index_from_storage(storage_context))
            except Exception as e:
                self.error(f"Error loading index from {path}: {e}")
                return None

        tasks = []
        for source in sources:
            hash_key = Misc.get_hash(source)
            tasks.append(asyncio.to_thread(_load_index, os.path.join(self.indices_cache_path, hash_key)))
        results = await asyncio.gather(*tasks)
        return {source: index for source, index in zip(sources, results, strict=False)}

    def _get_hash_repr_from_sources(self, sources: list[str]) -> str:
        sources = tuple(sorted(sources))
        return Misc.get_hash(str(sources))

    async def set_combined_index(self, sources: list[str], index: VectorStoreIndex):
        hash_key = self._get_hash_repr_from_sources(sources)
        await asyncio.to_thread(index.storage_context.persist, persist_dir=os.path.join(self.combined_index_cache_path, hash_key))

    async def get_combined_index(self, sources: list[str]) -> VectorStoreIndex | None:
        try:
            hash_key = self._get_hash_repr_from_sources(sources)
            abs_path = os.path.join(self.combined_index_cache_path, hash_key)
            if not os.path.exists(abs_path):
                return None
            storage_context = StorageContext.from_defaults(persist_dir=abs_path)
            return cast(VectorStoreIndex, load_index_from_storage(storage_context))
        except Exception as e:
            self.error(f"Error loading combined index from {sources}: {e}")
            return None
