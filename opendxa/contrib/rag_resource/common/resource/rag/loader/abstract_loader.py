from abc import ABC, abstractmethod
from llama_index.core import Document
from typing import List


class AbstractLoader(ABC):
    @abstractmethod
    async def load(self, source: str) -> List[Document]:
        pass