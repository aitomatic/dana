"""Tests for web search utility functions."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from dana.common.sys_resource.web_search.utils.content_processor import ContentProcessor
from dana.common.sys_resource.web_search.utils.summarizer import ContentSummarizer
from dana.common.sys_resource.web_search.utils.reason import LLM


class TestLLM:
    """Tests for LLM reasoning utility."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("openai.AsyncOpenAI"):
            self.llm = LLM(model="gpt-4o-mini")

    @pytest.mark.asyncio
    async def test_reason_text_output(self):
        """Test LLM reasoning with text output."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"},
        ]

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "2+2 equals 4."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch.object(self.llm.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await self.llm.reason(messages)

            assert result == "2+2 equals 4."
            mock_create.assert_called_once_with(
                model="gpt-4o-mini",
                messages=messages,
                response_format={"type": "text"},
            )

    @pytest.mark.asyncio
    async def test_reason_with_structured_output(self):
        """Test LLM reasoning with structured JSON output."""
        messages = [
            {"role": "user", "content": "Return a JSON object with name and age."},
        ]

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"name": "John", "age": 30}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch.object(self.llm.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await self.llm.reason_with_structured_output(messages)

            assert isinstance(result, dict)
            assert result["name"] == "John"
            assert result["age"] == 30
            mock_create.assert_called_once_with(
                model="gpt-4o-mini",
                messages=messages,
                response_format={"type": "json_object"},
            )

    @pytest.mark.asyncio
    async def test_reason_empty_response(self):
        """Test LLM reasoning with empty response."""
        messages = [{"role": "user", "content": "Test question"}]

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch.object(self.llm.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await self.llm.reason(messages)

            assert result == ""

    @pytest.mark.asyncio
    async def test_reason_structured_empty_response(self):
        """Test LLM reasoning with structured output and empty response."""
        messages = [{"role": "user", "content": "Return empty JSON"}]

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch.object(self.llm.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await self.llm.reason_with_structured_output(messages)

            assert result == {}


class TestContentProcessor:
    """Tests for ContentProcessor utility."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("dana.common.sys_resource.web_search.utils.reason.LLM"):
            self.processor = ContentProcessor(model="gpt-4o-mini")
            self.processor.llm = MagicMock()

    @pytest.mark.asyncio
    async def test_process_content_short(self):
        """Test content processing with short content (< 500 chars)."""
        short_content = "This is a short content piece with less than 500 characters."
        query = "test query"

        result = await self.processor.process_content(short_content, query)

        assert result == short_content
        # Should not call LLM for short content
        self.processor.llm.reason.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_content_medium_summarization(self):
        """Test content processing with medium content (500-10000 chars) for summarization."""
        # Create content between 500-10000 characters
        medium_content = "This is a medium length content. " * 20  # ~660 characters
        query = "specific information"

        # Mock LLM response
        self.processor.llm.reason = AsyncMock(return_value="Summarized content relevant to query")

        result = await self.processor.process_content(medium_content, query)

        assert result == "Summarized content relevant to query"
        self.processor.llm.reason.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_content_long_rag_approach(self):
        """Test content processing with long content (> 10000 chars) using RAG."""
        # Create long content
        long_content = "This is a very long content piece. " * 300  # ~10800 characters
        query = "specific information"

        # Mock RAG processing
        mock_summarizer = MagicMock()
        mock_summarizer.summarize_for_query = AsyncMock(return_value="RAG-processed summary")

        with patch("dana.common.sys_resource.web_search.utils.summarizer.ContentSummarizer") as mock_summarizer_class:
            mock_summarizer_class.return_value = mock_summarizer

            result = await self.processor.process_content(long_content, query)

            assert result == "RAG-processed summary"
            mock_summarizer_class.assert_called_once_with(long_content)
            mock_summarizer.summarize_for_query.assert_called_once_with(query)

    @pytest.mark.asyncio
    async def test_summarize_for_query_success(self):
        """Test successful query-focused summarization."""
        content = "This content contains information about Intel processors and their specifications."
        query = "Intel processor specifications"

        self.processor.llm.reason = AsyncMock(return_value="Intel processor specifications include core count and frequency.")

        result = await self.processor._summarize_for_query(content, query)

        assert result == "Intel processor specifications include core count and frequency."

        # Verify the prompt structure
        call_args = self.processor.llm.reason.call_args[0][0]
        assert len(call_args) == 1
        assert "Extract only the information" in call_args[0]["content"]
        assert query in call_args[0]["content"]
        assert content in call_args[0]["content"]

    @pytest.mark.asyncio
    async def test_summarize_for_query_no_relevant_info(self):
        """Test summarization when no relevant information is found."""
        content = "This content is about cooking recipes."
        query = "Intel processor specifications"

        self.processor.llm.reason = AsyncMock(return_value="No relevant information found")

        result = await self.processor._summarize_for_query(content, query)

        assert result == "No relevant information found"

    @pytest.mark.asyncio
    async def test_summarize_for_query_exception_handling(self):
        """Test summarization with exception handling."""
        content = "Test content"
        query = "test query"

        self.processor.llm.reason = AsyncMock(side_effect=Exception("API error"))

        result = await self.processor._summarize_for_query(content, query)

        assert "truncated - summarization failed" in result
        assert content[:1000] in result

    @pytest.mark.asyncio
    async def test_process_with_rag_success(self):
        """Test successful RAG processing."""
        long_content = "Long content for RAG processing"
        query = "specific query"

        mock_summarizer = MagicMock()
        mock_summarizer.summarize_for_query = AsyncMock(return_value="RAG summary result")

        with patch("dana.common.sys_resource.web_search.utils.summarizer.ContentSummarizer") as mock_summarizer_class:
            mock_summarizer_class.return_value = mock_summarizer

            result = await self.processor._process_with_rag(long_content, query)

            assert result == "RAG summary result"

    @pytest.mark.asyncio
    async def test_process_with_rag_empty_result(self):
        """Test RAG processing with empty result."""
        long_content = "Long content"
        query = "query"

        mock_summarizer = MagicMock()
        mock_summarizer.summarize_for_query = AsyncMock(return_value="")

        with patch("dana.common.sys_resource.web_search.utils.summarizer.ContentSummarizer") as mock_summarizer_class:
            mock_summarizer_class.return_value = mock_summarizer

            result = await self.processor._process_with_rag(long_content, query)

            assert result == "no relevant information found"

    @pytest.mark.asyncio
    async def test_process_with_rag_exception_handling(self):
        """Test RAG processing with exception handling."""
        long_content = "Long content for RAG"
        query = "query"

        with patch("dana.common.sys_resource.web_search.utils.summarizer.ContentSummarizer") as mock_summarizer_class:
            mock_summarizer_class.side_effect = Exception("RAG initialization failed")

            result = await self.processor._process_with_rag(long_content, query)

            assert "truncated - RAG processing failed" in result
            assert long_content[:1000] in result


class TestContentSummarizer:
    """Tests for ContentSummarizer utility."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_content = "This is test content for summarization with various technical details and specifications."

    def test_content_summarizer_initialization(self):
        """Test ContentSummarizer initialization."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource"):
            with patch.object(ContentSummarizer, "_build_query_engine"):
                summarizer = ContentSummarizer(self.test_content)

                assert summarizer.content == self.test_content
                assert summarizer.retriever is None

    def test_build_query_engine_success(self):
        """Test successful query engine building."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource"):
            with patch("llama_index.core.VectorStoreIndex") as mock_index_class:
                with patch("dana.common.sys_resource.embedding.embedding_integrations.LlamaIndexEmbeddingResource"):
                    # Mock the index and retriever
                    mock_index = MagicMock()
                    mock_retriever = MagicMock()
                    mock_index.as_retriever.return_value = mock_retriever
                    mock_index_class.from_documents.return_value = mock_index

                    summarizer = ContentSummarizer(self.test_content)

                    assert summarizer.retriever == mock_retriever
                    mock_index_class.from_documents.assert_called_once()

    def test_build_query_engine_exception_handling(self):
        """Test query engine building with exception handling."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource"):
            with patch("llama_index.core.VectorStoreIndex") as mock_index_class:
                mock_index_class.from_documents.side_effect = Exception("Index building failed")

                summarizer = ContentSummarizer(self.test_content)

                assert summarizer.retriever is None

    @pytest.mark.asyncio
    async def test_retrieve_success(self):
        """Test successful content retrieval."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource"):
            with patch.object(ContentSummarizer, "_build_query_engine"):
                summarizer = ContentSummarizer(self.test_content)

                # Mock retriever
                mock_node1 = MagicMock()
                mock_node1.text = "First relevant chunk"
                mock_node2 = MagicMock()
                mock_node2.text = "Second relevant chunk"

                mock_retriever = AsyncMock()
                mock_retriever.aretrieve.return_value = [mock_node1, mock_node2]
                summarizer.retriever = mock_retriever

                result = await summarizer.retrieve("test query")

                assert result == ["First relevant chunk", "Second relevant chunk"]
                mock_retriever.aretrieve.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_retrieve_no_retriever(self):
        """Test retrieval when no retriever is available."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource"):
            with patch.object(ContentSummarizer, "_build_query_engine"):
                summarizer = ContentSummarizer(self.test_content)
                summarizer.retriever = None

                result = await summarizer.retrieve("test query")

                assert result is None

    @pytest.mark.asyncio
    async def test_retrieve_exception_handling(self):
        """Test retrieval with exception handling."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource"):
            with patch.object(ContentSummarizer, "_build_query_engine"):
                summarizer = ContentSummarizer(self.test_content)

                mock_retriever = AsyncMock()
                mock_retriever.aretrieve.side_effect = Exception("Retrieval failed")
                summarizer.retriever = mock_retriever

                result = await summarizer.retrieve("test query")

                assert result is None

    @pytest.mark.asyncio
    async def test_get_relevant_context(self):
        """Test getting relevant context chunks."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource"):
            with patch.object(ContentSummarizer, "_build_query_engine"):
                summarizer = ContentSummarizer(self.test_content)

                # Mock the retrieve method
                summarizer.retrieve = AsyncMock(return_value=["Chunk 1", "Chunk 2", "Chunk 3"])

                result = await summarizer.get_relevant_context("test query")

                assert result == "Chunk 1\n\nChunk 2\n\nChunk 3"

    @pytest.mark.asyncio
    async def test_get_relevant_context_empty_chunks(self):
        """Test getting relevant context with empty chunks."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource"):
            with patch.object(ContentSummarizer, "_build_query_engine"):
                summarizer = ContentSummarizer(self.test_content)
                summarizer.retrieve = AsyncMock(return_value=[])

                result = await summarizer.get_relevant_context("test query")

                assert result is None

    @pytest.mark.asyncio
    async def test_summarize_for_query_success(self):
        """Test successful query-focused summarization."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource") as mock_llm_resource_class:
            with patch.object(ContentSummarizer, "_build_query_engine"):
                # Mock LLM response
                mock_response = MagicMock()
                mock_response.success = True
                mock_response.content = {"choices": [{"message": {"content": "Generated summary content"}}]}

                mock_llm_instance = MagicMock()
                mock_llm_instance.query = AsyncMock(return_value=mock_response)
                mock_llm_resource_class.return_value = mock_llm_instance

                summarizer = ContentSummarizer(self.test_content)
                summarizer.get_relevant_context = AsyncMock(return_value="Relevant context chunks")

                result = await summarizer.summarize_for_query("test query")

                assert result == "Generated summary content"

    @pytest.mark.asyncio
    async def test_summarize_for_query_no_context(self):
        """Test summarization with no relevant context."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource"):
            with patch.object(ContentSummarizer, "_build_query_engine"):
                summarizer = ContentSummarizer(self.test_content)
                summarizer.get_relevant_context = AsyncMock(return_value=None)

                result = await summarizer.summarize_for_query("test query")

                assert result is None

    @pytest.mark.asyncio
    async def test_summarize_for_query_llm_failure(self):
        """Test summarization with LLM failure."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource") as mock_llm_resource_class:
            with patch.object(ContentSummarizer, "_build_query_engine"):
                # Mock failed LLM response
                mock_response = MagicMock()
                mock_response.success = False
                mock_response.error = "LLM query failed"

                mock_llm_instance = MagicMock()
                mock_llm_instance.query = AsyncMock(return_value=mock_response)
                mock_llm_resource_class.return_value = mock_llm_instance

                summarizer = ContentSummarizer(self.test_content)
                # Mock both retrieve and get_relevant_context to avoid any internal calls
                summarizer.retrieve = AsyncMock(return_value=["Context chunk 1", "Context chunk 2"])
                summarizer.get_relevant_context = AsyncMock(return_value="Context chunk 1\n\nContext chunk 2")

                result = await summarizer.summarize_for_query("test query")

                assert result is None

    @pytest.mark.skip(reason="Async mocking issue - TODO: fix mock setup for LLM resource")
    @pytest.mark.asyncio
    async def test_summarize_for_query_different_response_formats(self):
        """Test summarization with different LLM response formats."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource") as mock_llm_resource_class:
            with patch.object(ContentSummarizer, "_build_query_engine"):
                with patch.object(
                    ContentSummarizer, "get_relevant_context", new=AsyncMock(return_value="Context chunk 1\n\nContext chunk 2")
                ):
                    summarizer = ContentSummarizer(self.test_content)

                    mock_llm_instance = AsyncMock()
                    mock_llm_resource_class.return_value = mock_llm_instance

                    # Test string content format
                    mock_response = MagicMock()
                    mock_response.success = True
                    mock_response.content = "Direct string response"
                    mock_llm_instance.query = AsyncMock(return_value=mock_response)

                    result = await summarizer.summarize_for_query("test query")
                    assert result == "Direct string response"

                    # Test dict with alternative keys
                    mock_response.content = {"content": "Alternative content key"}
                    result = await summarizer.summarize_for_query("test query")
                    assert result == "Alternative content key"

                    # Test dict with response key
                    mock_response.content = {"response": "Response key content"}
                    result = await summarizer.summarize_for_query("test query")
                    assert result == "Response key content"

    @pytest.mark.asyncio
    async def test_summarize_for_query_exception_handling(self):
        """Test summarization with exception handling."""
        with patch("dana.common.sys_resource.web_search.utils.summarizer.LegacyLLMResource") as mock_llm_resource_class:
            with patch.object(ContentSummarizer, "_build_query_engine"):
                with patch.object(
                    ContentSummarizer, "get_relevant_context", new=AsyncMock(return_value="Context chunk 1\n\nContext chunk 2")
                ):
                    # Create mock LLM instance that fails during query
                    mock_llm_instance = AsyncMock()
                    mock_llm_resource_class.return_value = mock_llm_instance
                    mock_llm_instance.query = AsyncMock(side_effect=Exception("Query failed"))

                    summarizer = ContentSummarizer(self.test_content)

                    result = await summarizer.summarize_for_query("test query")

                    assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
