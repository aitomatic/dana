import os
from pathlib import Path
import asyncio

from llama_index.core import Settings
from dana.common.mixins.tool_callable import ToolCallable
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.api.core.schemas import ExtractionResponse
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.common.sys_resource.embedding import get_default_embedding_model
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.duckdb import DuckDBVectorStore
from llama_index.core.schema import Document, NodeWithScore
import duckdb
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterOperator
from dana.common.sys_resource.rag.pipeline.document_loader import DocumentLoader
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
from llama_index.core.schema import MetadataMode
from uuid import uuid4

CACHE_DIR = os.getenv("RAG_CACHE_PATH", os.path.expanduser("~/.dana/.cache/rag"))
PERSIST_DIR = os.path.join(CACHE_DIR, "storage")
Path(PERSIST_DIR).mkdir(parents=True, exist_ok=True)
RAG_NAME = "dana_rag_db"

_conn = {}


def get_duckdb_connection(database_name: str, persist_dir: str, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    full_path = os.path.join(persist_dir, database_name)
    print(f"Getting duckdb connection for {full_path}")
    key = (full_path, read_only)
    if key in _conn:
        return _conn[key]
    conn = duckdb.connect(full_path, read_only=read_only)
    _conn[key] = conn
    return conn


class RAGResourceV2(BaseSysResource):
    """RAG resource for document retrieval."""

    def __init__(
        self,
        sources: list[str],
        name: str = "rag_resource",
        cache_dir: str | None = CACHE_DIR,  # Changed default to None
        force_reload: bool = False,
        description: str | None = None,
        chunk_size: int = 400,
        chunk_overlap: int = 100,
        debug: bool = False,
        reranking: bool = False,
        initial_multiplier: int = 2,
        return_raw: bool = False,
        num_results: int = 15,
        dimensions: int = 1024,
        embed_batch_size: int = 512,
        **kwargs,
    ):
        super().__init__(name, description)
        danapath = self._get_danapath()
        Settings.chunk_size = chunk_size
        Settings.chunk_overlap = chunk_overlap
        self.force_reload = force_reload
        self.debug = debug
        self.reranking = reranking
        self.initial_multiplier = initial_multiplier
        self.sources = self._resolve_sources(sources, danapath)
        self.cache_dir = self._resolve_cache_dir(cache_dir, danapath)
        if self.debug:
            print(f"RAGResource initialized with cache_dir: {self.cache_dir}")
        self.return_raw = return_raw
        self.num_results = num_results
        self.dimension = dimensions
        self.embed_batch_size = embed_batch_size
        self.loader = DocumentLoader()
        self._is_ready = False
        self._filenames = None
        self.vector_index = None
        self.hashes = []

        # Initialize LLM resource for reranking if enabled
        if self.reranking:
            self._llm_reranker = LegacyLLMResource(
                name=f"{name}_reranker",
                temperature=0.0,  # Use deterministic settings for reranking
            )
        else:
            self._llm_reranker = None

    def get_table_name(self) -> str:
        return f"{RAG_NAME.replace('.', '_')}_{self.dimension}"

    def get_existing_hashes(self) -> list[str]:
        try:
            with get_duckdb_connection(self.get_table_name(), PERSIST_DIR) as conn:
                result = conn.execute(f"""
                    SELECT DISTINCT 
                        json_extract_string(metadata_, '$.file_hash')::VARCHAR as file_hash, 
                    FROM {self.get_table_name()}.main.documents;""").fetchall()
            return [row[0] for row in result]
        except Exception as _:
            return []

    def _load_or_create_index(self, document_dict: dict[str, list[Document]]) -> None:
        def get_vector_store():
            return DuckDBVectorStore(database_name=self.get_table_name(), persist_dir=PERSIST_DIR, embed_dim=self.dimension)

        self.embed_model = get_default_embedding_model(dimension_override=self.dimension)
        if hasattr(self.embed_model, "dimensions"):
            # override using dimension from embed_model
            self.dimension = self.embed_model.dimensions
        else:
            self.dimension = len(self.embed_model.get_text_embedding("test"))
        uri = os.path.join(PERSIST_DIR, self.get_table_name())
        if not self.vector_index:
            if Path(uri).exists():
                print(f"Loading index from {uri}")
                vector_store = get_vector_store()
                self.vector_index = VectorStoreIndex.from_vector_store(vector_store, embed_model=self.embed_model)
            else:
                print(f"Creating index from {uri}")
                vector_store = get_vector_store()
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                documents = []
                for docs in document_dict.values():
                    documents.extend(docs)
                self.vector_index = VectorStoreIndex.from_documents(
                    documents=documents, storage_context=storage_context, embed_model=self.embed_model
                )

    def _get_danapath(self) -> str | None:
        # Use DANAPATH if set, otherwise default to .cache/rag
        # if cache_dir is None:
        danapaths = os.environ.get("DANAPATH", "")

        danapaths = danapaths.split(os.pathsep)

        danapath = None

        for _path in danapaths:
            if _path.endswith("stdlib") and "libs" in _path and "dana" in _path:
                continue
            if "agents" in _path:
                danapath = _path
                break

        return danapath

    def _resolve_sources(self, sources: list[str], danapath: str | None) -> list[str]:
        new_sources = []
        for src in sources:
            if src.startswith("http"):
                new_sources.append(src)
                continue
            if not os.path.isabs(src):
                if danapath:
                    new_sources.append(str(Path(danapath) / src))
                else:
                    new_sources.append(os.path.abspath(src))
            else:
                new_sources.append(src)
        return new_sources

    def _resolve_cache_dir(self, cache_dir: str | None, danapath: str | None) -> str:
        # If cache_dir is absolute, use it as is
        if cache_dir and os.path.isabs(cache_dir):
            return cache_dir

        # If cache_dir is relative, try to combine it with DANAPATH
        if danapath:
            if cache_dir:
                return os.path.join(danapath, cache_dir)
            else:
                return os.path.join(danapath, ".cache", "rag")
        else:
            return os.path.abspath(".cache/rag")

    @property
    def filenames(self) -> list[str]:
        if not self._is_ready:
            Misc.safe_asyncio_run(self.initialize)
        return self._filenames or []

    @property
    def is_available(self) -> bool:
        if not self._is_ready:
            Misc.safe_asyncio_run(self.initialize)
        return self._filenames is not None and any([fn != "system" for fn in self.filenames])

    async def initialize(self) -> None:
        """Initialize and preprocess sources."""
        if not self._is_ready:
            document_dict = await self.loader.load_sources(self.sources, group_by_fn=True)
            self.hashes = await self.get_hashes_from_documents(document_dict)
            self._load_or_create_index(document_dict)
            documents = document_dict
            self._filenames = [] if documents is None else list(documents.keys())
            await self._index_documents(documents)
            self._is_ready = True

    async def get_hashes_from_documents(self, documents: dict[str, list[Document]]) -> list[str]:
        mapping = []
        for _, docs in documents.items():
            if len(docs):
                mapping.append(docs[0].metadata.get("file_hash", str(uuid4())))
        return mapping

    async def _index_documents(self, documents: dict[str, list[Document]]) -> None:
        if not self.vector_index:
            raise ValueError("Vector index is not initialized. Please call initialize() first.")

        if not documents:
            return

        existing_hashes = self.get_existing_hashes()

        mapping = {}
        for filename, docs in documents.items():
            if len(docs):
                mapping[(docs[0].metadata.get("file_hash", str(uuid4())))] = filename

        doc_to_add = set(mapping.keys()).difference(set(existing_hashes))

        print(f"Adding {len(doc_to_add)} documents to the index")

        tasks = []
        for data in doc_to_add:
            docs = documents[mapping[data]]
            tasks.extend([self.vector_index.ainsert(doc) for doc in docs])

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                print(f"Error inserting document: {result}")

        self.vector_index.storage_context.persist(persist_dir=PERSIST_DIR)

    async def index_sources(self, sources: list[str]) -> None:
        document_dict = await self.loader.load_sources(sources, group_by_fn=True)
        if not self._is_ready:
            await self.initialize()
        documents = document_dict
        await self._index_documents(documents)

    async def index_extraction_response(self, extraction_response: ExtractionResponse, overwrite: bool = False) -> None:
        """Index an ExtractionResponse by converting it to Document objects and adding to the vector index.

        Args:
            extraction_response: The extraction response containing file data and pages
            overwrite: If True, remove existing documents with the same file_name before indexing
        """
        if not self._is_ready:
            await self.initialize()

        if not self.vector_index:
            raise ValueError("Vector index is not initialized. Please call initialize() first.")

        # Convert ExtractionResponse to Document objects
        documents = self._convert_extraction_response_to_documents(extraction_response)

        if not documents:
            if self.debug:
                print("No documents to index from extraction response")
            return

        file_name = extraction_response.file_object.file_name

        # Remove existing documents if overwrite is True
        if overwrite:
            # Get file hash from the first document's metadata
            file_hash = documents[0].metadata.get("file_hash") if documents else None
            if file_hash:
                await self._remove_documents_by_file_hash(file_hash)
                if self.debug:
                    print(f"Removed existing documents for file: {file_name} (hash: {file_hash})")
            else:
                if self.debug:
                    print(f"Warning: No file_hash found in metadata for file: {file_name}")

        # Create document dict in the format expected by _index_documents
        document_dict = {file_name: documents}

        # Use existing _index_documents method to handle the indexing
        await self._index_documents(document_dict)

        if self.debug:
            print(f"Successfully indexed {len(documents)} documents from extraction response: {file_name}")

    def _convert_extraction_response_to_documents(self, extraction_response: ExtractionResponse) -> list[Document]:
        """Convert an ExtractionResponse to a list of Document objects.

        Args:
            extraction_response: The extraction response to convert

        Returns:
            List of Document objects ready for indexing
        """
        import os
        from datetime import datetime

        documents = []
        file_object = extraction_response.file_object

        # Get file stats for metadata
        file_path = file_object.file_full_path
        try:
            stat = os.stat(file_path)
            file_size = stat.st_size
            creation_date = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d")
            last_modified_date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
        except (OSError, FileNotFoundError):
            # Fallback values if file doesn't exist or can't be accessed
            file_size = getattr(file_object, "total_words", 0)
            creation_date = datetime.now().strftime("%Y-%m-%d")
            last_modified_date = datetime.now().strftime("%Y-%m-%d")

        # Determine file type from extension
        file_extension = os.path.splitext(file_object.file_name)[1].lower()
        file_type_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".ppt": "application/vnd.ms-powerpoint",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".webp": "image/webp",
        }
        file_type = file_type_map.get(file_extension, "application/octet-stream")

        # Generate file hash for unique identification using aicapture
        try:
            from aicapture.cache import HashUtils

            file_hash = HashUtils.calculate_file_hash(file_path)
        except (ImportError, OSError, FileNotFoundError):
            # Fallback to using cache_key as file hash if aicapture is not available or file is not accessible
            raise ValueError("Failed to generate file hash for file: {file_path}")

        # Create a document for each page
        for page in file_object.pages:
            # Create metadata matching the specified format
            metadata = {
                "page_label": str(page.page_number),
                "file_name": file_object.file_name,
                "file_path": file_object.file_full_path,
                "file_type": file_type,
                "file_size": file_size,
                "creation_date": creation_date,
                "last_modified_date": last_modified_date,
                "source": file_object.file_full_path,
                "file_hash": file_hash,  # Add file hash for unique identification
                # Additional metadata for extraction responses
                "page_number": page.page_number,
                "page_hash": page.page_hash,
                "total_pages": file_object.total_pages,
                "cache_key": file_object.cache_key,
                "extraction_type": "extraction_response",
            }

            # Define excluded metadata keys
            excluded_embed_metadata_keys = [
                "file_name",
                "file_type",
                "file_size",
                "creation_date",
                "last_modified_date",
                "last_accessed_date",
            ]
            excluded_llm_metadata_keys = [
                "file_name",
                "file_type",
                "file_size",
                "creation_date",
                "last_modified_date",
                "last_accessed_date",
            ]

            # Create Document object
            doc = Document(text=page.page_content, metadata=metadata, id_=f"{file_object.cache_key}_page_{page.page_number}")

            # Set excluded metadata keys
            doc.excluded_embed_metadata_keys = excluded_embed_metadata_keys
            doc.excluded_llm_metadata_keys = excluded_llm_metadata_keys

            documents.append(doc)

        return documents

    async def _remove_documents_by_file_hash(self, file_hash: str) -> None:
        """Remove documents from the vector index by file hash.

        Args:
            file_hash: The file hash to match for removal
        """
        if not self.vector_index:
            raise ValueError("Vector index is not initialized.")

        try:
            # Connect to the DuckDB database
            with get_duckdb_connection(self.get_table_name(), PERSIST_DIR) as conn:
                # Remove documents with matching file hash
                query = f"""
                    DELETE FROM {self.get_table_name()}.main.documents 
                    WHERE json_extract_string(metadata_, '$.file_hash') = ?
                """
                result = conn.execute(query, [file_hash])
                removed_count = result.rowcount

            if self.debug:
                print(f"Removed {removed_count} documents with file_hash: {file_hash}")

        except Exception as e:
            if self.debug:
                print(f"Error removing documents by file_hash {file_hash}: {e}")
            # Don't raise the exception to allow the indexing to continue
            # This ensures that even if removal fails, new documents can still be added

    async def retrieve(self, query: str, num_results: int = 10) -> list[NodeWithScore]:
        if not self._is_ready:
            await self.initialize()
        if not self.vector_index:
            raise ValueError("Vector index is not initialized. Please call initialize() first.")
        return await self.vector_index.as_retriever(
            similarity_top_k=num_results,
            embed_model=self.embed_model,
            filters=MetadataFilters(filters=[MetadataFilter(key="file_hash", operator=FilterOperator.IN, value=self.hashes)]),
        ).aretrieve(query)

    @ToolCallable.tool
    async def query(self, query: str, num_results: int = 10) -> str | list:
        """Retrieve relevant documents. Minimum number of results is 5"""
        if not self._is_ready:
            await self.initialize()

        if not self.is_available:
            return "No relevant documents found"

        num_results = max(num_results, self.num_results)

        if self.debug:
            print(f"Querying {num_results} results from {self.name} RAG with query: {query}")

        # Get initial results (more than needed for reranking)
        initial_num_results = num_results
        if self.reranking:
            # Retrieve more results for better reranking selection
            initial_num_results = num_results * self.initial_multiplier

        results = await self.retrieve(query, initial_num_results)

        # Apply LLM reranking if enabled
        if self.reranking and self._llm_reranker and len(results) > 1:
            results = await self._rerank_with_llm(query, results, num_results)
        elif len(results) > num_results:
            # Truncate to requested number if no reranking
            results = results[:num_results]
        if not self.return_raw:
            return "\n\n".join([result.node.get_content(MetadataMode.LLM) for result in results])
        else:
            return results

    async def _rerank_with_llm(self, query: str, results: list, target_count: int) -> list:
        """Rerank and filter results using LLM to improve relevance and discard irrelevant content.

        The LLM will:
        1. Analyze each document for relevance to the query
        2. Discard completely unrelated documents
        3. Rank remaining documents by relevance
        4. Return at most target_count documents (may return fewer)
        """
        if not results:
            return results

        if self.debug:
            print(f"LLM reranking: analyzing {len(results)} results (target {target_count} will be selected)")

        # Prepare documents for reranking
        documents = []
        for i, result in enumerate(results):
            content = result.node.get_content()
            # Truncate very long documents to avoid token limits
            if len(content) > 2000:
                content = content[:2000] + "..."
            documents.append(
                {
                    "id": i,
                    "content": content,
                    "score": result.score if hasattr(result, "score") else 0.0,
                }
            )

        # Create reranking prompt
        prompt = self._create_reranking_prompt(query, documents, target_count)

        try:
            # Query LLM for reranking
            request = BaseRequest(
                arguments={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 1000,
                }
            )

            response = await self._llm_reranker.query(request)

            if response.success:
                content = Misc.get_response_content(response)
                # Parse the response to get ranked document IDs
                ranked_ids = self._parse_reranking_response(content)

                # Reorder results based on LLM ranking (only include LLM-selected documents)
                reranked_results = []
                for doc_id in ranked_ids:
                    if 0 <= doc_id < len(results):
                        reranked_results.append(results[doc_id])

                if self.debug:
                    original_count = len(results)
                    filtered_count = len(reranked_results)
                    print(f"LLM reranking successful: filtered {original_count} -> {filtered_count} results")

                # Return only LLM-selected results (may be fewer than target_count)
                return reranked_results[:target_count] if len(reranked_results) > target_count else reranked_results
            else:
                if self.debug:
                    print(f"LLM reranking failed: {response.error}")
                return results[:target_count]

        except Exception as e:
            if self.debug:
                print(f"Error during LLM reranking: {e}")
            return results[:target_count]

    def _create_reranking_prompt(self, query: str, documents: list[dict], target_count: int) -> str:
        """Create a prompt for LLM-based reranking and filtering."""
        docs_text = ""
        for doc in documents:
            docs_text += f"Document {doc['id']}:\n{doc['content']}\n\n"

        prompt = f"""You are an expert document relevance analyzer. Given a query and a list of documents, your task is to:

1. IDENTIFY documents that are actually relevant to answering the query
2. DISCARD documents that are unrelated or contain irrelevant information
3. RANK the relevant documents by their usefulness in answering the query
4. Return AT MOST {target_count} document IDs (you may return fewer if many documents are irrelevant)

Query: {query}

Documents:
{docs_text}

Instructions:
- Only include documents that contain information directly relevant to the query
- If a document is completely unrelated to the query, DO NOT include it in your response
- If multiple documents are relevant, rank them from most useful to least useful
- Return a JSON array of document IDs in order of relevance: [most_relevant_id, second_most_relevant_id, ...]
- If NO documents are relevant to the query, return an empty array: []
- Maximum {target_count} document IDs in your response

Response (JSON array only):"""

        return prompt

    def _parse_reranking_response(self, response_content: str | dict) -> list[int]:
        """Parse LLM response to extract ranked document IDs."""
        try:
            # Handle both string and dict responses
            if isinstance(response_content, dict):
                response_text = response_content.get("content", "")
            else:
                response_text = response_content

            # Use Misc.text_to_dict to parse the response
            parsed = Misc.text_to_dict(response_text)

            # The response should be a JSON array of integers
            if isinstance(parsed, list):
                return [int(x) for x in parsed if isinstance(x, int | str) and str(x).isdigit()]
            elif isinstance(parsed, dict) and "ranking" in parsed:
                ranking = parsed["ranking"]
                if isinstance(ranking, list):
                    return [int(x) for x in ranking if isinstance(x, int | str) and str(x).isdigit()]

            # Fallback: try to extract numbers from the text
            import re

            numbers = re.findall(r"\b\d+\b", response_text)
            return [int(x) for x in numbers]

        except Exception as e:
            if self.debug:
                print(f"Failed to parse reranking response: {e}")
            return []


if __name__ == "__main__":
    rag = RAGResourceV2(
        sources=[
            "/Users/lam/Downloads/STD-ENG-015.pdf",
            "/Users/lam/Downloads/Fans Best practice work pack rev 4.pdf",
            "/Users/lam/Desktop/repos/opendxa/docs/reference",
            "docs/releases",
        ],
        reranking=False,
        debug=True,
    )
    import asyncio

    print(rag.is_available)
    print(rag.filenames)

    print(len(asyncio.run(rag.query("Procedure for monitoring sugar manufacturing process"), debug=True)))
