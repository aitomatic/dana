from llama_index.core import Document

from dana.common.sys_resource.rag.utility.web_fetch import fetch_web_content

from .abstract_loader import AbstractLoader


class WebLoader(AbstractLoader):
    async def load(self, source: str) -> list[Document]:
        return [Document(text=await fetch_web_content(source), metadata={"source": source}, id_=source)]
