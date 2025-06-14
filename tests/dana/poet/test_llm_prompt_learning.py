"""
Tests for Enhanced LLM Optimization Plugin with Prompt Learning

This module tests the prompt learning capabilities including:
- LLM-powered prompt analysis and optimization
- Execution feedback integration
- Performance tracking and recommendations
- Plugin learning interface
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from opendxa.dana.poet.plugins.enhanced_llm_optimization_plugin import EnhancedLLMOptimizationPlugin, PromptAnalysis, PromptLearner
from opendxa.dana.poet.poet import POETConfig, POETExecutor


class TestPromptLearner:
    """Test the prompt learning system."""

    def test_prompt_learner_initialization(self):
        """Test prompt learner initializes correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            learner = PromptLearner(storage_path=temp_dir)

            assert learner.storage_path == Path(temp_dir)
            assert learner.min_executions_for_learning == 5
            assert learner.execution_count == 0
            assert len(learner.prompt_history) == 0

    def test_prompt_analysis_simulation(self):
        """Test simulated LLM prompt analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            learner = PromptLearner(storage_path=temp_dir)

            # Test short prompt analysis
            short_prompt = "Analyze this"
            analysis = learner.analyze_prompt(short_prompt, "financial_services", "test_function")

            assert isinstance(analysis, PromptAnalysis)
            assert 0 <= analysis.clarity_score <= 1
            assert 0 <= analysis.completeness_score <= 1
            assert 0 <= analysis.specificity_score <= 1
            assert len(analysis.improvements) > 0
            assert "context" in analysis.improvements[0].lower()
            assert len(analysis.optimized_prompt) > len(short_prompt)

    def test_execution_feedback_recording(self):
        """Test execution feedback recording and storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            learner = PromptLearner(storage_path=temp_dir)

            function_name = "test_function"
            prompt = "Analyze financial risk"

            # Record multiple executions
            for i in range(5):
                learner.record_execution_feedback(
                    function_name=function_name,
                    prompt=prompt,
                    performance_score=0.7 + (i * 0.05),
                    execution_time=2.0 - (i * 0.1),
                    success=True,
                )

            assert function_name in learner.prompt_history
            history = learner.prompt_history[function_name]
            assert len(history.performance_scores) == 5
            assert len(history.execution_times) == 5
            assert len(history.success_rates) == 5

            # Check performance improvement
            assert history.performance_scores[-1] > history.performance_scores[0]

    def test_optimization_trigger_logic(self):
        """Test when prompt optimization should be triggered."""
        with tempfile.TemporaryDirectory() as temp_dir:
            learner = PromptLearner(storage_path=temp_dir)
            learner.analysis_frequency = 3  # Lower for testing

            function_name = "test_function"

            # Insufficient data - should not optimize
            assert not learner.should_optimize_prompt(function_name)

            # Record poor performance data
            for i in range(6):
                learner.record_execution_feedback(
                    function_name=function_name,
                    prompt="test prompt",
                    performance_score=0.5,  # Poor performance
                    execution_time=2.0,
                    success=i % 3 != 0,  # 67% success rate
                )

            # Should trigger optimization due to poor performance
            learner.execution_count = 5  # Simulate execution count
            assert learner.should_optimize_prompt(function_name)

    def test_learning_recommendations(self):
        """Test learning recommendation generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            learner = PromptLearner(storage_path=temp_dir)

            function_name = "test_function"

            # No data case
            recommendations = learner.get_learning_recommendations(function_name)
            assert "Insufficient data" in recommendations[0]

            # Record some poor performance
            for i in range(5):
                learner.record_execution_feedback(
                    function_name=function_name,
                    prompt="test prompt",
                    performance_score=0.4,  # Poor quality
                    execution_time=15.0,  # Slow
                    success=i % 2 == 0,  # 60% success rate
                )

            recommendations = learner.get_learning_recommendations(function_name)
            assert len(recommendations) > 0
            assert any("quality" in rec.lower() for rec in recommendations)
            assert any("slow" in rec.lower() or "time" in rec.lower() for rec in recommendations)

    def test_prompt_history_persistence(self):
        """Test prompt history save/load functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create and populate learner
            learner1 = PromptLearner(storage_path=temp_dir)
            learner1.record_execution_feedback("test_function", "test prompt", 0.8, 1.5, True)
            learner1._save_prompt_history()

            # Create new learner instance - should load data
            learner2 = PromptLearner(storage_path=temp_dir)
            assert "test_function" in learner2.prompt_history
            history = learner2.prompt_history["test_function"]
            assert len(history.performance_scores) == 1
            assert history.performance_scores[0] == 0.8


class TestEnhancedLLMOptimizationPlugin:
    """Test the enhanced LLM optimization plugin."""

    def test_plugin_initialization(self):
        """Test plugin initializes correctly."""
        plugin = EnhancedLLMOptimizationPlugin(enable_prompt_learning=True)

        assert plugin.get_plugin_name() == "enhanced_llm_optimization"
        assert plugin.enable_prompt_learning is True
        assert plugin.prompt_learner is not None
        assert plugin.prompt_enhancement_enabled is True

    def test_plugin_initialization_without_learning(self):
        """Test plugin initialization with learning disabled."""
        plugin = EnhancedLLMOptimizationPlugin(enable_prompt_learning=False)

        assert plugin.prompt_learner is None
        assert plugin.enable_prompt_learning is False

    def test_input_processing_basic(self):
        """Test basic input processing without learning."""
        plugin = EnhancedLLMOptimizationPlugin(enable_prompt_learning=False)

        # Test prompt extraction and basic optimization
        args = ("Analyze this data",)
        kwargs = {}

        result = plugin.process_inputs(args, kwargs)

        assert "args" in result
        assert "kwargs" in result
        assert len(result["args"][0]) > len(args[0])  # Should be enhanced
        assert "detailed and accurate" in result["args"][0]

    def test_input_processing_with_learning(self):
        """Test input processing with prompt learning enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin = EnhancedLLMOptimizationPlugin(enable_prompt_learning=True, storage_path=temp_dir)

            # Set context
            plugin.set_current_context("test_function", "financial_services")

            args = ("Analyze credit risk",)
            kwargs = {}

            result = plugin.process_inputs(args, kwargs)

            assert "args" in result
            assert "kwargs" in result
            # Prompt should be processed
            assert len(result["args"]) > 0

    def test_output_validation_with_feedback(self):
        """Test output validation and feedback recording."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin = EnhancedLLMOptimizationPlugin(enable_prompt_learning=True, storage_path=temp_dir)

            plugin.set_current_context("test_function", "financial_services")

            # Mock context with prompt information
            context = {"perceived_input": {"args": ("Analyze financial risk",), "kwargs": {}}, "execution_time": 2.5, "success": True}

            result = "High risk due to low credit score"
            validated_result = plugin.validate_output(result, context)

            assert validated_result == result
            # Should have recorded feedback in learner
            assert "test_function" in plugin.prompt_learner.prompt_history

    def test_learning_status_reporting(self):
        """Test learning status reporting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin = EnhancedLLMOptimizationPlugin(enable_prompt_learning=True, storage_path=temp_dir)

            status = plugin.get_learning_status()

            assert status["learning_enabled"] is True
            assert status["parameters_learned"] == 3
            assert "functions_tracked" in status
            assert "total_optimizations" in status

    def test_learnable_parameters(self):
        """Test learnable parameter definition."""
        plugin = EnhancedLLMOptimizationPlugin()

        params = plugin.get_learnable_parameters()

        assert "prompt_enhancement_enabled" in params
        assert "context_optimization_level" in params
        assert "response_validation_threshold" in params

        # Check parameter metadata
        threshold_param = params["response_validation_threshold"]
        assert threshold_param["type"] == "continuous"
        assert threshold_param["range"] == (0.0, 1.0)

    def test_parameter_learning_application(self):
        """Test applying learned parameters."""
        plugin = EnhancedLLMOptimizationPlugin()

        original_threshold = plugin.response_validation_threshold

        learned_params = {"response_validation_threshold": 0.8, "context_optimization_level": 0.9, "prompt_enhancement_enabled": False}

        plugin.apply_learned_parameters(learned_params)

        assert plugin.response_validation_threshold == 0.8
        assert plugin.context_optimization_level == 0.9
        assert plugin.prompt_enhancement_enabled is False

    def test_plugin_info(self):
        """Test plugin information reporting."""
        plugin = EnhancedLLMOptimizationPlugin(enable_prompt_learning=True)

        info = plugin.get_plugin_info()

        assert info["name"] == "enhanced_llm_optimization"
        assert info["domain"] == "llm_optimization"
        assert "prompt_learning" in info["capabilities"]
        assert "llm_prompt_analysis" in info["learning_features"]
        assert "adaptive_learning" in info["optimization_features"]


class TestPOETIntegration:
    """Test integration with POET executor."""

    def test_poet_with_enhanced_llm_plugin(self):
        """Test POET executor with enhanced LLM plugin."""

        # Create a mock function to enhance
        def mock_reason(prompt: str) -> str:
            return f"Analysis: {prompt}"

        # Configure POET with enhanced LLM optimization
        config = POETConfig(domain="enhanced_llm_optimization", enable_training=True, learning_algorithm="statistical")

        executor = POETExecutor(config)
        enhanced_function = executor(mock_reason)

        # Execute function - should use enhanced prompt
        result = enhanced_function("Analyze financial risk")

        assert isinstance(result, str)
        assert "Analysis:" in result
        # Should have POET executor attached
        assert hasattr(enhanced_function, "_poet_executor")

    @patch("opendxa.dana.poet.plugins.PLUGIN_REGISTRY")
    def test_plugin_discovery_and_loading(self, mock_registry):
        """Test that the enhanced plugin can be discovered and loaded."""
        # Mock the plugin registry to return our enhanced plugin
        mock_plugin = EnhancedLLMOptimizationPlugin()
        mock_registry.get_plugin.return_value = mock_plugin

        config = POETConfig(domain="enhanced_llm_optimization")
        executor = POETExecutor(config)

        assert executor.domain_plugin is not None
        mock_registry.get_plugin.assert_called_with("enhanced_llm_optimization")


class TestEndToEndLearning:
    """Test end-to-end learning functionality."""

    def test_complete_learning_cycle(self):
        """Test complete learning cycle from execution to optimization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin = EnhancedLLMOptimizationPlugin(enable_prompt_learning=True, storage_path=temp_dir)

            function_name = "risk_analyzer"
            plugin.set_current_context(function_name, "financial_services")

            # Simulate multiple executions with poor performance
            for i in range(10):
                # Process inputs
                args = ("Analyze credit risk",)
                processed = plugin.process_inputs(args, {})

                # Simulate execution
                context = {
                    "perceived_input": processed,
                    "execution_time": 3.0 + i * 0.1,
                    "success": i % 3 != 0,  # 67% success rate
                }

                # Validate output (triggers feedback recording)
                result = f"Risk analysis result {i}"
                plugin.validate_output(result, context)

                # Provide execution feedback
                feedback = {
                    "function_name": function_name,
                    "success": context["success"],
                    "execution_time": context["execution_time"],
                    "output_quality": 0.6 + (i * 0.02),  # Gradually improving
                    "error_type": None if context["success"] else "timeout",
                    "parameters_used": {},
                    "perceived_input": processed,
                    "execution_result": {"success": context["success"]},
                }
                plugin.receive_feedback(feedback)

            # Check that learning occurred
            assert function_name in plugin.prompt_learner.prompt_history
            history = plugin.prompt_learner.prompt_history[function_name]
            assert len(history.performance_scores) == 10

            # Get recommendations
            recommendations = plugin.get_learning_recommendations(function_name)
            assert len(recommendations) > 0

            # Check learning status
            status = plugin.get_learning_status()
            assert status["functions_tracked"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
