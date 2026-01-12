from llama_index.core import Document

from dana.common.sys_resource.rag.utility.web_fetch import fetch_web_content
from aicapture.cache import HashUtils
from .abstract_loader import AbstractLoader
from uuid import uuid4
import tempfile


class WebLoader(AbstractLoader):
    async def load(self, source: str) -> list[Document]:
        text = await fetch_web_content(source)
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=True) as temp_file:
                temp_file.write(text)
                temp_file.flush()
                file_hash = HashUtils.calculate_file_hash(temp_file.name)
        except Exception as _:
            # Fall back to a random hash
            file_hash = str(uuid4())

        return [Document(text=text, metadata={"source": source, "file_hash": file_hash}, id_=source)]
