import os
from multiprocessing import cpu_count

from llama_index.core import Document
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.readers.file.base import _DefaultFileMetadataFunc

from .abstract_loader import AbstractLoader


class LocalFileMetadataFunc(_DefaultFileMetadataFunc):
    def __call__(self, file_path: str) -> dict:
        metadata = super().__call__(file_path)
        metadata['source'] = file_path
        return metadata

class LocalLoader(AbstractLoader):
    def __init__(self, supported_types: list[str]):
        self.supported_types = supported_types
        self._encoding = 'utf-8'
        self.filename_as_id = True
        self.metadata_func = LocalFileMetadataFunc()


    async def load(self, source: str) -> list[Document]:
        if os.path.isdir(source):
            return await SimpleDirectoryReader(source, recursive=True, required_exts=self.supported_types, 
                                               encoding=self._encoding, filename_as_id=self.filename_as_id, 
                                               file_metadata=self.metadata_func
                                               ).aload_data(num_workers=max(1, cpu_count() // 4))
        else:
            return await SimpleDirectoryReader(
                input_files=[source],
                encoding=self._encoding,
                filename_as_id=self.filename_as_id,
                file_metadata=self.metadata_func
            ).aload_data(num_workers=1)