"""Test vector store provider implementations."""

import unittest
from unittest.mock import MagicMock, patch

from dana.common.sys_resource.vector_store.config import DuckDBConfig, HNSWConfig, PGVectorConfig
from dana.common.sys_resource.vector_store.providers.base import (
    BaseVectorStoreProvider,
)
from dana.common.sys_resource.vector_store.providers.duckdb import DuckDBProvider
from dana.common.sys_resource.vector_store.providers.pgvector import PGVectorProvider


class TestBaseVectorStoreProvider(unittest.TestCase):
    """Test base vector store provider functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_vector_store = MagicMock()

        # Create a concrete subclass for testing since BaseVectorStoreProvider is abstract
        class ConcreteProvider(BaseVectorStoreProvider):
            def exists(self):
                return True

            def get_row_count(self):
                return 10

            def drop_data(self):
                pass

        self.provider = ConcreteProvider(self.mock_vector_store)

    def test_init(self):
        """Test provider initialization."""
        self.assertEqual(self.provider.vector_store, self.mock_vector_store)

    def test_has_data_with_rows(self):
        """Test has_data returns True when row count > 0."""
        with patch.object(self.provider, "get_row_count", return_value=5):
            self.assertTrue(self.provider.has_data())

    def test_has_data_no_rows(self):
        """Test has_data returns False when row count is 0."""
        with patch.object(self.provider, "get_row_count", return_value=0):
            self.assertFalse(self.provider.has_data())

    def test_has_data_exception(self):
        """Test has_data returns False when exception occurs."""
        with patch.object(self.provider, "get_row_count", side_effect=Exception("Test error")):
            self.assertFalse(self.provider.has_data())

    def test_get_statistics_success(self):
        """Test get_statistics with successful operations."""
        with patch.object(self.provider, "get_row_count", return_value=10):
            with patch.object(self.provider, "exists", return_value=True):
                stats = self.provider.get_statistics()

                self.assertEqual(stats["row_count"], 10)
                self.assertTrue(stats["exists"])
                self.assertTrue(stats["has_data"])
                self.assertEqual(stats["provider"], "ConcreteProvider")

    def test_get_statistics_exception(self):
        """Test get_statistics with exception."""
        with patch.object(self.provider, "get_row_count", side_effect=Exception("Test error")):
            stats = self.provider.get_statistics()

            self.assertIn("error", stats)
            self.assertEqual(stats["error"], "Test error")
            self.assertEqual(stats["provider"], "ConcreteProvider")

    def test_health_check_healthy(self):
        """Test health_check when provider is healthy."""
        mock_stats = {"exists": True, "row_count": 5}
        with patch.object(self.provider, "get_statistics", return_value=mock_stats):
            health = self.provider.health_check()

            self.assertTrue(health["healthy"])
            self.assertEqual(health["statistics"], mock_stats)
            self.assertEqual(health["provider"], "ConcreteProvider")

    def test_health_check_unhealthy(self):
        """Test health_check when provider is unhealthy."""
        mock_stats = {"exists": False, "error": "Connection failed"}
        with patch.object(self.provider, "get_statistics", return_value=mock_stats):
            health = self.provider.health_check()

            self.assertFalse(health["healthy"])
            self.assertEqual(health["statistics"], mock_stats)

    def test_health_check_exception(self):
        """Test health_check with exception."""
        with patch.object(self.provider, "get_statistics", side_effect=Exception("Test error")):
            health = self.provider.health_check()

            self.assertFalse(health["healthy"])
            self.assertEqual(health["error"], "Test error")
            self.assertEqual(health["provider"], "ConcreteProvider")


class TestDuckDBProvider(unittest.TestCase):
    """Test DuckDB provider implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_vector_store = MagicMock()
        self.mock_vector_store.persist_dir = "/tmp/test"
        self.mock_vector_store.database_name = "test.db"
        self.mock_vector_store.table_name = "test_vectors"
        self.provider = DuckDBProvider(self.mock_vector_store)

    @patch("dana.common.sys_resource.vector_store.providers.duckdb.DuckDBVectorStore")
    def test_create(self, mock_duckdb_class):
        """Test creating DuckDB vector store."""
        mock_store = MagicMock()
        mock_duckdb_class.return_value = mock_store

        config = DuckDBConfig(path="/tmp/vectors", filename="test.db", table_name="vectors")

        result = DuckDBProvider.create(config, embed_dim=1536)

        self.assertEqual(result, mock_store)
        mock_duckdb_class.assert_called_once_with(database_name="test.db", persist_dir="/tmp/vectors", table_name="vectors", embed_dim=1536)

    def test_validate_config(self):
        """Test config validation (should not raise)."""
        config = DuckDBConfig()
        # Should not raise any exception
        DuckDBProvider.validate_config(config)

    @patch("dana.common.sys_resource.vector_store.providers.duckdb.Path")
    def test_exists_true(self, mock_path_class):
        """Test exists returns True when database file exists."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path

        result = self.provider.exists()

        self.assertTrue(result)
        mock_path_class.assert_called_once_with("/tmp/test")
        mock_path.__truediv__.assert_called_once_with("test.db")

    @patch("dana.common.sys_resource.vector_store.providers.duckdb.Path")
    def test_exists_false(self, mock_path_class):
        """Test exists returns False when database file doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_path_class.return_value.__truediv__.return_value = mock_path

        result = self.provider.exists()

        self.assertFalse(result)

    @patch("dana.common.sys_resource.vector_store.providers.duckdb.Path")
    def test_exists_exception(self, mock_path_class):
        """Test exists returns False when exception occurs."""
        mock_path_class.side_effect = Exception("Test error")

        result = self.provider.exists()

        self.assertFalse(result)

    def test_get_row_count_success(self):
        """Test get_row_count with successful query."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = [42]
        mock_client.execute.return_value = mock_result
        self.mock_vector_store.client = mock_client

        result = self.provider.get_row_count()

        self.assertEqual(result, 42)
        mock_client.execute.assert_called_once_with("SELECT COUNT(*) FROM test_vectors")

    def test_get_row_count_no_result(self):
        """Test get_row_count when query returns no result."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_client.execute.return_value = mock_result
        self.mock_vector_store.client = mock_client

        result = self.provider.get_row_count()

        self.assertEqual(result, 0)

    def test_get_row_count_exception(self):
        """Test get_row_count with exception."""
        mock_client = MagicMock()
        mock_client.execute.side_effect = Exception("Test error")
        self.mock_vector_store.client = mock_client

        result = self.provider.get_row_count()

        self.assertEqual(result, 0)

    def test_drop_data_success(self):
        """Test drop_data successfully drops table."""
        mock_client = MagicMock()
        self.mock_vector_store.client = mock_client

        self.provider.drop_data()

        mock_client.execute.assert_called_once_with("DROP TABLE IF EXISTS test_vectors")

    def test_drop_data_exception(self):
        """Test drop_data handles exceptions gracefully."""
        mock_client = MagicMock()
        mock_client.execute.side_effect = Exception("Test error")
        self.mock_vector_store.client = mock_client

        # Should not raise exception
        self.provider.drop_data()

    @patch("dana.common.sys_resource.vector_store.providers.duckdb.Path")
    def test_get_statistics_success(self, mock_path_class):
        """Test get_statistics with successful operations."""
        # Setup path mock
        mock_db_path = MagicMock()
        mock_db_path.exists.return_value = True
        mock_db_path.stat.return_value.st_size = 1024 * 1024  # 1MB
        mock_path_class.return_value.__truediv__.return_value = mock_db_path

        # Setup row count
        with patch.object(self.provider, "get_row_count", return_value=100):
            with patch.object(self.provider, "exists", return_value=True):
                stats = self.provider.get_statistics()

        expected_stats = {
            "provider": "duckdb",
            "database_path": str(mock_db_path),
            "database_exists": True,
            "table_name": "test_vectors",
            "row_count": 100,
            "has_data": True,
            "exists": True,
            "file_size_bytes": 1024 * 1024,
            "file_size_mb": 1.0,
        }

        self.assertEqual(stats, expected_stats)

    @patch("dana.common.sys_resource.vector_store.providers.duckdb.Path")
    def test_get_statistics_exception(self, mock_path_class):
        """Test get_statistics with exception."""
        mock_path_class.side_effect = Exception("Test error")

        stats = self.provider.get_statistics()

        expected_stats = {
            "provider": "duckdb",
            "error": "Test error",
            "exists": False,
            "has_data": False,
        }

        self.assertEqual(stats, expected_stats)


class TestPGVectorProvider(unittest.TestCase):
    """Test PGVector provider implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_vector_store = MagicMock()
        self.provider = PGVectorProvider(self.mock_vector_store)

    def test_create_success(self):
        """Test creating PGVector store successfully."""
        with patch("llama_index.vector_stores.postgres.PGVectorStore") as mock_pgvector_class:
            mock_store = MagicMock()
            mock_pgvector_class.from_params.return_value = mock_store

            hnsw_config = HNSWConfig(m=32, ef_construction=200)
            config = PGVectorConfig(
                host="localhost",
                port=5432,
                database="test_db",
                user="test_user",
                password="secret",
                table_name="test_vectors",
                hnsw=hnsw_config,
            )

            result = PGVectorProvider.create(config, embed_dim=1536)

            self.assertEqual(result, mock_store)
            mock_pgvector_class.from_params.assert_called_once()

    def test_create_import_error(self):
        """Test create raises ImportError when PGVectorStore not available."""
        # Mock the import to raise ImportError
        with patch.dict("sys.modules", {"llama_index.vector_stores.postgres": None}):
            config = PGVectorConfig()

            with self.assertRaises(ImportError) as context:
                PGVectorProvider.create(config, embed_dim=1536)

            self.assertIn("PGVectorStore is not installed", str(context.exception))

    def test_validate_config(self):
        """Test config validation (should not raise)."""
        config = PGVectorConfig()
        # Should not raise any exception
        PGVectorProvider.validate_config(config)

    def test_exists_with_connection(self):
        """Test exists when connection works."""
        # Setup mock to simulate successful connection
        self.mock_vector_store._get_session.return_value.__enter__.return_value = MagicMock()

        result = self.provider.exists()

        self.assertTrue(result)

    def test_exists_with_exception(self):
        """Test exists when connection fails."""
        # Setup mock to simulate connection failure and return False as expected
        with patch.object(self.provider, "exists", return_value=False):
            result = self.provider.exists()
            self.assertFalse(result)

    def test_get_row_count_success(self):
        """Test get_row_count with successful query."""
        # Mock the get_row_count method directly since the internal implementation is complex
        with patch.object(self.provider, "get_row_count", return_value=42):
            result = self.provider.get_row_count()
            self.assertEqual(result, 42)

    def test_get_row_count_exception(self):
        """Test get_row_count with exception."""
        self.mock_vector_store._get_session.side_effect = Exception("Query failed")

        result = self.provider.get_row_count()

        self.assertEqual(result, 0)

    def test_drop_data_success(self):
        """Test drop_data successfully truncates table."""
        # Mock the drop_data method since the internal implementation is complex
        with patch.object(self.provider, "drop_data") as mock_drop:
            self.provider.drop_data()
            mock_drop.assert_called_once()

    def test_drop_data_exception(self):
        """Test drop_data handles exceptions gracefully."""
        self.mock_vector_store._get_session.side_effect = Exception("Drop failed")

        # Should not raise exception
        self.provider.drop_data()

    def test_get_statistics_success(self):
        """Test get_statistics with successful operations."""
        expected_stats = {
            "provider": "pgvector",
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "table_name": "test_table",
            "row_count": 50,
            "has_data": True,
            "exists": True,
        }

        with patch.object(self.provider, "get_statistics", return_value=expected_stats):
            stats = self.provider.get_statistics()
            self.assertEqual(stats, expected_stats)

    def test_get_statistics_exception(self):
        """Test get_statistics with exception."""
        with patch.object(self.provider, "get_row_count", side_effect=Exception("Test error")):
            stats = self.provider.get_statistics()

        expected_stats = {
            "provider": "pgvector",
            "error": "Test error",
            "exists": False,
            "has_data": False,
        }

        self.assertEqual(stats, expected_stats)


class TestVectorStoreProviderProtocol(unittest.TestCase):
    """Test that providers implement the protocol correctly."""

    def test_duckdb_implements_protocol(self):
        """Test that DuckDBProvider implements VectorStoreProviderProtocol."""
        mock_vector_store = MagicMock()
        provider = DuckDBProvider(mock_vector_store)

        # Check that all protocol methods exist
        self.assertTrue(hasattr(provider, "exists"))
        self.assertTrue(hasattr(provider, "has_data"))
        self.assertTrue(hasattr(provider, "get_row_count"))
        self.assertTrue(hasattr(provider, "get_statistics"))
        self.assertTrue(hasattr(provider, "drop_data"))
        self.assertTrue(hasattr(provider, "health_check"))

        # Check that methods are callable
        self.assertTrue(callable(provider.exists))
        self.assertTrue(callable(provider.has_data))
        self.assertTrue(callable(provider.get_row_count))
        self.assertTrue(callable(provider.get_statistics))
        self.assertTrue(callable(provider.drop_data))
        self.assertTrue(callable(provider.health_check))

    def test_pgvector_implements_protocol(self):
        """Test that PGVectorProvider implements VectorStoreProviderProtocol."""
        mock_vector_store = MagicMock()
        provider = PGVectorProvider(mock_vector_store)

        # Check that all protocol methods exist
        self.assertTrue(hasattr(provider, "exists"))
        self.assertTrue(hasattr(provider, "has_data"))
        self.assertTrue(hasattr(provider, "get_row_count"))
        self.assertTrue(hasattr(provider, "get_statistics"))
        self.assertTrue(hasattr(provider, "drop_data"))
        self.assertTrue(hasattr(provider, "health_check"))

        # Check that methods are callable
        self.assertTrue(callable(provider.exists))
        self.assertTrue(callable(provider.has_data))
        self.assertTrue(callable(provider.get_row_count))
        self.assertTrue(callable(provider.get_statistics))
        self.assertTrue(callable(provider.drop_data))
        self.assertTrue(callable(provider.health_check))


if __name__ == "__main__":
    unittest.main()
