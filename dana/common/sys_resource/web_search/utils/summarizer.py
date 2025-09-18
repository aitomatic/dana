"""Content summarization utility using RAG (Retrieval-Augmented Generation)."""

import logging

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc

logger = logging.getLogger(__name__)


class ContentSummarizer:
    """Content summarizer using RAG for query-focused summarization."""

    def __init__(self, content: str, top_k: int = 5):
        """
        Initialize ContentSummarizer with content.

        Args:
            content: Text content to index
            top_k: Number of top relevant chunks to retrieve
        """
        self.content = content
        self.retriever = None
        self.top_k = top_k

        # Initialize LLM resource for summarization
        self._llm_resource = LegacyLLMResource(
            name="web_search_content_summarizer",
            temperature=0.1,  # Low temperature for consistent, factual summaries
        )

        self._build_retriever()

    def _build_retriever(self):
        """Build retrieval system from content."""
        try:
            from llama_index.core import VectorStoreIndex, Document
            from dana.common.sys_resource.embedding.embedding_integrations import LlamaIndexEmbeddingResource

            # Get Dana's standard embedding model
            embedding_resource = LlamaIndexEmbeddingResource()
            embed_model = embedding_resource.get_default_embedding_model()

            # Create document from content
            documents = [Document(text=self.content)]

            # Build vector index with specific embedding model
            index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)

            # Create retriever only (no LLM response generation)
            self.retriever = index.as_retriever(similarity_top_k=self.top_k)

            logger.debug(f"Content retriever built for {len(self.content)} chars")

        except Exception as e:
            logger.error(f"Failed to build content retriever: {e}")
            self.retriever = None

    async def retrieve(self, query: str) -> list | None:
        """
        Retrieve relevant document chunks for a query.

        Args:
            query: Query to search for relevant content

        Returns:
            List of relevant text chunks or None if failed
        """
        if not self.retriever:
            logger.error("Retriever not available")
            return None

        try:
            nodes = await self.retriever.aretrieve(query)
            return [node.text for node in nodes] if nodes else []

        except Exception as e:
            logger.error(f"Content retrieval failed: {e}")
            return None

    async def get_relevant_context(self, query: str) -> str | None:
        """
        Get relevant context chunks for a query (for use with external LLM).

        Args:
            query: Query to search for relevant content

        Returns:
            Concatenated relevant text chunks or None if failed
        """
        chunks = await self.retrieve(query)
        if not chunks:
            return None

        return "\n\n".join(chunks)

    async def summarize_for_query(self, query: str, filter_context: bool = True) -> str | None:
        """
        Summarize content focusing on specific query using RAG approach.

        Args:
            query: Query to focus summarization on

        Returns:
            Query-focused summary or None if failed
        """
        try:
            # Get relevant context chunks
            if filter_context:
                relevant_context = await self.get_relevant_context(query)
            else:
                relevant_context = self.content

            if not relevant_context:
                logger.warning("No relevant context found for query")
                return None

            # Prepare messages for LLM
            system_message = {
                "role": "system",
                "content": (
                    "You are a helpful assistant that summarizes content based on specific queries. "
                    "Focus on information directly relevant to the user's query. "
                    "Be concise but comprehensive, including technical specifications and important details."
                ),
            }

            user_message = {
                "role": "user",
                "content": (
                    f"Based on the following content, provide a summary that focuses specifically on: {query}\n\n"
                    f"Content:\n{relevant_context}\n\n"
                    f"Please summarize all information relevant to '{query}', including technical specifications, "
                    f"details, and any specific information related to this query."
                ),
            }

            # Call LLM resource
            request = BaseRequest(
                arguments={
                    "messages": [system_message, user_message],
                    "max_tokens": 2000,  # Reasonable limit for summaries
                }
            )

            response = await self._llm_resource.query(request)

            if response.success and response.content:
                summary = Misc.get_response_content(response)

                logger.debug(f"Generated summary for query '{query}': {len(summary)} chars")
                return summary
            else:
                logger.error(f"LLM query failed: {response.error}")
                return None

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None
