"""Test vector store factory functionality."""

import unittest
from unittest.mock import MagicMock, patch

from dana.common.sys_resource.vector_store.config import (
    VectorStoreConfig,
    create_duckdb_config,
    create_pgvector_config,
)
from dana.common.sys_resource.vector_store.factory import VectorStoreFactory


class TestVectorStoreFactory(unittest.TestCase):
    """Test vector store factory."""

    def test_get_supported_providers(self):
        """Test getting supported providers."""
        providers = VectorStoreFactory.get_supported_providers()

        self.assertIsInstance(providers, list)
        self.assertIn("duckdb", providers)
        self.assertIn("pgvector", providers)

    def test_validate_provider_supported(self):
        """Test validating supported providers."""
        self.assertTrue(VectorStoreFactory.validate_provider("duckdb"))
        self.assertTrue(VectorStoreFactory.validate_provider("pgvector"))

    def test_validate_provider_unsupported(self):
        """Test validating unsupported providers."""
        self.assertFalse(VectorStoreFactory.validate_provider("unsupported"))
        self.assertFalse(VectorStoreFactory.validate_provider(""))

    @patch("dana.common.sys_resource.vector_store.factory.DuckDBProvider")
    def test_create_duckdb(self, mock_provider):
        """Test creating DuckDB vector store."""
        # Setup mocks
        mock_vector_store = MagicMock()
        mock_provider.create.return_value = mock_vector_store
        mock_provider.validate_config.return_value = None

        # Create config and test
        config = create_duckdb_config(path="/tmp", filename="test.db")
        result = VectorStoreFactory.create(config, embed_dim=1536)

        # Verify
        self.assertEqual(result, mock_vector_store)
        mock_provider.validate_config.assert_called_once_with(config.duckdb)
        mock_provider.create.assert_called_once_with(config.duckdb, 1536)

    @patch("dana.common.sys_resource.vector_store.factory.PGVectorProvider")
    def test_create_pgvector(self, mock_provider):
        """Test creating PGVector vector store."""
        # Setup mocks
        mock_vector_store = MagicMock()
        mock_provider.create.return_value = mock_vector_store
        mock_provider.validate_config.return_value = None

        # Create config and test
        config = create_pgvector_config(host="test.db", port=5433)
        result = VectorStoreFactory.create(config, embed_dim=1536)

        # Verify
        self.assertEqual(result, mock_vector_store)
        mock_provider.validate_config.assert_called_once_with(config.pgvector)
        mock_provider.create.assert_called_once_with(config.pgvector, 1536)

    def test_create_unsupported_provider(self):
        """Test creating vector store with unsupported provider."""
        # Create config with unsupported provider - this should already fail in config validation
        with self.assertRaises(ValueError) as context:
            VectorStoreConfig(provider="unsupported")
        self.assertIn("Unsupported vector store provider", str(context.exception))

    @patch("dana.common.sys_resource.vector_store.factory.DuckDBProvider")
    def test_create_with_provider_duckdb(self, mock_provider_class):
        """Test creating DuckDB provider wrapper."""
        # Setup mocks
        mock_vector_store = MagicMock()
        mock_provider_instance = MagicMock()
        mock_provider_class.create.return_value = mock_vector_store
        mock_provider_class.return_value = mock_provider_instance
        mock_provider_class.validate_config.return_value = None

        # Create config and test
        config = create_duckdb_config()
        result = VectorStoreFactory.create_with_provider(config, embed_dim=1536)

        # Verify
        self.assertEqual(result, mock_provider_instance)
        mock_provider_class.validate_config.assert_called_once_with(config.duckdb)
        mock_provider_class.create.assert_called_once_with(config.duckdb, 1536)
        mock_provider_class.assert_called_once_with(mock_vector_store)

    @patch("dana.common.sys_resource.vector_store.factory.PGVectorProvider")
    def test_create_with_provider_pgvector(self, mock_provider_class):
        """Test creating PGVector provider wrapper."""
        # Setup mocks
        mock_vector_store = MagicMock()
        mock_provider_instance = MagicMock()
        mock_provider_class.create.return_value = mock_vector_store
        mock_provider_class.return_value = mock_provider_instance
        mock_provider_class.validate_config.return_value = None

        # Create config and test
        config = create_pgvector_config()
        result = VectorStoreFactory.create_with_provider(config, embed_dim=1536)

        # Verify
        self.assertEqual(result, mock_provider_instance)
        mock_provider_class.validate_config.assert_called_once_with(config.pgvector)
        mock_provider_class.create.assert_called_once_with(config.pgvector, 1536)
        mock_provider_class.assert_called_once_with(mock_vector_store)

    @patch("dana.common.sys_resource.vector_store.factory.VectorStoreFactory.create")
    def test_create_from_dict_duckdb(self, mock_create):
        """Test creating DuckDB vector store from dict."""
        mock_vector_store = MagicMock()
        mock_create.return_value = mock_vector_store

        result = VectorStoreFactory.create_from_dict(
            "duckdb", embed_dim=1536, path="/tmp/vectors", filename="test.db", table_name="test_table"
        )

        self.assertEqual(result, mock_vector_store)
        mock_create.assert_called_once()

        # Verify config was created correctly
        call_args = mock_create.call_args
        config = call_args[0][0]  # First positional argument
        embed_dim = call_args[0][1]  # Second positional argument

        self.assertEqual(embed_dim, 1536)
        self.assertEqual(config.provider, "duckdb")
        self.assertEqual(config.duckdb.path, "/tmp/vectors")
        self.assertEqual(config.duckdb.filename, "test.db")
        self.assertEqual(config.duckdb.table_name, "test_table")

    @patch("dana.common.sys_resource.vector_store.factory.VectorStoreFactory.create")
    def test_create_from_dict_pgvector(self, mock_create):
        """Test creating PGVector vector store from dict."""
        mock_vector_store = MagicMock()
        mock_create.return_value = mock_vector_store

        result = VectorStoreFactory.create_from_dict(
            "pgvector", embed_dim=1536, host="test.db", port=5433, database="test_db", hnsw_config={"m": 32, "ef_construction": 200}
        )

        self.assertEqual(result, mock_vector_store)
        mock_create.assert_called_once()

        # Verify config was created correctly
        call_args = mock_create.call_args
        config = call_args[0][0]  # First positional argument
        embed_dim = call_args[0][1]  # Second positional argument

        self.assertEqual(embed_dim, 1536)
        self.assertEqual(config.provider, "pgvector")
        self.assertEqual(config.pgvector.host, "test.db")
        self.assertEqual(config.pgvector.port, 5433)
        self.assertEqual(config.pgvector.database, "test_db")
        self.assertEqual(config.pgvector.hnsw.m, 32)
        self.assertEqual(config.pgvector.hnsw.ef_construction, 200)

    def test_create_from_dict_unsupported_provider(self):
        """Test creating vector store from dict with unsupported provider."""
        with self.assertRaises(ValueError) as context:
            VectorStoreFactory.create_from_dict("unsupported", embed_dim=1536)
        self.assertIn("Unsupported vector store provider", str(context.exception))

    @patch("dana.common.sys_resource.vector_store.factory.DuckDBProvider.validate_config")
    def test_create_with_validation_error(self, mock_validate):
        """Test factory handles validation errors properly."""
        # Setup mock to raise validation error
        mock_validate.side_effect = ValueError("Invalid configuration")

        config = create_duckdb_config()

        with self.assertRaises(ValueError) as context:
            VectorStoreFactory.create(config, embed_dim=1536)
        self.assertIn("Invalid configuration", str(context.exception))


if __name__ == "__main__":
    unittest.main()
