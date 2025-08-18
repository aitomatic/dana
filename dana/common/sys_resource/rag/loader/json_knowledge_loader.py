from dana.common.sys_resource.rag.loader.local_loader import LocalLoader, LocalFileMetadataFunc
from llama_index.core import Document
from llama_index.core.readers import SimpleDirectoryReader
import os
from multiprocessing import cpu_count
import json


class JsonKnowledgeLoader(LocalLoader):
    def __init__(self, supported_types: list[str]):
        self.supported_types = supported_types
        self._encoding = "utf-8"
        self.filename_as_id = True
        self.metadata_func = LocalFileMetadataFunc()

    def post_process(self, doc: Document) -> Document:
        if doc.metadata["file_path"].endswith(".json"):
            json_dict = json.loads(doc.text)
            question = json_dict.get("question", "")
            plan = json_dict.get("plan", "")
            facts = json_dict.get("facts", "")
            heuristics = json_dict.get("heuristics", "")
            if question:
                doc.text_resource.text = question
                doc.metadata["plan"] = plan
                doc.metadata["facts"] = facts
                doc.metadata["heuristics"] = heuristics
                doc.excluded_embed_metadata_keys.extend(["plan", "facts", "heuristics"])
                doc.excluded_llm_metadata_keys.extend(["plan", "facts", "heuristics"])
        return doc

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

                results = await SimpleDirectoryReader(
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

                results = await SimpleDirectoryReader(
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
            return [self.post_process(doc) for doc in results]

        except Exception as e:
            # Log the error but return empty list instead of propagating the exception
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error loading RAG source {source}: {e}")
            return []


if __name__ == "__main__":
    import asyncio

    loader = JsonKnowledgeLoader(supported_types=[".json"])
    results = asyncio.run(loader.load("agents/financial_stmt_analysis/knows/processed_knowledge"))
    print(len(results))
