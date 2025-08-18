"""Integration tests for vector store module."""

import unittest
from unittest.mock import MagicMock, patch

from dana.common.sys_resource.vector_store import (
    DuckDBConfig,
    PGVectorConfig,
    VectorStoreConfig,
    VectorStoreFactory,
    create_duckdb_config,
    create_pgvector_config,
)


class TestVectorStoreIntegration(unittest.TestCase):
    """Integration tests for the complete vector store module."""

    def test_module_imports(self):
        """Test that all expected classes and functions are importable."""
        # Test that imports work without errors
        from dana.common.sys_resource.vector_store import (
            DuckDBConfig,
            HNSWConfig,
            PGVectorConfig,
            VectorStoreConfig,
            VectorStoreFactory,
        )

        # Basic smoke test - check that classes exist
        self.assertTrue(callable(VectorStoreConfig))
        self.assertTrue(callable(DuckDBConfig))
        self.assertTrue(callable(PGVectorConfig))
        self.assertTrue(callable(HNSWConfig))
        self.assertTrue(callable(VectorStoreFactory))

    @patch("dana.common.sys_resource.vector_store.factory.DuckDBProvider")
    def test_end_to_end_duckdb_workflow(self, mock_provider_class):
        """Test complete workflow for DuckDB vector store creation."""
        # Setup mocks
        mock_vector_store = MagicMock()
        mock_provider_instance = MagicMock()
        mock_provider_class.create.return_value = mock_vector_store
        mock_provider_class.return_value = mock_provider_instance
        mock_provider_class.validate_config.return_value = None

        # Mock provider methods
        mock_provider_instance.exists.return_value = True
        mock_provider_instance.has_data.return_value = False
        mock_provider_instance.get_row_count.return_value = 0
        mock_provider_instance.get_statistics.return_value = {"provider": "duckdb", "row_count": 0, "exists": True, "has_data": False}

        # 1. Create configuration
        config = create_duckdb_config(path="/tmp/test_vectors", filename="test.db", table_name="test_table")

        # Verify config structure
        self.assertEqual(config.provider, "duckdb")
        self.assertEqual(config.duckdb.path, "/tmp/test_vectors")
        self.assertEqual(config.duckdb.filename, "test.db")
        self.assertEqual(config.duckdb.table_name, "test_table")

        # 2. Create vector store using factory
        vector_store = VectorStoreFactory.create(config, embed_dim=1536)
        self.assertEqual(vector_store, mock_vector_store)

        # 3. Create provider for lifecycle management
        provider = VectorStoreFactory.create_with_provider(config, embed_dim=1536)
        self.assertEqual(provider, mock_provider_instance)

        # 4. Test provider lifecycle operations
        self.assertTrue(provider.exists())
        self.assertFalse(provider.has_data())
        self.assertEqual(provider.get_row_count(), 0)

        stats = provider.get_statistics()
        self.assertEqual(stats["provider"], "duckdb")
        self.assertEqual(stats["row_count"], 0)

        # Verify all expected calls were made
        self.assertEqual(mock_provider_class.validate_config.call_count, 2)
        self.assertEqual(mock_provider_class.create.call_count, 2)
        mock_provider_instance.exists.assert_called()
        mock_provider_instance.has_data.assert_called()
        mock_provider_instance.get_row_count.assert_called()
        mock_provider_instance.get_statistics.assert_called()

    @patch("dana.common.sys_resource.vector_store.factory.PGVectorProvider")
    def test_end_to_end_pgvector_workflow(self, mock_provider_class):
        """Test complete workflow for PGVector vector store creation."""
        # Setup mocks
        mock_vector_store = MagicMock()
        mock_provider_instance = MagicMock()
        mock_provider_class.create.return_value = mock_vector_store
        mock_provider_class.return_value = mock_provider_instance
        mock_provider_class.validate_config.return_value = None

        # Mock provider methods
        mock_provider_instance.exists.return_value = True
        mock_provider_instance.has_data.return_value = True
        mock_provider_instance.get_row_count.return_value = 100
        mock_provider_instance.get_statistics.return_value = {"provider": "pgvector", "row_count": 100, "exists": True, "has_data": True}

        # 1. Create configuration with HNSW parameters
        config = create_pgvector_config(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="secret",
            hnsw_config={"m": 32, "ef_construction": 200},
        )

        # Verify config structure
        self.assertEqual(config.provider, "pgvector")
        self.assertEqual(config.pgvector.host, "localhost")
        self.assertEqual(config.pgvector.port, 5432)
        self.assertEqual(config.pgvector.database, "test_db")
        self.assertEqual(config.pgvector.user, "test_user")
        self.assertEqual(config.pgvector.password, "secret")
        self.assertEqual(config.pgvector.hnsw.m, 32)
        self.assertEqual(config.pgvector.hnsw.ef_construction, 200)

        # 2. Create vector store using factory
        vector_store = VectorStoreFactory.create(config, embed_dim=1536)
        self.assertEqual(vector_store, mock_vector_store)

        # 3. Create provider for lifecycle management
        provider = VectorStoreFactory.create_with_provider(config, embed_dim=1536)
        self.assertEqual(provider, mock_provider_instance)

        # 4. Test provider lifecycle operations
        self.assertTrue(provider.exists())
        self.assertTrue(provider.has_data())
        self.assertEqual(provider.get_row_count(), 100)

        stats = provider.get_statistics()
        self.assertEqual(stats["provider"], "pgvector")
        self.assertEqual(stats["row_count"], 100)

        # Verify all expected calls were made
        self.assertEqual(mock_provider_class.validate_config.call_count, 2)
        self.assertEqual(mock_provider_class.create.call_count, 2)

    def test_factory_create_from_dict_workflow(self):
        """Test using factory create_from_dict method."""
        with patch("dana.common.sys_resource.vector_store.factory.VectorStoreFactory.create") as mock_create:
            mock_vector_store = MagicMock()
            mock_create.return_value = mock_vector_store

            # Test DuckDB creation from dict
            result = VectorStoreFactory.create_from_dict("duckdb", embed_dim=1536, path="/tmp/vectors", filename="test.db")

            self.assertEqual(result, mock_vector_store)
            mock_create.assert_called_once()

            # Verify the config passed to create
            call_args = mock_create.call_args
            config = call_args[0][0]
            embed_dim = call_args[0][1]

            self.assertEqual(embed_dim, 1536)
            self.assertEqual(config.provider, "duckdb")
            self.assertEqual(config.duckdb.path, "/tmp/vectors")
            self.assertEqual(config.duckdb.filename, "test.db")

    def test_configuration_validation_workflow(self):
        """Test configuration validation across the system."""
        # Test valid configurations don't raise errors
        _ = create_duckdb_config(path="/tmp", filename="test.db")
        _ = create_pgvector_config(host="localhost", database="test_db")

        # Test factory validation
        self.assertTrue(VectorStoreFactory.validate_provider("duckdb"))
        self.assertTrue(VectorStoreFactory.validate_provider("pgvector"))
        self.assertFalse(VectorStoreFactory.validate_provider("invalid"))

        # Test provider lists
        providers = VectorStoreFactory.get_supported_providers()
        self.assertIn("duckdb", providers)
        self.assertIn("pgvector", providers)

    def test_error_handling_workflow(self):
        """Test error handling across the module."""
        # Test invalid provider in config
        with self.assertRaises(ValueError):
            VectorStoreConfig(provider="invalid")

        # Test invalid factory provider
        with self.assertRaises(ValueError):
            VectorStoreFactory.create_from_dict("invalid", embed_dim=1536)

        # Test invalid DuckDB config
        with self.assertRaises(ValueError):
            DuckDBConfig(path="")  # Empty path should fail

        # Test invalid PGVector config
        with self.assertRaises(ValueError):
            PGVectorConfig(port=0)  # Invalid port should fail

    @patch("dana.common.sys_resource.vector_store.factory.DuckDBProvider")
    def test_provider_lifecycle_operations(self, mock_provider_class):
        """Test provider lifecycle operations integration."""
        # Setup provider mock
        mock_vector_store = MagicMock()
        mock_provider_instance = MagicMock()
        mock_provider_class.create.return_value = mock_vector_store
        mock_provider_class.return_value = mock_provider_instance
        mock_provider_class.validate_config.return_value = None

        # Setup method returns
        mock_provider_instance.exists.return_value = True
        mock_provider_instance.has_data.return_value = True
        mock_provider_instance.get_row_count.return_value = 50
        mock_provider_instance.get_statistics.return_value = {"provider": "duckdb", "row_count": 50, "exists": True, "has_data": True}
        mock_provider_instance.health_check.return_value = {"healthy": True, "statistics": {"row_count": 50}}

        config = create_duckdb_config()
        provider = VectorStoreFactory.create_with_provider(config, embed_dim=1536)

        # Test all lifecycle operations
        self.assertTrue(provider.exists())
        self.assertTrue(provider.has_data())
        self.assertEqual(provider.get_row_count(), 50)

        stats = provider.get_statistics()
        self.assertEqual(stats["row_count"], 50)

        health = provider.health_check()
        self.assertTrue(health["healthy"])

        # Test drop data operation
        provider.drop_data()
        mock_provider_instance.drop_data.assert_called_once()


if __name__ == "__main__":
    unittest.main()
