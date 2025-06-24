from llama_index.core import VectorStoreIndex

from llama_index.core.schema import NodeWithScore
from typing import List

class Retriever:
    def __init__(self, index: VectorStoreIndex, **kwargs) -> None:
        self._index = index

    @classmethod
    def from_index(cls, index: VectorStoreIndex, **kwargs) -> "Retriever":
        return cls(index, **kwargs)

    def retrieve(self, query: str, num_results: int = 10) -> List[NodeWithScore]:
        return self._index.as_retriever(similarity_top_k=num_results).retrieve(query)
    
    async def aretrieve(self, query: str, num_results: int = 10) -> List[NodeWithScore]:
        return await self._index.as_retriever(similarity_top_k=num_results).aretrieve(query)