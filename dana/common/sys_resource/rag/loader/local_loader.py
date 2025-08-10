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
        # Check if source exists before attempting to load
        if not os.path.exists(source):
            # Log warning but return empty list instead of failing
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"RAG source does not exist: {source}")
            return []

        try:
            if os.path.isdir(source):
                # Check if directory has any files with supported extensions
                has_supported_files = False
                for _, _, files in os.walk(source):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in self.supported_types):
                            has_supported_files = True
                            break
                    if has_supported_files:
                        break

                if not has_supported_files:
                    # Log info but return empty list instead of failing
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(f"RAG source directory contains no supported files: {source}")
                    return []

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
                    raise_on_error=False,  # Changed to False to handle errors gracefully
                    fs=None,
                ).aload_data(num_workers=max(1, cpu_count() // 4))

            else:
                # Single file
                if not any(source.lower().endswith(ext) for ext in self.supported_types):
                    # Log info but return empty list for unsupported file types
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(f"RAG source file has unsupported extension: {source}")
                    return []

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
                    raise_on_error=False,  # Changed to False to handle errors gracefully
                    fs=None,
                ).aload_data(num_workers=1)

        except Exception as e:
            # Log the error but return empty list instead of propagating the exception
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error loading RAG source {source}: {e}")
            return []
