import os
from multiprocessing import cpu_count

from llama_index.core import Document
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.readers.file.base import _DefaultFileMetadataFunc

from .abstract_loader import AbstractLoader


class LocalFileMetadataFunc(_DefaultFileMetadataFunc):
    def __call__(self, file_path: str) -> dict:
        metadata = super().__call__(file_path)
        metadata["source"] = file_path
        return metadata


class LocalLoader(AbstractLoader):
    def __init__(self, supported_types: list[str]):
        self.supported_types = supported_types
        self._encoding = "utf-8"
        self.filename_as_id = True
        self.metadata_func = LocalFileMetadataFunc()

    async def load(self, source: str) -> list[Document]:
        if os.path.isdir(source):
            return await SimpleDirectoryReader(
                input_dir=source,
                input_files=None,
                exclude=[
                    ".DS_Store",  # MacOS
                    # "*.json",  # TODO: JSON files should be indexed differently
                ],
                exclude_hidden=False,
                errors="strict",
                recursive=True,
                encoding=self._encoding,
                filename_as_id=self.filename_as_id,
                required_exts=self.supported_types,
                file_extractor=None,
                num_files_limit=None,
                file_metadata=self.metadata_func,
                raise_on_error=True,
                fs=None,
            ).aload_data(num_workers=max(1, cpu_count() // 4))

        else:
            return await SimpleDirectoryReader(
                input_dir=None,
                input_files=[source],
                exclude=[
                    ".DS_Store",  # MacOS
                    # "*.json",  # TODO: JSON files should be indexed differently
                ],
                exclude_hidden=False,
                errors="strict",
                recursive=False,
                encoding=self._encoding,
                filename_as_id=self.filename_as_id,
                required_exts=None,
                file_extractor=None,
                num_files_limit=None,
                file_metadata=self.metadata_func,
                raise_on_error=True,
                fs=None,
            ).aload_data(num_workers=1)
