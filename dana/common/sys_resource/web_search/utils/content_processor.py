"""Content processing with query-focused summarization."""

import logging
from .reason import LLM

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Process content with query-focused extraction and summarization."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = LLM(model=model)

    async def process_content(self, content: str, query: str) -> str:
        """
        Process content based on length and query relevance:
        - < 500 chars: return as-is
        - 500-10000 chars: summarize for query relevance
        - > 10000 chars: use RAG approach
        """
        content_length = len(content)

        if content_length < 500:
            logger.debug(f"Short content ({content_length} chars), keeping as-is")
            return content

        if content_length <= 10000:
            logger.info(f"Summarizing content ({content_length} chars) for query: {query}")
            return await self._summarize_for_query(content, query)

        logger.info(f"Long content ({content_length} chars), using RAG approach")
        return await self._process_with_rag(content, query)

    async def _summarize_for_query(self, content: str, query: str) -> str:
        """Extract only query-relevant content."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": f"""Extract only the information from this content that directly relates to: "{query}"

Content:
{content}

Instructions:
- Focus ONLY on information relevant to the query
- Keep all technical specs, numbers, and specific details
- Remove unrelated sections completely
- Be concise but complete for the query topic
- If no relevant information exists, say "No relevant information found"

Relevant information:""",
                }
            ]

            summary = await self.llm.reason(messages)
            if summary and "no relevant information" not in summary.lower():
                logger.info(f"Summarized {len(content)} -> {len(summary)} chars")
                return summary.strip()
            else:
                logger.warning(f"No relevant content found for query: {query}")
                return summary

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return content[:1000] + "... [truncated - summarization failed]"

    async def _process_with_rag(self, content: str, query: str) -> str:
        """Process very long content with RAG-based summarization."""
        try:
            from .summarizer import ContentSummarizer

            logger.info(f"Processing {len(content)} chars with RAG for query: {query}")

            # Create content summarizer with RAG capability
            summarizer = ContentSummarizer(content)

            # Use RAG to summarize for the specific query
            summary = await summarizer.summarize_for_query(query)

            if summary and len(summary.strip()) > 0:
                logger.info(f"RAG processing: {len(content)} -> {len(summary)} chars")
                return summary.strip()
            else:
                logger.warning("RAG returned empty summary, falling back")
                return "no relevant information found"

        except Exception as e:
            logger.error(f"RAG processing failed: {e}")
            return content[:1000] + "... [truncated - RAG processing failed]"
