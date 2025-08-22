"""Test vector store configuration classes."""

import unittest

from dana.common.sys_resource.vector_store.config import (
    DuckDBConfig,
    HNSWConfig,
    PGVectorConfig,
    VectorStoreConfig,
    create_duckdb_config,
    create_pgvector_config,
)


class TestHNSWConfig(unittest.TestCase):
    """Test HNSW configuration class."""

    def test_default_values(self):
        """Test that default values are correctly set."""
        config = HNSWConfig()

        self.assertEqual(config.m, 64)
        self.assertEqual(config.ef_construction, 400)
        self.assertEqual(config.ef_search, 400)
        self.assertEqual(config.dist_method, "vector_cosine_ops")

    def test_custom_values(self):
        """Test custom values can be set."""
        config = HNSWConfig(m=32, ef_construction=200, ef_search=100, dist_method="vector_l2_ops")

        self.assertEqual(config.m, 32)
        self.assertEqual(config.ef_construction, 200)
        self.assertEqual(config.ef_search, 100)
        self.assertEqual(config.dist_method, "vector_l2_ops")

    def test_to_kwargs(self):
        """Test conversion to kwargs format."""
        config = HNSWConfig(m=32, ef_construction=200)
        kwargs = config.to_kwargs()

        expected = {
            "hnsw_m": 32,
            "hnsw_ef_construction": 200,
            "hnsw_ef_search": 400,  # default
            "hnsw_dist_method": "vector_cosine_ops",  # default
        }
        self.assertEqual(kwargs, expected)


class TestDuckDBConfig(unittest.TestCase):
    """Test DuckDB configuration class."""

    def test_default_values(self):
        """Test that default values are correctly set."""
        config = DuckDBConfig()

        self.assertEqual(config.path, ".cache/vector_db")
        self.assertEqual(config.filename, "vector_store.db")
        self.assertEqual(config.table_name, "vectors")

    def test_custom_values(self):
        """Test custom values can be set."""
        config = DuckDBConfig(path="/tmp/test_vectors", filename="test.db", table_name="test_table")

        self.assertEqual(config.path, "/tmp/test_vectors")
        self.assertEqual(config.filename, "test.db")
        self.assertEqual(config.table_name, "test_table")

    def test_validation_empty_path(self):
        """Test validation for empty path."""
        with self.assertRaises(ValueError) as context:
            DuckDBConfig(path="")
        self.assertIn("path cannot be empty", str(context.exception))

    def test_validation_empty_filename(self):
        """Test validation for empty filename."""
        with self.assertRaises(ValueError) as context:
            DuckDBConfig(filename="")
        self.assertIn("filename cannot be empty", str(context.exception))

    def test_validation_empty_table_name(self):
        """Test validation for empty table name."""
        with self.assertRaises(ValueError) as context:
            DuckDBConfig(table_name="")
        self.assertIn("table_name cannot be empty", str(context.exception))


class TestPGVectorConfig(unittest.TestCase):
    """Test PGVector configuration class."""

    def test_default_values(self):
        """Test that default values are correctly set."""
        config = PGVectorConfig()

        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.database, "vector_db")
        self.assertEqual(config.user, "postgres")
        self.assertEqual(config.password, "")
        self.assertEqual(config.schema_name, "public")
        self.assertEqual(config.table_name, "vectors")
        self.assertEqual(config.use_halfvec, False)
        self.assertEqual(config.hybrid_search, False)
        self.assertIsInstance(config.hnsw, HNSWConfig)

    def test_custom_values(self):
        """Test custom values can be set."""
        hnsw_config = HNSWConfig(m=32)
        config = PGVectorConfig(
            host="db.example.com",
            port=5433,
            database="test_db",
            user="test_user",
            password="secret",
            schema_name="test_schema",
            table_name="test_vectors",
            use_halfvec=True,
            hybrid_search=True,
            hnsw=hnsw_config,
        )

        self.assertEqual(config.host, "db.example.com")
        self.assertEqual(config.port, 5433)
        self.assertEqual(config.database, "test_db")
        self.assertEqual(config.user, "test_user")
        self.assertEqual(config.password, "secret")
        self.assertEqual(config.schema_name, "test_schema")
        self.assertEqual(config.table_name, "test_vectors")
        self.assertEqual(config.use_halfvec, True)
        self.assertEqual(config.hybrid_search, True)
        self.assertEqual(config.hnsw.m, 32)

    def test_validation_empty_host(self):
        """Test validation for empty host."""
        with self.assertRaises(ValueError) as context:
            PGVectorConfig(host="")
        self.assertIn("host cannot be empty", str(context.exception))

    def test_validation_invalid_port(self):
        """Test validation for invalid port."""
        with self.assertRaises(ValueError) as context:
            PGVectorConfig(port=0)
        self.assertIn("port must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            PGVectorConfig(port=-1)
        self.assertIn("port must be a positive integer", str(context.exception))

    def test_validation_empty_database(self):
        """Test validation for empty database."""
        with self.assertRaises(ValueError) as context:
            PGVectorConfig(database="")
        self.assertIn("database cannot be empty", str(context.exception))

    def test_validation_empty_user(self):
        """Test validation for empty user."""
        with self.assertRaises(ValueError) as context:
            PGVectorConfig(user="")
        self.assertIn("user cannot be empty", str(context.exception))


class TestVectorStoreConfig(unittest.TestCase):
    """Test main vector store configuration class."""

    def test_duckdb_provider(self):
        """Test DuckDB provider configuration."""
        config = VectorStoreConfig(provider="duckdb")

        self.assertEqual(config.provider, "duckdb")
        self.assertIsInstance(config.duckdb, DuckDBConfig)
        self.assertIsInstance(config.pgvector, PGVectorConfig)

    def test_pgvector_provider(self):
        """Test PGVector provider configuration."""
        config = VectorStoreConfig(provider="pgvector")

        self.assertEqual(config.provider, "pgvector")
        self.assertIsInstance(config.duckdb, DuckDBConfig)
        self.assertIsInstance(config.pgvector, PGVectorConfig)

    def test_custom_provider_configs(self):
        """Test custom provider configurations."""
        duckdb_config = DuckDBConfig(path="/tmp", filename="test.db")
        pgvector_config = PGVectorConfig(host="test.db", port=5433)

        config = VectorStoreConfig(provider="duckdb", duckdb=duckdb_config, pgvector=pgvector_config)

        self.assertEqual(config.duckdb.path, "/tmp")
        self.assertEqual(config.duckdb.filename, "test.db")
        self.assertEqual(config.pgvector.host, "test.db")
        self.assertEqual(config.pgvector.port, 5433)

    def test_unsupported_provider(self):
        """Test unsupported provider raises error."""
        with self.assertRaises(ValueError) as context:
            VectorStoreConfig(provider="unsupported")
        self.assertIn("Unsupported vector store provider", str(context.exception))

    def test_get_provider_config_duckdb(self):
        """Test get_provider_config for DuckDB."""
        config = VectorStoreConfig(provider="duckdb")
        provider_config = config.get_provider_config()

        self.assertIsInstance(provider_config, DuckDBConfig)

    def test_get_provider_config_pgvector(self):
        """Test get_provider_config for PGVector."""
        config = VectorStoreConfig(provider="pgvector")
        provider_config = config.get_provider_config()

        self.assertIsInstance(provider_config, PGVectorConfig)


class TestConfigHelpers(unittest.TestCase):
    """Test configuration helper functions."""

    def test_create_duckdb_config_default(self):
        """Test creating DuckDB config with defaults."""
        config = create_duckdb_config()

        self.assertEqual(config.provider, "duckdb")
        self.assertEqual(config.duckdb.path, ".cache/vector_db")
        self.assertEqual(config.duckdb.filename, "vector_store.db")
        self.assertEqual(config.duckdb.table_name, "vectors")

    def test_create_duckdb_config_custom(self):
        """Test creating DuckDB config with custom values."""
        config = create_duckdb_config(path="/tmp/vectors", filename="custom.db", table_name="custom_table")

        self.assertEqual(config.provider, "duckdb")
        self.assertEqual(config.duckdb.path, "/tmp/vectors")
        self.assertEqual(config.duckdb.filename, "custom.db")
        self.assertEqual(config.duckdb.table_name, "custom_table")

    def test_create_pgvector_config_default(self):
        """Test creating PGVector config with defaults."""
        config = create_pgvector_config()

        self.assertEqual(config.provider, "pgvector")
        self.assertEqual(config.pgvector.host, "localhost")
        self.assertEqual(config.pgvector.port, 5432)
        self.assertEqual(config.pgvector.database, "vector_db")

    def test_create_pgvector_config_custom(self):
        """Test creating PGVector config with custom values."""
        config = create_pgvector_config(
            host="db.example.com",
            port=5433,
            database="test_db",
            user="test_user",
            password="secret",
            schema_name="test_schema",
            table_name="test_vectors",
            use_halfvec=True,
            hybrid_search=True,
        )

        self.assertEqual(config.provider, "pgvector")
        self.assertEqual(config.pgvector.host, "db.example.com")
        self.assertEqual(config.pgvector.port, 5433)
        self.assertEqual(config.pgvector.database, "test_db")
        self.assertEqual(config.pgvector.user, "test_user")
        self.assertEqual(config.pgvector.password, "secret")
        self.assertEqual(config.pgvector.schema_name, "test_schema")
        self.assertEqual(config.pgvector.table_name, "test_vectors")
        self.assertEqual(config.pgvector.use_halfvec, True)
        self.assertEqual(config.pgvector.hybrid_search, True)

    def test_create_pgvector_config_with_hnsw(self):
        """Test creating PGVector config with HNSW configuration."""
        hnsw_config = {"m": 32, "ef_construction": 200}
        config = create_pgvector_config(hnsw_config=hnsw_config)

        self.assertEqual(config.provider, "pgvector")
        self.assertEqual(config.pgvector.hnsw.m, 32)
        self.assertEqual(config.pgvector.hnsw.ef_construction, 200)
        self.assertEqual(config.pgvector.hnsw.ef_search, 400)  # default


if __name__ == "__main__":
    unittest.main()
