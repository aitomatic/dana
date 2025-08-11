"""Test TabularIndex core functionality."""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
import asyncio

from dana.common.resource.tabular_index.tabular_index import TabularIndex
from dana.common.resource.tabular_index.config import TabularConfig, BatchSearchConfig


class TestTabularIndex(unittest.TestCase):
    """Test TabularIndex class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock embedding field constructor
        self.mock_embedding_constructor = MagicMock(return_value="test embedding text")

        # Create a basic config
        self.config = TabularConfig(
            source="test.csv",
            embedding_field_constructor=self.mock_embedding_constructor,
            table_name="test_table",
            cache_dir="/tmp/test_cache",
        )

        # Create mock dependencies
        self.mock_embedding_model = MagicMock()
        self.mock_provider = MagicMock()
        self.mock_vector_store = MagicMock()
        self.mock_provider.vector_store = self.mock_vector_store

        # Create TabularIndex instance
        self.tabular_index = TabularIndex(config=self.config, embedding_model=self.mock_embedding_model, provider=self.mock_provider)

    def test_init(self):
        """Test TabularIndex initialization."""
        self.assertEqual(self.tabular_index.config, self.config)
        self.assertEqual(self.tabular_index.embedding_model, self.mock_embedding_model)
        self.assertEqual(self.tabular_index.provider, self.mock_provider)
        self.assertIsNone(self.tabular_index.index)

    def test_should_rebuild_force_reload_true(self):
        """Test _should_rebuild when force_reload is True."""
        self.config.force_reload = True
        result = self.tabular_index._should_rebuild()
        self.assertTrue(result)

    def test_should_rebuild_vector_store_not_exists(self):
        """Test _should_rebuild when vector store doesn't exist."""
        self.config.force_reload = False
        with patch.object(self.tabular_index, "_vector_store_exists", return_value=False):
            result = self.tabular_index._should_rebuild()
            self.assertTrue(result)

    def test_should_rebuild_vector_store_exists_but_no_data(self):
        """Test _should_rebuild when vector store exists but has no data."""
        self.config.force_reload = False
        with patch.object(self.tabular_index, "_vector_store_exists", return_value=True):
            with patch.object(self.tabular_index, "_vector_store_has_data", return_value=False):
                result = self.tabular_index._should_rebuild()
                self.assertTrue(result)

    def test_should_rebuild_vector_store_exists_with_data(self):
        """Test _should_rebuild when vector store exists and has data."""
        self.config.force_reload = False
        with patch.object(self.tabular_index, "_vector_store_exists", return_value=True):
            with patch.object(self.tabular_index, "_vector_store_has_data", return_value=True):
                result = self.tabular_index._should_rebuild()
                self.assertFalse(result)

    def test_vector_store_exists(self):
        """Test _vector_store_exists method."""
        self.mock_provider.exists.return_value = True
        result = self.tabular_index._vector_store_exists()
        self.assertTrue(result)
        self.mock_provider.exists.assert_called_once()

    def test_vector_store_has_data(self):
        """Test _vector_store_has_data method."""
        self.mock_provider.has_data.return_value = True
        result = self.tabular_index._vector_store_has_data()
        self.assertTrue(result)
        self.mock_provider.has_data.assert_called_once()

    @patch("os.path.exists")
    def test_validate_rebuild_preconditions_success(self, mock_exists):
        """Test _validate_rebuild_preconditions with valid conditions."""
        mock_exists.return_value = True
        with patch("pandas.read_csv"):
            # Should not raise exception
            self.tabular_index._validate_rebuild_preconditions()

    @patch("os.path.exists")
    def test_validate_rebuild_preconditions_file_not_found(self, mock_exists):
        """Test _validate_rebuild_preconditions when source file doesn't exist."""
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError) as context:
            self.tabular_index._validate_rebuild_preconditions()
        self.assertIn("Source data not found", str(context.exception))

    @patch("os.path.exists")
    @patch("pandas.read_csv")
    def test_validate_rebuild_preconditions_unreadable_csv(self, mock_read_csv, mock_exists):
        """Test _validate_rebuild_preconditions when CSV is not readable."""
        mock_exists.return_value = True
        mock_read_csv.side_effect = pd.errors.EmptyDataError("No data")

        with self.assertRaises(ValueError) as context:
            self.tabular_index._validate_rebuild_preconditions()
        self.assertIn("Source data is not readable", str(context.exception))

    def test_validate_rebuild_preconditions_no_embedding_model(self):
        """Test _validate_rebuild_preconditions when embedding model is None."""
        self.tabular_index.embedding_model = None
        with patch("os.path.exists", return_value=True):
            with patch("pandas.read_csv"):  # Mock successful file read
                with self.assertRaises(ValueError) as context:
                    self.tabular_index._validate_rebuild_preconditions()
                self.assertIn("Embedding model is not configured", str(context.exception))

    def test_validate_rebuild_preconditions_no_provider(self):
        """Test _validate_rebuild_preconditions when provider is None."""
        self.tabular_index.provider = None
        with patch("os.path.exists", return_value=True):
            with patch("pandas.read_csv"):  # Mock successful file read
                with self.assertRaises(ValueError) as context:
                    self.tabular_index._validate_rebuild_preconditions()
                self.assertIn("Vector store provider is not configured", str(context.exception))

    def test_drop_existing_vector_store(self):
        """Test _drop_existing_vector_store method."""
        self.tabular_index._drop_existing_vector_store()
        self.mock_provider.drop_data.assert_called_once()

    def test_retrieve_basic(self):
        """Test retrieve method with basic functionality."""

        async def _test():
            # Setup mock index
            mock_index = MagicMock()
            mock_retriever = MagicMock()
            mock_node = MagicMock()
            mock_node.text = "test text"
            mock_node.metadata = {"key": "value"}

            mock_retriever.aretrieve = AsyncMock(return_value=[mock_node])
            mock_index.as_retriever.return_value = mock_retriever
            self.tabular_index.index = mock_index

            result = await self.tabular_index.retrieve("test query", 5)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["text"], "test text")
            self.assertEqual(result[0]["metadata"], {"key": "value"})
            mock_index.as_retriever.assert_called_once_with(similarity_top_k=5)
            mock_retriever.aretrieve.assert_called_once_with("test query")

        asyncio.run(_test())

    def test_retrieve_initializes_if_no_index(self):
        """Test retrieve method initializes index if not present."""

        async def _test():
            self.tabular_index.index = None

            with patch.object(self.tabular_index, "initialize", new_callable=AsyncMock) as mock_init:
                # Setup mock index after initialization
                mock_index = MagicMock()
                mock_retriever = MagicMock()
                mock_retriever.aretrieve = AsyncMock(return_value=[])
                mock_index.as_retriever.return_value = mock_retriever

                async def set_index():
                    self.tabular_index.index = mock_index

                mock_init.side_effect = set_index

                result = await self.tabular_index.retrieve("test query")

                mock_init.assert_called_once()
                self.assertEqual(result, [])

        asyncio.run(_test())

    def test_single_search_basic(self):
        """Test single_search method."""

        async def _test():
            # Mock the index to be already initialized
            self.tabular_index.index = MagicMock()

            with patch.object(self.tabular_index, "retrieve", new_callable=AsyncMock) as mock_retrieve:
                mock_retrieve.return_value = [{"text": "result", "metadata": {}}]

                result = await self.tabular_index.single_search("test query", 10)

                expected = {"query": "test query", "results": [{"text": "result", "metadata": {}}]}
                self.assertEqual(result, expected)
                mock_retrieve.assert_called_once_with("test query", 10)

        asyncio.run(_test())

    def test_single_search_with_callback(self):
        """Test single_search method with callback."""

        async def _test():
            # Mock the index to be already initialized
            self.tabular_index.index = MagicMock()
            mock_callback = MagicMock()

            with patch.object(self.tabular_index, "retrieve", new_callable=AsyncMock) as mock_retrieve:
                mock_retrieve.return_value = [{"text": "result", "metadata": {}}]

                result = await self.tabular_index.single_search("test query", 10, mock_callback)

                expected_results = [{"text": "result", "metadata": {}}]
                mock_callback.assert_called_once_with("test query", expected_results)
                self.assertEqual(result["query"], "test query")
                self.assertEqual(result["results"], expected_results)

        asyncio.run(_test())

    def test_batch_search_basic(self):
        """Test batch_search method."""

        async def _test():
            # Mock the index to be already initialized
            self.tabular_index.index = MagicMock()
            queries = ["query1", "query2"]
            batch_config = BatchSearchConfig(batch_size=10, top_k=5)

            with patch.object(self.tabular_index, "single_search", new_callable=AsyncMock) as mock_single:
                mock_single.side_effect = [
                    {"query": "query1", "results": [{"text": "result1", "metadata": {}}]},
                    {"query": "query2", "results": [{"text": "result2", "metadata": {}}]},
                ]

                result = await self.tabular_index.batch_search(queries, batch_config)

                self.assertEqual(len(result), 2)
                self.assertEqual(result[0]["query"], "query1")
                self.assertEqual(result[1]["query"], "query2")
                self.assertEqual(mock_single.call_count, 2)

        asyncio.run(_test())

    def test_batch_search_with_callback(self):
        """Test batch_search method with callback."""

        async def _test():
            # Mock the index to be already initialized
            self.tabular_index.index = MagicMock()
            queries = ["query1"]
            batch_config = BatchSearchConfig()
            mock_callback = MagicMock()

            with patch.object(self.tabular_index, "single_search", new_callable=AsyncMock) as mock_single:
                mock_single.return_value = {"query": "query1", "results": []}

                await self.tabular_index.batch_search(queries, batch_config, mock_callback)

                # Callback should be passed to single_search
                mock_single.assert_called_once_with("query1", batch_config.top_k, mock_callback)

        asyncio.run(_test())

    def test_general_query_basic(self):
        """Test general_query method."""

        async def _test():
            # Mock the index to be already initialized
            self.tabular_index.index = MagicMock()

            with patch.object(self.tabular_index, "retrieve", new_callable=AsyncMock) as mock_retrieve:
                mock_retrieve.return_value = [{"text": "result", "metadata": {}}]

                result = await self.tabular_index.general_query("test query")

                self.assertEqual(result, [{"text": "result", "metadata": {}}])
                mock_retrieve.assert_called_once_with("test query")  # No default top_k passed

        asyncio.run(_test())

    def test_general_query_with_callback(self):
        """Test general_query method with callback."""

        async def _test():
            # Mock the index to be already initialized
            self.tabular_index.index = MagicMock()
            mock_callback = MagicMock()

            with patch.object(self.tabular_index, "retrieve", new_callable=AsyncMock) as mock_retrieve:
                mock_retrieve.return_value = [{"text": "result", "metadata": {}}]

                result = await self.tabular_index.general_query("test query", mock_callback)

                expected_results = [{"text": "result", "metadata": {}}]
                mock_callback.assert_called_once_with("test query", expected_results)
                self.assertEqual(result, expected_results)

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
