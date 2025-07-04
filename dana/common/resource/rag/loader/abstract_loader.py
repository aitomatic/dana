from abc import ABC, abstractmethod

from llama_index.core import Document


class AbstractLoader(ABC):
    @abstractmethod
    async def load(self, source: str) -> list[Document]:
        pass
