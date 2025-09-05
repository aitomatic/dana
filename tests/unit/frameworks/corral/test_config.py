"""Tests for CORRAL configuration."""

import pytest

from dana.frameworks.corral.config import (
    CORRALConfig,
    SourceType,
    IndexingStrategy,
    ReasoningType,
    ExplanationDepth,
    ActionMode,
    DEFAULT_CONFIG,
    LIGHTWEIGHT_CONFIG,
    COMPREHENSIVE_CONFIG,
)


class TestCORRALConfig:
    """Test CORRAL configuration class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CORRALConfig()

        # Curation settings
        assert SourceType.INTERACTION in config.curation_sources
        assert SourceType.WORKFLOW in config.curation_sources
        assert SourceType.RESOURCE in config.curation_sources
        assert config.quality_threshold == 0.7
        assert config.auto_validation is True

        # Organization settings
        assert config.auto_categorization is True
        assert config.relationship_discovery is True
        assert config.indexing_strategy == IndexingStrategy.MULTI_DIMENSIONAL

        # Retrieval settings
        assert config.max_retrieval_results == 10
        assert config.min_confidence_threshold == 0.5
        assert config.context_window == 5

        # Reasoning settings
        assert ReasoningType.CAUSAL in config.reasoning_types
        assert ReasoningType.ANALOGICAL in config.reasoning_types
        assert config.explanation_depth == ExplanationDepth.STANDARD
        assert config.confidence_propagation is True

        # Action settings
        assert config.action_execution_mode == ActionMode.INTEGRATED
        assert config.fallback_strategies is True
        assert config.risk_assessment is True

        # Learning settings
        assert config.learning_rate == 0.1
        assert config.pattern_discovery is True
        assert config.knowledge_pruning is True
        assert config.meta_learning is True

        # Performance settings
        assert config.enable_caching is True
        assert config.parallel_processing is True
        assert config.max_memory_usage_mb == 1024

    def test_custom_config(self):
        """Test creating custom configuration."""
        config = CORRALConfig(
            quality_threshold=0.8,
            max_retrieval_results=20,
            learning_rate=0.2,
            reasoning_types=[ReasoningType.CAUSAL],
            explanation_depth=ExplanationDepth.COMPREHENSIVE,
        )

        assert config.quality_threshold == 0.8
        assert config.max_retrieval_results == 20
        assert config.learning_rate == 0.2
        assert len(config.reasoning_types) == 1
        assert ReasoningType.CAUSAL in config.reasoning_types
        assert config.explanation_depth == ExplanationDepth.COMPREHENSIVE

    def test_config_validation_valid(self):
        """Test validation with valid configuration."""
        config = CORRALConfig(
            quality_threshold=0.8, min_confidence_threshold=0.3, max_retrieval_results=15, learning_rate=0.15, context_window=3
        )

        # Should not raise exception
        config.validate()

    def test_config_validation_invalid_quality_threshold(self):
        """Test validation with invalid quality threshold."""
        config = CORRALConfig(quality_threshold=1.5)  # Invalid: > 1

        with pytest.raises(ValueError, match="quality_threshold must be between 0 and 1"):
            config.validate()

        config = CORRALConfig(quality_threshold=-0.1)  # Invalid: < 0

        with pytest.raises(ValueError, match="quality_threshold must be between 0 and 1"):
            config.validate()

    def test_config_validation_invalid_confidence_threshold(self):
        """Test validation with invalid confidence threshold."""
        config = CORRALConfig(min_confidence_threshold=1.5)  # Invalid: > 1

        with pytest.raises(ValueError, match="min_confidence_threshold must be between 0 and 1"):
            config.validate()

        config = CORRALConfig(min_confidence_threshold=-0.1)  # Invalid: < 0

        with pytest.raises(ValueError, match="min_confidence_threshold must be between 0 and 1"):
            config.validate()

    def test_config_validation_invalid_max_results(self):
        """Test validation with invalid max results."""
        config = CORRALConfig(max_retrieval_results=0)  # Invalid: <= 0

        with pytest.raises(ValueError, match="max_retrieval_results must be positive"):
            config.validate()

        config = CORRALConfig(max_retrieval_results=-5)  # Invalid: < 0

        with pytest.raises(ValueError, match="max_retrieval_results must be positive"):
            config.validate()

    def test_config_validation_invalid_learning_rate(self):
        """Test validation with invalid learning rate."""
        config = CORRALConfig(learning_rate=1.5)  # Invalid: > 1

        with pytest.raises(ValueError, match="learning_rate must be between 0 and 1"):
            config.validate()

        config = CORRALConfig(learning_rate=-0.1)  # Invalid: < 0

        with pytest.raises(ValueError, match="learning_rate must be between 0 and 1"):
            config.validate()

    def test_config_validation_invalid_context_window(self):
        """Test validation with invalid context window."""
        config = CORRALConfig(context_window=-1)  # Invalid: < 0

        with pytest.raises(ValueError, match="context_window must be non-negative"):
            config.validate()


class TestEnumTypes:
    """Test enum types used in configuration."""

    def test_source_type_enum(self):
        """Test SourceType enum values."""
        assert SourceType.INTERACTION.value == "interaction"
        assert SourceType.WORKFLOW.value == "workflow"
        assert SourceType.RESOURCE.value == "resource"
        assert SourceType.EXTERNAL.value == "external"
        assert SourceType.USER_FEEDBACK.value == "user_feedback"

    def test_indexing_strategy_enum(self):
        """Test IndexingStrategy enum values."""
        assert IndexingStrategy.SIMPLE.value == "simple"
        assert IndexingStrategy.MULTI_DIMENSIONAL.value == "multi_dimensional"
        assert IndexingStrategy.SEMANTIC.value == "semantic"
        assert IndexingStrategy.HYBRID.value == "hybrid"

    def test_reasoning_type_enum(self):
        """Test ReasoningType enum values."""
        assert ReasoningType.CAUSAL.value == "causal"
        assert ReasoningType.ANALOGICAL.value == "analogical"
        assert ReasoningType.DEDUCTIVE.value == "deductive"
        assert ReasoningType.ABDUCTIVE.value == "abductive"
        assert ReasoningType.TEMPORAL.value == "temporal"

    def test_explanation_depth_enum(self):
        """Test ExplanationDepth enum values."""
        assert ExplanationDepth.MINIMAL.value == "minimal"
        assert ExplanationDepth.STANDARD.value == "standard"
        assert ExplanationDepth.COMPREHENSIVE.value == "comprehensive"

    def test_action_mode_enum(self):
        """Test ActionMode enum values."""
        assert ActionMode.INTEGRATED.value == "integrated"
        assert ActionMode.STANDALONE.value == "standalone"


class TestPresetConfigs:
    """Test preset configuration instances."""

    def test_default_config_instance(self):
        """Test DEFAULT_CONFIG preset."""
        assert isinstance(DEFAULT_CONFIG, CORRALConfig)
        assert DEFAULT_CONFIG.max_retrieval_results == 10
        assert DEFAULT_CONFIG.learning_rate == 0.1
        assert DEFAULT_CONFIG.explanation_depth == ExplanationDepth.STANDARD

        # Should be valid
        DEFAULT_CONFIG.validate()

    def test_lightweight_config_instance(self):
        """Test LIGHTWEIGHT_CONFIG preset."""
        assert isinstance(LIGHTWEIGHT_CONFIG, CORRALConfig)
        assert LIGHTWEIGHT_CONFIG.max_retrieval_results == 5
        assert LIGHTWEIGHT_CONFIG.pattern_discovery is False
        assert LIGHTWEIGHT_CONFIG.knowledge_pruning is False
        assert LIGHTWEIGHT_CONFIG.parallel_processing is False
        assert LIGHTWEIGHT_CONFIG.max_memory_usage_mb == 256
        assert LIGHTWEIGHT_CONFIG.explanation_depth == ExplanationDepth.MINIMAL
        assert len(LIGHTWEIGHT_CONFIG.reasoning_types) == 1
        assert ReasoningType.CAUSAL in LIGHTWEIGHT_CONFIG.reasoning_types

        # Should be valid
        LIGHTWEIGHT_CONFIG.validate()

    def test_comprehensive_config_instance(self):
        """Test COMPREHENSIVE_CONFIG preset."""
        assert isinstance(COMPREHENSIVE_CONFIG, CORRALConfig)
        assert COMPREHENSIVE_CONFIG.max_retrieval_results == 20
        assert COMPREHENSIVE_CONFIG.context_window == 10
        assert COMPREHENSIVE_CONFIG.learning_rate == 0.2
        assert COMPREHENSIVE_CONFIG.max_memory_usage_mb == 2048
        assert COMPREHENSIVE_CONFIG.explanation_depth == ExplanationDepth.COMPREHENSIVE

        # Should have all reasoning types
        expected_types = [ReasoningType.CAUSAL, ReasoningType.ANALOGICAL, ReasoningType.DEDUCTIVE, ReasoningType.ABDUCTIVE]
        for reasoning_type in expected_types:
            assert reasoning_type in COMPREHENSIVE_CONFIG.reasoning_types

        # Should be valid
        COMPREHENSIVE_CONFIG.validate()

    def test_preset_configs_differences(self):
        """Test that preset configs have expected differences."""
        # Lightweight should be more restrictive than default
        assert LIGHTWEIGHT_CONFIG.max_retrieval_results < DEFAULT_CONFIG.max_retrieval_results
        assert LIGHTWEIGHT_CONFIG.max_memory_usage_mb < DEFAULT_CONFIG.max_memory_usage_mb
        assert len(LIGHTWEIGHT_CONFIG.reasoning_types) < len(DEFAULT_CONFIG.reasoning_types)

        # Comprehensive should be more permissive than default
        assert COMPREHENSIVE_CONFIG.max_retrieval_results > DEFAULT_CONFIG.max_retrieval_results
        assert COMPREHENSIVE_CONFIG.max_memory_usage_mb > DEFAULT_CONFIG.max_memory_usage_mb
        assert len(COMPREHENSIVE_CONFIG.reasoning_types) > len(DEFAULT_CONFIG.reasoning_types)
