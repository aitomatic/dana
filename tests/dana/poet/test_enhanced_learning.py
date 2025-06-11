"""
Tests for Enhanced POET T-Stage Learning System

This module tests the advanced learning capabilities including:
- Statistical online learning
- Performance tracking and metrics
- Parameter convergence
- Cross-function learning preparation
"""

import json
import pytest
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from opendxa.dana.poet.learning.online_learner import OnlineLearner, ExecutionFeedback, ParameterHistory
from opendxa.dana.poet.learning.metrics import PerformanceTracker, LearningMetrics, PerformanceSnapshot


class TestOnlineLearner:
    """Test the statistical online learning system"""

    def test_online_learner_initialization(self):
        """Test online learner initializes correctly"""
        learner = OnlineLearner(base_learning_rate=0.1, momentum=0.9, confidence_threshold=0.8)

        assert learner.base_learning_rate == 0.1
        assert learner.momentum == 0.9
        assert learner.confidence_threshold == 0.8
        assert learner.update_count == 0
        assert learner.successful_updates == 0

    def test_execution_feedback_creation(self):
        """Test execution feedback data structure"""
        feedback = ExecutionFeedback(
            function_name="test_function",
            execution_id="12345",
            success=True,
            execution_time=1.5,
            output_quality=0.8,
            parameters_used={"timeout": 30.0, "retries": 3},
        )

        assert feedback.function_name == "test_function"
        assert feedback.success is True
        assert feedback.execution_time == 1.5
        assert feedback.output_quality == 0.8
        assert feedback.parameters_used["timeout"] == 30.0

    def test_parameter_history_tracking(self):
        """Test parameter history tracking"""
        history = ParameterHistory()

        # Add observations
        history.add_observation(30.0, 0.8, 0.7)
        history.add_observation(28.0, 0.85, 0.8)
        history.add_observation(26.0, 0.9, 0.9)

        assert len(history.values) == 3
        assert len(history.performances) == 3
        assert list(history.values)[-1] == 26.0
        assert list(history.performances)[-1] == 0.9

        # Test trend calculation
        trend = history.get_recent_trend()
        assert trend > 0  # Performance should be improving

        # Test gradient estimation
        gradient = history.estimate_gradient()
        assert gradient != 0  # Should detect parameter-performance relationship

    def test_timeout_parameter_optimization(self):
        """Test timeout parameter learning"""
        learner = OnlineLearner(base_learning_rate=0.1)

        # Simulate slow execution that should increase timeout
        feedback = ExecutionFeedback(
            function_name="slow_function",
            execution_id="1",
            success=True,
            execution_time=28.0,  # Near timeout (28s > 90% of 30s = 27s)
            output_quality=0.7,
            parameters_used={"timeout": 30.0},
        )

        current_params = {"timeout": 30.0}
        updated_params = learner.update_parameters(feedback, current_params)

        # Timeout should increase due to near-timeout execution
        assert updated_params["timeout"] > current_params["timeout"]
        assert updated_params["timeout"] <= 300.0  # Within bounds

    def test_retries_parameter_optimization(self):
        """Test retries parameter learning"""
        learner = OnlineLearner(base_learning_rate=0.1)

        # Simulate multiple failures to increase retries
        current_params = {"retries": 3}

        for i in range(6):  # Multiple failure observations
            feedback = ExecutionFeedback(
                function_name="failing_function",
                execution_id=str(i),
                success=False,
                execution_time=5.0,
                output_quality=0.0,
                parameters_used=current_params.copy(),
            )

            updated_params = learner.update_parameters(feedback, current_params)
            current_params = updated_params

        # Retries should increase due to failures
        assert updated_params["retries"] > 3
        assert updated_params["retries"] <= 10  # Within bounds

    def test_learning_statistics(self):
        """Test learning statistics collection"""
        learner = OnlineLearner()

        # Simulate learning updates
        for i in range(10):
            feedback = ExecutionFeedback(
                function_name="test_function",
                execution_id=str(i),
                success=i % 2 == 0,  # 50% success rate
                execution_time=1.0,
                output_quality=0.7 if i % 2 == 0 else 0.3,
                parameters_used={"timeout": 30.0},
            )

            learner.update_parameters(feedback, {"timeout": 30.0})

        stats = learner.get_learning_stats()

        assert stats["update_count"] == 10
        assert 0 <= stats["success_rate"] <= 1
        assert stats["parameters_tracked"] > 0
        assert "last_update" in stats
        assert "global_performance_trend" in stats

    def test_convergence_detection(self):
        """Test parameter convergence detection"""
        learner = OnlineLearner()

        # Simulate converging parameter values
        stable_value = 30.0
        for i in range(25):
            # Add small noise around stable value
            noise = 0.01 * (i % 3 - 1)  # Small variations
            feedback = ExecutionFeedback(
                function_name="converging_function",
                execution_id=str(i),
                success=True,
                execution_time=1.0,
                output_quality=0.8,
                parameters_used={"timeout": stable_value + noise},
            )

            learner.update_parameters(feedback, {"timeout": stable_value + noise})

        # Should detect convergence - use "timeout" to match any key containing timeout
        converged = learner.detect_convergence("timeout")
        assert converged is True


class TestPerformanceTracker:
    """Test the performance tracking and metrics system"""

    def test_performance_tracker_initialization(self):
        """Test performance tracker initializes correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = PerformanceTracker(storage_path=temp_dir, window_hours=24)

            assert tracker.storage_path == Path(temp_dir)
            assert tracker.window_hours == 24
            assert len(tracker.performance_history) == 0

    def test_performance_recording(self):
        """Test performance measurement recording"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = PerformanceTracker(storage_path=temp_dir)

            # Record performance
            tracker.record_performance(
                function_name="test_function",
                parameter_values={"timeout": 30.0, "retries": 3},
                performance_score=0.8,
                execution_time=2.5,
                success=True,
            )

            assert len(tracker.performance_history) == 1
            assert "test_function" in tracker.parameter_evolution
            assert len(tracker.parameter_evolution["test_function"]) == 1

            snapshot = tracker.performance_history[0]
            assert snapshot.function_name == "test_function"
            assert snapshot.performance_score == 0.8
            assert snapshot.success is True

    def test_learning_metrics_calculation(self):
        """Test comprehensive learning metrics calculation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = PerformanceTracker(storage_path=temp_dir)

            # Record multiple performance measurements
            for i in range(20):
                performance_score = 0.5 + (i * 0.02)  # Improving performance
                tracker.record_performance(
                    function_name="improving_function",
                    parameter_values={"timeout": 30.0 - i, "retries": 3},
                    performance_score=performance_score,
                    execution_time=2.0 - (i * 0.05),
                    success=True,
                )

            metrics = tracker.calculate_learning_metrics("improving_function")

            assert metrics.total_updates == 20
            assert metrics.successful_updates == 20
            assert metrics.average_improvement > 0  # Should show improvement
            assert metrics.performance_trend > 0  # Positive trend
            assert len(metrics.parameter_stability) > 0

    def test_parameter_update_tracking(self):
        """Test parameter update effectiveness tracking"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = PerformanceTracker(storage_path=temp_dir)

            # Record parameter update
            tracker.record_parameter_update(
                function_name="adaptive_function",
                old_params={"timeout": 30.0},
                new_params={"timeout": 25.0},
                predicted_improvement=0.1,
                actual_improvement=0.08,
            )

            # Should track prediction accuracy
            assert len(tracker.prediction_accuracy_history) == 1
            accuracy = tracker.prediction_accuracy_history[0]
            assert 0 <= accuracy <= 1

    def test_performance_summary_generation(self):
        """Test performance summary generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = PerformanceTracker(storage_path=temp_dir)

            # Record diverse performance data
            for i in range(15):
                tracker.record_performance(
                    function_name="summary_function",
                    parameter_values={"timeout": 30.0, "retries": 3},
                    performance_score=0.6 + (i * 0.02),
                    execution_time=1.5,
                    success=i % 4 != 0,  # 75% success rate
                )

            summary = tracker.get_performance_summary("summary_function")

            assert "metrics" in summary
            assert "statistics" in summary
            assert "insights" in summary

            insights = summary["insights"]
            assert isinstance(insights, list)
            assert len(insights) > 0


class TestLearningMetrics:
    """Test learning metrics data structures"""

    def test_learning_metrics_serialization(self):
        """Test metrics serialization and deserialization"""
        metrics = LearningMetrics(
            total_updates=100,
            successful_updates=85,
            convergence_rate=0.7,
            average_improvement=0.15,
            learning_efficiency=0.8,
            prediction_accuracy=0.75,
        )

        # Test to_dict
        data = metrics.to_dict()
        assert data["total_updates"] == 100
        assert data["successful_updates"] == 85
        assert "last_updated" in data

        # Test from_dict
        restored_metrics = LearningMetrics.from_dict(data)
        assert restored_metrics.total_updates == 100
        assert restored_metrics.successful_updates == 85
        assert restored_metrics.convergence_rate == 0.7

    def test_performance_snapshot_serialization(self):
        """Test performance snapshot serialization"""
        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(),
            function_name="test_function",
            parameter_values={"timeout": 30.0},
            performance_score=0.8,
            execution_time=2.0,
            success=True,
        )

        data = snapshot.to_dict()
        assert data["function_name"] == "test_function"
        assert data["performance_score"] == 0.8
        assert "timestamp" in data


class TestIntegratedLearningSystem:
    """Test the integrated learning system end-to-end"""

    def test_learning_system_integration(self):
        """Test complete learning system working together"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize components
            learner = OnlineLearner(base_learning_rate=0.1)
            tracker = PerformanceTracker(storage_path=temp_dir)

            # Simulate learning loop
            current_params = {"timeout": 30.0, "retries": 3}

            for iteration in range(10):
                # Simulate function execution
                execution_time = 2.0 + (iteration * 0.1)
                success = iteration % 3 != 0  # Mostly successful
                performance_score = 0.6 + (iteration * 0.03) if success else 0.2

                # Create feedback
                feedback = ExecutionFeedback(
                    function_name="integrated_test",
                    execution_id=str(iteration),
                    success=success,
                    execution_time=execution_time,
                    output_quality=performance_score,
                    parameters_used=current_params.copy(),
                )

                # Update parameters with learning
                updated_params = learner.update_parameters(feedback, current_params)

                # Record performance
                tracker.record_performance(
                    function_name="integrated_test",
                    parameter_values=current_params,
                    performance_score=performance_score,
                    execution_time=execution_time,
                    success=success,
                )

                # Record parameter update if changed
                if updated_params != current_params:
                    tracker.record_parameter_update(
                        function_name="integrated_test",
                        old_params=current_params,
                        new_params=updated_params,
                        predicted_improvement=0.05,
                        actual_improvement=performance_score - 0.6,
                    )

                current_params = updated_params

            # Validate learning occurred
            learning_stats = learner.get_learning_stats()
            assert learning_stats["update_count"] == 10
            assert learning_stats["parameters_tracked"] > 0

            # Validate tracking occurred
            metrics = tracker.calculate_learning_metrics("integrated_test")
            assert metrics.total_updates == 10
            assert metrics.learning_efficiency > 0

            # Generate recommendations
            summary = tracker.get_performance_summary("integrated_test")
            insights = summary["insights"]
            assert isinstance(insights, list)

    def test_learning_persistence(self):
        """Test learning data persistence and recovery"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First tracker instance
            tracker1 = PerformanceTracker(storage_path=temp_dir)

            # Record some data
            for i in range(5):
                tracker1.record_performance(
                    function_name="persistent_function",
                    parameter_values={"timeout": 30.0},
                    performance_score=0.7 + (i * 0.05),
                    execution_time=2.0,
                    success=True,
                )

            # Save metrics
            tracker1.save_metrics()

            # Create new tracker instance (simulating restart)
            tracker2 = PerformanceTracker(storage_path=temp_dir)

            # Should load historical data
            assert len(tracker2.performance_history) > 0
            assert "persistent_function" in tracker2.parameter_evolution


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
