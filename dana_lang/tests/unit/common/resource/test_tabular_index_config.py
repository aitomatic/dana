"""Test tabular index configuration classes."""

import unittest
from unittest.mock import MagicMock

from dana.common.sys_resource.tabular_index.config import (
    BatchSearchConfig,
    EmbeddingConfig,
    TabularConfig,
)


class TestTabularConfig(unittest.TestCase):
    """Test TabularConfig class."""

    def test_default_values(self):
        """Test that default values are correctly set."""
        mock_constructor = MagicMock()
        config = TabularConfig(
            source="test.csv",
            embedding_field_constructor=mock_constructor,
        )

        self.assertEqual(config.source, "test.csv")
        self.assertEqual(config.embedding_field_constructor, mock_constructor)
        self.assertEqual(config.table_name, "my_tabular_index")
        self.assertIsNone(config.metadata_constructor)
        self.assertEqual(config.excluded_embed_metadata_keys, [])
        self.assertEqual(config.cache_dir, ".cache/tabular_index")
        self.assertFalse(config.force_reload)

    def test_custom_values(self):
        """Test custom values can be set."""
        mock_embedding_constructor = MagicMock()
        mock_metadata_constructor = MagicMock()

        config = TabularConfig(
            source="/tmp/test.parquet",
            embedding_field_constructor=mock_embedding_constructor,
            table_name="custom_table",
            metadata_constructor=mock_metadata_constructor,
            excluded_embed_metadata_keys=["id", "timestamp"],
            cache_dir="/tmp/cache",
            force_reload=True,
        )

        self.assertEqual(config.source, "/tmp/test.parquet")
        self.assertEqual(config.embedding_field_constructor, mock_embedding_constructor)
        self.assertEqual(config.table_name, "custom_table")
        self.assertEqual(config.metadata_constructor, mock_metadata_constructor)
        self.assertEqual(config.excluded_embed_metadata_keys, ["id", "timestamp"])
        self.assertEqual(config.cache_dir, "/tmp/cache")
        self.assertTrue(config.force_reload)

    def test_validation_empty_source(self):
        """Test validation for empty source."""
        mock_constructor = MagicMock()
        with self.assertRaises(ValueError) as context:
            TabularConfig(source="", embedding_field_constructor=mock_constructor)
        self.assertIn("Source file path cannot be empty", str(context.exception))

    def test_validation_invalid_file_extension(self):
        """Test validation for invalid file extensions."""
        mock_constructor = MagicMock()
        with self.assertRaises(ValueError) as context:
            TabularConfig(source="test.txt", embedding_field_constructor=mock_constructor)
        self.assertIn("Source file must be a CSV or Parquet file", str(context.exception))

    def test_validation_valid_csv_extension(self):
        """Test validation accepts CSV files."""
        mock_constructor = MagicMock()
        # Should not raise exception
        config = TabularConfig(source="test.csv", embedding_field_constructor=mock_constructor)
        self.assertEqual(config.source, "test.csv")

    def test_validation_valid_parquet_extension(self):
        """Test validation accepts Parquet files."""
        mock_constructor = MagicMock()
        # Should not raise exception
        config = TabularConfig(source="test.parquet", embedding_field_constructor=mock_constructor)
        self.assertEqual(config.source, "test.parquet")

    def test_validation_case_insensitive_extensions(self):
        """Test validation is case insensitive for file extensions."""
        mock_constructor = MagicMock()
        # Should not raise exception for uppercase extensions
        config1 = TabularConfig(source="test.CSV", embedding_field_constructor=mock_constructor)
        config2 = TabularConfig(source="test.PARQUET", embedding_field_constructor=mock_constructor)
        self.assertEqual(config1.source, "test.CSV")
        self.assertEqual(config2.source, "test.PARQUET")


class TestEmbeddingConfig(unittest.TestCase):
    """Test EmbeddingConfig class."""

    def test_default_values(self):
        """Test that default values are correctly set."""
        config = EmbeddingConfig(model_name="openai:text-embedding-3-small")

        self.assertEqual(config.model_name, "openai:text-embedding-3-small")
        self.assertIsNone(config.dimensions)

    def test_custom_values(self):
        """Test custom values can be set."""
        config = EmbeddingConfig(model_name="openai:text-embedding-3-large", dimensions=3072)

        self.assertEqual(config.model_name, "openai:text-embedding-3-large")
        self.assertEqual(config.dimensions, 3072)

    def test_validation_invalid_model_format(self):
        """Test validation for invalid model format."""
        with self.assertRaises(ValueError) as context:
            EmbeddingConfig(model_name="invalid-model-name")
        self.assertIn("Invalid model format", str(context.exception))
        self.assertIn("Expected 'provider:model_name'", str(context.exception))

    def test_validation_valid_model_format(self):
        """Test validation accepts valid model format."""
        # Should not raise exception
        config = EmbeddingConfig(model_name="huggingface:sentence-transformers/all-MiniLM-L6-v2")
        self.assertEqual(config.model_name, "huggingface:sentence-transformers/all-MiniLM-L6-v2")

    def test_validation_cohere_model_format(self):
        """Test validation accepts Cohere model format."""
        # Should not raise exception
        config = EmbeddingConfig(model_name="cohere:embed-english-v3.0")
        self.assertEqual(config.model_name, "cohere:embed-english-v3.0")


class TestBatchSearchConfig(unittest.TestCase):
    """Test BatchSearchConfig class."""

    def test_default_values(self):
        """Test that default values are correctly set."""
        config = BatchSearchConfig()

        self.assertEqual(config.batch_size, 20)
        self.assertEqual(config.pre_filter_top_k, 100)
        self.assertEqual(config.post_filter_top_k, 20)
        self.assertEqual(config.top_k, 10)

    def test_custom_values(self):
        """Test custom values can be set."""
        config = BatchSearchConfig(batch_size=50, pre_filter_top_k=200, post_filter_top_k=50, top_k=25)

        self.assertEqual(config.batch_size, 50)
        self.assertEqual(config.pre_filter_top_k, 200)
        self.assertEqual(config.post_filter_top_k, 50)
        self.assertEqual(config.top_k, 25)

    def test_partial_custom_values(self):
        """Test that only some values can be customized."""
        config = BatchSearchConfig(batch_size=100, top_k=5)

        self.assertEqual(config.batch_size, 100)
        self.assertEqual(config.pre_filter_top_k, 100)  # default
        self.assertEqual(config.post_filter_top_k, 20)  # default
        self.assertEqual(config.top_k, 5)


if __name__ == "__main__":
    unittest.main()
