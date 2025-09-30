import os
from pathlib import Path
import asyncio

from llama_index.core import Settings
from dana.common.mixins.tool_callable import ToolCallable
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.common.sys_resource.embedding import get_default_embedding_model
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.vector_stores.duckdb import DuckDBVectorStore
from llama_index.core.schema import Document, NodeWithScore
from dana.common.sys_resource.rag.pipeline.document_loader import DocumentLoader
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
from llama_index.core.schema import MetadataMode

CACHE_DIR = os.getenv("RAG_CACHE_PATH", os.path.expanduser("~/.dana/.cache/rag"))
PERSIST_DIR = os.path.join(CACHE_DIR, "storage")
Path(PERSIST_DIR).mkdir(parents=True, exist_ok=True)
RAG_NAME = "dana_rag_db"


class RAGResource(BaseSysResource):
    """RAG resource for document retrieval."""

    def __init__(
        self,
        sources: list[str],
        name: str = "rag_resource",
        cache_dir: str | None = CACHE_DIR,  # Changed default to None
        force_reload: bool = False,
        description: str | None = None,
        chunk_size: int = 1024,
        chunk_overlap: int = 256,
        debug: bool = False,
        reranking: bool = False,
        initial_multiplier: int = 2,
        return_raw: bool = False,
        num_results: int = 15,
        dimensions: int = 1024,
        embed_batch_size: int = 512,
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

    def get_existing_filenames_and_sizes(self) -> list[tuple[str, int]]:
        import duckdb

        conn = duckdb.connect(os.path.join(PERSIST_DIR, self.get_table_name()))
        result = conn.execute(f"""
            SELECT DISTINCT 
                json_extract_string(metadata_, '$.file_name')::VARCHAR as file_name, 
                json_extract(metadata_, '$.file_size')::INTEGER as file_size 
            FROM {self.get_table_name()}.main.documents;""").fetchall()
        return result

    def _load_or_create_index(self, document_dict: dict[str, list[Document]]) -> None:
        def get_vector_store():
            return DuckDBVectorStore(database_name=self.get_table_name(), persist_dir=PERSIST_DIR, embed_dim=self.dimension)

        self.embed_model = get_default_embedding_model(dimension_override=self.dimension)
        if hasattr(self.embed_model, "dimensions"):
            # override using dimension from embed_model
            self.dimension = self.embed_model.dimensions
        uri = os.path.join(PERSIST_DIR, self.get_table_name())
        if Path(uri).exists():
            print(f"Loading index from {uri}")
            vector_store = get_vector_store()
            storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir=PERSIST_DIR)
            self.vector_index = load_index_from_storage(
                storage_context,
                embed_model=self.embed_model,
            )
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
            self.vector_index.storage_context.persist(persist_dir=PERSIST_DIR)

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
            document_dict = await self.loader.load_sources(self.sources)
            self._load_or_create_index(document_dict)
            self.documents = document_dict
            self._is_ready = True
            self._filenames = [] if self.documents is None else list(self.documents.keys())
            self.existing_filenames = self.get_existing_filenames_and_sizes()

            mapping = {}
            for filename, docs in self.documents.items():
                if len(docs):
                    mapping[(docs[0].metadata["file_name"], docs[0].metadata["file_size"])] = filename

            doc_to_add = set(mapping.keys()).difference(set(self.existing_filenames))

            print(f"Adding {doc_to_add} documents to the index")

            tasks = []
            for data in doc_to_add:
                docs = self.documents[mapping[data]]
                tasks.extend([self.vector_index.ainsert(doc) for doc in docs])

            await asyncio.gather(*tasks)

            self.vector_index.storage_context.persist(persist_dir=PERSIST_DIR)

    async def retrieve(self, query: str, num_results: int = 10) -> list[NodeWithScore]:
        if not self._is_ready:
            await self.initialize()
        return await self.vector_index.as_retriever(similarity_top_k=num_results, embed_model=self.embed_model).aretrieve(query)

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
    rag = RAGResource(
        sources=[
            "/Users/lam/Downloads/STD-ENG-015.pdf",
            "/Users/lam/Downloads/Fans Best practice work pack rev 4.pdf",
            "/Users/lam/Desktop/repos/opendxa/docs/reference",
            "docs/releases",
        ],
        reranking=True,
        debug=True,
    )
    import asyncio

    print(rag.is_available)
    print(rag.filenames)

    print(len(asyncio.run(rag.query("Procedure for monitoring sugar manufacturing process"), debug=True)))
