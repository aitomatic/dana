import asyncio
import hashlib
import json
import os
import re
from multiprocessing import cpu_count
from pathlib import Path

from llama_index.core import (
    Document,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata

from opendxa.common.utils.misc import Misc
from opendxa.contrib.dana_rag.common.utility.web_fetch import fetch_web_content

"""
Document Store Module

This module provides a comprehensive document processing and retrieval system that supports
both local files and web content. It implements a vector-based search system using LlamaIndex
for efficient document retrieval and semantic search capabilities.

Key Features:
    - Multi-format Support: Handles various document types including PDF, TXT, DOCX, MD, CSV, JSON, HTML, XML, PPTX, XLSX, XLS, and DOC
    - Web Content Processing: Fetches and processes web content using Playwright with anti-bot detection measures
    - Document Chunking: Splits documents into manageable chunks for better processing and retrieval
    - Vector Store Indexing: Creates and maintains vector indices for efficient semantic search
    - Caching System: Implements document caching to improve performance and reduce processing time
    - Result Reranking: Uses LLM-based reranking to improve search result relevance

Main Components:
    - RAGStore: Core class that handles document processing, indexing, and retrieval
    - fetch_web_content: Utility function for fetching web content with browser automation
    - _ensure_playwright_installed: Helper function to ensure Playwright dependencies are installed

Usage:
    ```python
    # Initialize document store with multiple local files/folders
    doc_store = RAGStore(
        document_paths=["path/to/document.pdf", "path/to/folder", "path/to/doc2.txt"],
        output_folder="path/to/output",
        chunk_size=512,
        chunk_overlap=128
    )

    # Initialize with multiple web URLs
    doc_store = RAGStore(
        document_paths=["https://example1.com", "https://example2.com"],
        output_folder="path/to/output"
    )

    # Initialize with mixed URLs and local paths
    doc_store = RAGStore(
        document_paths=["https://example.com", "local/folder", "local/file.pdf"],
        output_folder="path/to/output"
    )

    # Retrieve documents
    results = await doc_store.retrieve("your query here", num_results=10)
    ```

Note:
    - The module requires OpenAI API access for reranking functionality
    - Playwright is used for web content fetching and is automatically installed if not present
    - Document processing can be resource-intensive for large files or directories
"""


class RAGStore:
    DOUBLE_NEWLINE = "\n\n"
    NEWLINE = "\n"
    SUPPORTED_TYPES = [".pdf", ".txt", ".docx", ".md", ".csv", ".json", ".html", ".xml", ".pptx", ".xlsx", ".xls", ".doc"]
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 128

    def __init__(
        self,
        doc_paths: list[str],
        output_folder: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        use_chunking: bool = True,
        enable_print: bool = False,
        force_reload: bool = False,
    ):
        if not doc_paths:
            raise ValueError("document_paths cannot be empty")
        self.force_reload = force_reload
        self.chunk_size = chunk_size if chunk_size is not None else self.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else self.CHUNK_OVERLAP
        self.use_chunking = use_chunking
        self.enable_print = enable_print
        self.output_folder = output_folder
        self.document_paths_info = self._verify_and_preprocess_documents(doc_paths, output_folder)
        self.storage_path, self.cache_file = self._initialize_paths(output_folder)
        self.source_documents = self.load_documents_by_source()
        self.indices = self.create_indices()
        self.combined_query_engine = self.create_combined_query_engine()

    @classmethod
    def from_single_path(cls, document_path: str, **kwargs):
        """Create RAGStore from single document path for backward compatibility."""
        return cls(doc_paths=[document_path], **kwargs)

    async def _fetch_web_content_parallel(self, web_urls: list[str], output_folder: str) -> dict[str, str]:
        """Fetch multiple web URLs in parallel."""
        temp_output = Path(output_folder) / "temp"
        temp_output.mkdir(parents=True, exist_ok=True)

        async def fetch_single_url(url: str) -> tuple[str, str]:
            """Fetch a single URL and return (url, local_file_path)."""
            try:
                # Create file name from url, preserving extension
                document_path = url
                # Clean up url to be a valid file name using regex
                document_path = re.sub(r"^https?://", "", document_path)  # Remove http:// or https://
                document_path = re.sub(r"[^\w\-\.]", "_", document_path)  # Replace any non-word chars with underscore
                # Always ensure .html extension for web content
                if not document_path.endswith(".html"):
                    document_path = document_path + ".html"
                document_full_path = temp_output / document_path

                # Only use cached file if force_reload is False
                if document_full_path.exists() and not self.force_reload:
                    return url, str(document_full_path)

                if self.enable_print:
                    print(f"Fetching: {url}")

                content = await fetch_web_content(url, enable_print=self.enable_print)
                with open(str(document_full_path), "w") as file:
                    file.write(content)

                if self.enable_print:
                    print(f"Completed: {url}")

                return url, str(document_full_path)
            except Exception as e:
                if self.enable_print:
                    print(f"Error fetching {url}: {str(e)}")
                raise

        if self.enable_print:
            print(f"Starting parallel fetch of {len(web_urls)} URLs...")

        # Fetch all URLs in parallel
        tasks = [fetch_single_url(url) for url in web_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        url_to_path = {}
        for result in results:
            if isinstance(result, Exception):
                continue  # Skip failed URLs
            url, local_path = result
            url_to_path[url] = local_path

        if self.enable_print:
            print(f"Successfully fetched {len(url_to_path)} out of {len(web_urls)} URLs")

        return url_to_path

    def _verify_and_preprocess_documents(self, raw_document_paths: list[str], output_folder: str) -> list[tuple[str, bool]]:
        """
        Verify if each document_path is web url or local path.
        If local path, verify if it exists.
        If web url, download and save to local path.

        Returns:
            List[Tuple[str, bool]]: List of (document_path, is_dir) tuples where is_dir is True if path is a directory, False if it's a file
        """
        processed_paths = []
        errors = []

        # Separate web URLs from local paths
        web_urls = []
        local_paths = []

        for raw_document_path in raw_document_paths:
            if raw_document_path.startswith("http"):
                web_urls.append(raw_document_path)
            else:
                local_paths.append(raw_document_path)

        # Process web URLs in parallel if any exist
        url_to_path = {}
        if web_urls:
            if self.enable_print:
                print(f"Processing {len(web_urls)} web URLs in parallel...")
            try:
                url_to_path = Misc.safe_asyncio_run(self._fetch_web_content_parallel, web_urls, output_folder)
            except Exception as e:
                if self.enable_print:
                    print(f"Error in parallel web fetching: {str(e)}")

        # Process all paths in original order
        for i, raw_document_path in enumerate(raw_document_paths):
            try:
                if self.enable_print:
                    print(f"Processing document source {i+1}/{len(raw_document_paths)}: {raw_document_path}")

                if raw_document_path.startswith("http"):
                    if raw_document_path in url_to_path:
                        processed_paths.append((url_to_path[raw_document_path], False))
                    else:
                        raise RuntimeError(f"Failed to fetch web content for: {raw_document_path}")
                else:
                    if not os.path.exists(raw_document_path):
                        raise FileNotFoundError(f"File not found: {raw_document_path}")
                    processed_paths.append((raw_document_path, os.path.isdir(raw_document_path)))
            except Exception as e:
                error_msg = f"Error processing {raw_document_path}: {str(e)}"
                errors.append(error_msg)
                if self.enable_print:
                    print(f"Warning: {error_msg}")

        if not processed_paths:
            if errors:
                raise RuntimeError(f"Failed to process all document paths. Errors: {'; '.join(errors)}")
            else:
                raise RuntimeError("No valid document paths found")

        if errors and self.enable_print:
            print(f"Warning: {len(errors)} out of {len(raw_document_paths)} document sources failed to process")

        return processed_paths

    def _get_combined_index_hash(self) -> str:
        """Generate a hash from all document paths for combined index storage."""
        # Sort paths to ensure deterministic hash regardless of order
        sorted_paths = sorted([path_info[0] for path_info in self.document_paths_info])
        combined_string = "|".join(sorted_paths)

        # Create hash and limit to reasonable length for filesystem
        hash_obj = hashlib.md5(combined_string.encode("utf-8"))
        return hash_obj.hexdigest()[:16]  # Use first 16 chars of MD5 hash

    def _create_combined_index_from_existing(self, individual_indices: dict) -> VectorStoreIndex:
        """Create combined index by merging existing indices without recomputing embeddings."""
        # Collect all nodes from individual indices
        all_nodes = []
        total_nodes = 0

        for source_idx, index in individual_indices.items():
            if self.enable_print:
                print(f"  Extracting nodes from source {source_idx+1}")

            # Get all nodes from the docstore
            # Use the correct method to get all nodes
            try:
                # Method 1: Try to get all nodes directly
                node_dict = index.docstore.docs
                source_nodes = list(node_dict.values())
                all_nodes.extend(source_nodes)
                total_nodes += len(source_nodes)

                if self.enable_print:
                    print(f"    Retrieved {len(source_nodes)} nodes from source {source_idx+1}")

            except Exception as e:
                if self.enable_print:
                    print(f"    Error extracting nodes from source {source_idx+1}: {str(e)}")
                continue

        if self.enable_print:
            print(f"  Collected {total_nodes} nodes across {len(individual_indices)} sources")

        if not all_nodes:
            if self.enable_print:
                print("  Warning: No nodes collected, falling back to document-based approach")
            # Fallback: create from documents if node extraction fails
            all_documents = []
            for _source_idx, documents in self.source_documents.items():
                all_documents.extend(documents)
            return VectorStoreIndex.from_documents(all_documents)

        # Create new index from collected nodes (this reuses existing embeddings)
        combined_index = VectorStoreIndex(nodes=all_nodes)

        return combined_index

    def _initialize_paths(self, output_folder: str):
        # Create combined identifier from all paths for cache file only
        path_names = []
        for path_info in self.document_paths_info:
            path_names.append(Path(path_info[0]).stem)

        # Sort path names to ensure consistent cache file naming regardless of order
        path_names.sort()

        # Create combined name (with fallback for very long names)
        combined_name = "_".join(path_names)
        if len(combined_name) > 100:  # Filesystem limit consideration
            # Use sorted path names for hash too to maintain consistency
            sorted_paths = sorted([path_info[0] for path_info in self.document_paths_info])
            combined_name = f"multi_docs_{hash(str(sorted_paths)) % 10000}"

        _output_folder = Path(output_folder)
        # No longer create a combined storage path since each source gets its own
        cache_file = _output_folder / f"{combined_name}_processed_documents.json"
        return None, str(cache_file)  # Return None for storage_path since it's not used

    def chunk_document(self, doc: Document, chunk_size: int = 512, overlap: int = 128) -> list:
        words = doc.text.split()
        chunks = []
        for start in range(0, len(words), chunk_size - overlap):
            end = start + chunk_size
            chunk_text = " ".join(words[start:end])
            chunk_metadata = dict(doc.metadata) if doc.metadata else {}
            chunk_metadata["chunk_index"] = start // (chunk_size - overlap)
            chunk_metadata["chunk_start_word"] = start
            chunk_metadata["chunk_end_word"] = min(end, len(words))
            chunks.append(Document(text=chunk_text, metadata=chunk_metadata))
            if end >= len(words):
                break
        return chunks

    def load_documents_by_source(self):
        """Load documents separately for each source, maintaining source separation."""

        if os.path.exists(self.cache_file) and not self.force_reload:
            if self.enable_print:
                print(f"Loading documents from cache: {self.cache_file}")
            with open(self.cache_file) as file:
                cached_data = json.load(file)

                # Check if cache is in old format (list) or new format (dict with source indices)
                if isinstance(cached_data, list):
                    if self.enable_print:
                        print("Warning: Cache file is in old format, ignoring cache and reprocessing")
                    # Old format detected, ignore cache and reprocess
                    pass
                elif isinstance(cached_data, dict):
                    # Check if it's the new source-separated format
                    if all(key.isdigit() for key in cached_data.keys()):
                        # New source-separated format
                        source_documents = {}
                        for source_idx, docs_data in cached_data.items():
                            source_documents[int(source_idx)] = [Document(text=doc["text"], metadata=doc["metadata"]) for doc in docs_data]
                        return source_documents
                    else:
                        if self.enable_print:
                            print("Warning: Unrecognized cache format, ignoring cache and reprocessing")
                else:
                    if self.enable_print:
                        print("Warning: Invalid cache format, ignoring cache and reprocessing")

        if self.enable_print:
            print(f"Processing documents from {len(self.document_paths_info)} sources separately")

        # Process each document source separately
        source_documents = {}
        cache_data = {}

        for i, (document_path, is_dir) in enumerate(self.document_paths_info):
            if self.enable_print:
                print(f"Processing source {i+1}/{len(self.document_paths_info)}: {document_path}")

            try:
                if self.enable_print:
                    print(f"  Attempting to load documents from: {document_path}")
                    print(f"  File exists: {os.path.exists(document_path)}")
                    if os.path.exists(document_path):
                        print(f"  File size: {os.path.getsize(document_path)} bytes")

                if not is_dir:
                    # Handle single file
                    file_extension = os.path.splitext(document_path)[1].lower()
                    if self.enable_print:
                        print(f"  File extension: {file_extension}")

                    if file_extension not in self.SUPPORTED_TYPES:
                        if self.enable_print:
                            print(f"Warning: Skipping unsupported file type: {file_extension} for {document_path}")
                        continue

                    if self.enable_print:
                        print(f"  Using SimpleDirectoryReader for file: {document_path}")

                    documents = SimpleDirectoryReader(input_files=[document_path], encoding="utf-8").load_data(
                        show_progress=self.enable_print, num_workers=1
                    )
                else:
                    # Handle directory
                    if self.enable_print:
                        print(f"  Using SimpleDirectoryReader for directory: {document_path}")

                    documents = SimpleDirectoryReader(
                        document_path, recursive=True, required_exts=self.SUPPORTED_TYPES, encoding="utf-8"
                    ).load_data(show_progress=self.enable_print, num_workers=max(1, cpu_count() // 4))

                if self.enable_print:
                    print(f"  SimpleDirectoryReader returned {len(documents)} documents")

                if not documents:
                    if self.enable_print:
                        print(f"Warning: No documents loaded from {document_path}")
                    continue

                # Add source information to metadata
                for doc in documents:
                    if doc.metadata is None:
                        doc.metadata = {}
                    doc.metadata["source_index"] = i
                    doc.metadata["source_path"] = document_path
                    doc.metadata["source_type"] = "directory" if is_dir else "file"

                # Apply chunking if enabled
                if self.use_chunking:
                    chunked_docs = []
                    for doc in documents:
                        chunked_docs.extend(self.chunk_document(doc, chunk_size=self.chunk_size, overlap=self.chunk_overlap))
                    source_documents[i] = chunked_docs
                    cache_data[str(i)] = [{"text": doc.text, "metadata": doc.metadata} for doc in chunked_docs]
                else:
                    source_documents[i] = documents
                    cache_data[str(i)] = [{"text": doc.text, "metadata": doc.metadata} for doc in documents]

                if self.enable_print:
                    print(f"  Successfully loaded {len(source_documents[i])} documents from source {i+1}")

            except Exception as e:
                if self.enable_print:
                    print(f"Warning: Error processing source {document_path}: {str(e)}")
                    import traceback

                    traceback.print_exc()
                continue

        if not source_documents:
            raise RuntimeError("No documents were successfully loaded from any source")

        if self.enable_print:
            print(f"Saving processed documents to cache: {self.cache_file}")
        with open(self.cache_file, "w") as file:
            json.dump(cache_data, file, indent=4)

        return source_documents

    def create_indices(self):
        """Create separate indices for each source AND a combined persisted index."""
        indices = {}

        # First, create/load individual source indices (for individual caching)
        for source_idx, documents in self.source_documents.items():
            source_path = self.document_paths_info[source_idx][0]
            path_stem = Path(source_path).stem

            # Create storage path: output_folder/{path.stem}/rag_store
            source_storage_path = Path(self.output_folder) / path_stem / "rag_store"
            source_storage_path.mkdir(parents=True, exist_ok=True)
            source_storage_path_str = str(source_storage_path)

            if self.force_reload:
                if self.enable_print:
                    print(f"Force reload enabled. Creating new index for source {source_idx+1}: {source_path}")
                    print(f"  Storage path: {source_storage_path_str}")
                index = VectorStoreIndex.from_documents(documents)
                if self.enable_print:
                    print(f"Persisting index for source {source_idx+1} to: {source_storage_path_str}")
                index.storage_context.persist(persist_dir=source_storage_path_str)
                indices[source_idx] = index
            else:
                try:
                    if self.enable_print:
                        print(f"Loading index for source {source_idx+1} from storage: {source_storage_path_str}")
                    storage_context = StorageContext.from_defaults(persist_dir=source_storage_path_str)
                    index = load_index_from_storage(storage_context)
                    indices[source_idx] = index
                except Exception:
                    if self.enable_print:
                        print(f"Index not found for source {source_idx+1}. Creating new index: {source_path}")
                        print(f"  Storage path: {source_storage_path_str}")
                    index = VectorStoreIndex.from_documents(documents)
                    if self.enable_print:
                        print(f"Persisting index for source {source_idx+1} to: {source_storage_path_str}")
                    index.storage_context.persist(persist_dir=source_storage_path_str)
                    indices[source_idx] = index

        # Now create combined index with hash-based storage
        combined_hash = self._get_combined_index_hash()
        combined_storage_path = Path(self.output_folder) / f"combined_rag_store_{combined_hash}"
        combined_storage_path.mkdir(parents=True, exist_ok=True)
        combined_storage_path_str = str(combined_storage_path)

        if self.enable_print:
            print(f"Combined index storage path: {combined_storage_path_str}")

        if self.force_reload:
            if self.enable_print:
                print("Creating new combined index by merging individual indices (reusing embeddings)")
            combined_index = self._create_combined_index_from_existing(indices)
            if self.enable_print:
                print(f"Persisting combined index to: {combined_storage_path_str}")
            combined_index.storage_context.persist(persist_dir=combined_storage_path_str)
        else:
            try:
                if self.enable_print:
                    print(f"Loading combined index from {combined_storage_path_str}")
                storage_context = StorageContext.from_defaults(persist_dir=combined_storage_path_str)
                combined_index = load_index_from_storage(storage_context)
            except Exception:
                if self.enable_print:
                    print("Combined index not found. Creating new one by merging individual indices (reusing embeddings)")
                combined_index = self._create_combined_index_from_existing(indices)
                if self.enable_print:
                    print(f"Persisting combined index to: {combined_storage_path_str}")
                combined_index.storage_context.persist(persist_dir=combined_storage_path_str)

        indices["combined"] = combined_index

        if self.enable_print:
            print(f"Created indices: {len(indices)-1} individual + 1 combined")

        return indices

    def create_combined_query_engine(self):
        """Create a SubQuestionQueryEngine with individual sources AND combined index."""
        if not self.indices:
            if self.enable_print:
                print("Warning: No indices available for creating combined query engine")
            return None

        # Create QueryEngineTool for each individual source index
        query_engine_tools = []

        for source_idx, index in self.indices.items():
            if source_idx == "combined":
                continue  # Skip combined index, we'll add it separately

            source_path = self.document_paths_info[source_idx][0]
            # Create a more descriptive name for the tool
            tool_name = f"source_{source_idx+1}"
            tool_description = f"Useful for queries about content from {source_path}"

            # Create query engine for this index
            query_engine = index.as_query_engine()

            # Create tool wrapper
            query_engine_tool = QueryEngineTool(
                query_engine=query_engine, metadata=ToolMetadata(name=tool_name, description=tool_description)
            )
            query_engine_tools.append(query_engine_tool)

        # Add combined index as a tool
        if "combined" in self.indices:
            combined_query_engine = self.indices["combined"].as_query_engine()
            combined_tool = QueryEngineTool(
                query_engine=combined_query_engine,
                metadata=ToolMetadata(
                    name="combined_all_sources",
                    description="Useful for queries that might span multiple sources or when unsure which specific source to use",
                ),
            )
            query_engine_tools.append(combined_tool)

        if self.enable_print:
            print(f"Created {len(query_engine_tools)} query engine tools")
            for tool in query_engine_tools:
                print(f"  - {tool.metadata.name}: {tool.metadata.description}")

        # Create SubQuestionQueryEngine that can route queries to appropriate sources
        combined_query_engine = SubQuestionQueryEngine.from_defaults(query_engine_tools=query_engine_tools, verbose=self.enable_print)

        return combined_query_engine

    async def rerank_results(self, query: str, results: list[str]) -> list[str]:
        # NOTE : IMPLEMENT RERANKING HERE
        return results

    async def retrieve(self, query: str, num_results: int | None = 10) -> list[str]:
        """Retrieve the most relevant results for a query using the combined query engine."""
        if num_results is None:
            num_results = 10

        if self.enable_print:
            print(f"Retrieving results for query: {query}")

        if self.combined_query_engine is None:
            if self.enable_print:
                print("Warning: No combined query engine available, falling back to manual retrieval")
            return await self._manual_retrieve(query, num_results)

        try:
            # Use the combined query engine which intelligently routes to appropriate sources
            response = self.combined_query_engine.query(query)

            if self.enable_print:
                print(f"Query response: {response}")
                if hasattr(response, "source_nodes") and response.source_nodes:
                    print(f"Found {len(response.source_nodes)} source nodes")
                    # Show which sources were used
                    source_breakdown = {}
                    for node in response.source_nodes:
                        source_path = node.metadata.get("source_path", "unknown")
                        source_breakdown.setdefault(source_path, 0)
                        source_breakdown[source_path] += 1

                    print("Sources used:")
                    for source, count in source_breakdown.items():
                        print(f"  - {source}: {count} nodes")

            # Extract text results from the response
            if hasattr(response, "source_nodes") and response.source_nodes:
                # Get the source nodes and extract text
                results = []
                for node in response.source_nodes[:num_results]:
                    results.append(node.text)
                return results
            else:
                # If no source nodes, return the response text as a single result
                return [str(response)]

        except Exception as e:
            if self.enable_print:
                print(f"Error using combined query engine: {str(e)}")
                print("Falling back to manual retrieval")
            return await self._manual_retrieve(query, num_results)

    async def _manual_retrieve(self, query: str, num_results: int) -> list[str]:
        """Retrieve from combined index as fallback."""
        if self.enable_print:
            print(f"Manual retrieval for {num_results} results using combined index")

        # Check if combined index exists
        if "combined" not in self.indices:
            if self.enable_print:
                print("Warning: No combined index available, cannot retrieve")
            return []

        try:
            # Use combined index for retrieval
            combined_index = self.indices["combined"]
            retriever = combined_index.as_retriever(similarity_top_k=num_results)
            nodes = retriever.retrieve(query)

            # Extract text results and track source breakdown
            results = []
            source_breakdown = {}

            for node in nodes:
                results.append(node.text)

                # Track which sources contributed to results
                if self.enable_print:
                    source_path = node.metadata.get("source_path", "unknown")
                    source_name = Path(source_path).name if source_path != "unknown" else "unknown"
                    source_breakdown.setdefault(source_name, 0)
                    source_breakdown[source_name] += 1

            if self.enable_print:
                print(f"Manual retrieval returned {len(results)} results from combined index")
                if source_breakdown:
                    print("Results by source:")
                    for source, count in sorted(source_breakdown.items()):
                        print(f"  - {source}: {count} results")

            return results

        except Exception as e:
            if self.enable_print:
                print(f"Error retrieving from combined index: {str(e)}")
            return []


if __name__ == "__main__":

    base_url = "https://simulationresearch.lbl.gov/modelica/releases/latest/help/{}"

    paths = []
    for doc_site_name in [
        # ASHRAE Guideline 36 validation models as standard reference examples of HVAC operation sequences
        "Buildings_Controls_OBC_ASHRAE_G36_AHUs_MultiZone_VAV_Economizers_Subsequences_Limits_Validation.html",
        "Buildings_Controls_OBC_ASHRAE_G36_AHUs_MultiZone_VAV_Economizers_Subsequences_Modulations_Validation.html",
        "Buildings_Controls_OBC_ASHRAE_G36_AHUs_MultiZone_VAV_Economizers_Subsequences_Validation.html",
        "Buildings_Controls_OBC_ASHRAE_G36_AHUs_MultiZone_VAV_Economizers_Validation.html",
        "Buildings_Controls_OBC_ASHRAE_G36_AHUs_MultiZone_VAV_SetPoints_OutdoorAirFlow_ASHRAE62_1_Validation.html",
        "Buildings_Controls_OBC_ASHRAE_G36_AHUs_MultiZone_VAV_SetPoints_OutdoorAirFlow_Title24_Validation.html",
        "Buildings_Controls_OBC_ASHRAE_G36_AHUs_MultiZone_VAV_SetPoints_Validation.html",
        "Buildings_Controls_OBC_ASHRAE_G36_AHUs_MultiZone_VAV_Validation.html",
    ]:
        doc_path = base_url.format(doc_site_name)
        paths.append(doc_path)

    import asyncio

    doc_store = RAGStore(doc_paths=paths, output_folder="proposal/data/storage", force_reload=True, enable_print=True)
    answer = asyncio.run(doc_store._manual_retrieve("Recommend CDL code block or program for this problem", num_results=10))
    print(len(answer))
