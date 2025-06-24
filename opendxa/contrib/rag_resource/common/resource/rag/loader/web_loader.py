from .abstract_loader import AbstractLoader
from llama_index.core import Document
from typing import List
from opendxa.contrib.rag_resource.common.utility.web_fetch import fetch_web_content

class WebLoader(AbstractLoader):
    async def load(self, source: str) -> List[Document]:
        return [Document(text=await fetch_web_content(source), metadata={"source": source}, id_=source)]