#!/usr/bin/env python3
"""
POET ML Monitoring - Production-Ready Example

This example demonstrates POET's ML monitoring domain expertise:
1. Drift detection with statistical intelligence
2. Domain-specific P→O→E→T enhancements
3. Learning from ML operations feedback
4. Production-ready monitoring capabilities
"""

import sys
import os
import numpy as np
from typing import Dict, List, Any, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from opendxa.dana.poet import poet, feedback
from opendxa.common.utils.logging import DXA_LOGGER


@poet(domain="ml_monitoring", optimize_for="accuracy")
def detect_feature_drift(
    current_data: List[float], reference_data: List[float], feature_name: str = "feature", method: str = "ks_test"
) -> Dict[str, Any]:
    """
    Detect statistical drift in feature distributions

    POET enhances this with:
    - Advanced statistical tests (P)
    - Multiple drift detection methods (O)
    - Confidence intervals and significance testing (E)
    - Learning from false positive/negative feedback (T)
    """

    # Basic statistical comparison (will be enhanced by POET)
    current_mean = np.mean(current_data)
    reference_mean = np.mean(reference_data)

    current_std = np.std(current_data)
    reference_std = np.std(reference_data)

    # Simple drift detection (POET will enhance with proper statistical tests)
    mean_diff = abs(current_mean - reference_mean) / (reference_std + 1e-8)
    std_diff = abs(current_std - reference_std) / (reference_std + 1e-8)

    # Basic drift score (POET will enhance with statistical significance)
    drift_score = max(mean_diff, std_diff)
    drift_threshold = 2.0  # Will be learned/adjusted

    drift_detected = drift_score > drift_threshold

    return {
        "drift_detected": drift_detected,
        "drift_score": drift_score,
        "feature_name": feature_name,
        "method": method,
        "threshold": drift_threshold,
        "statistics": {
            "current_mean": current_mean,
            "reference_mean": reference_mean,
            "current_std": current_std,
            "reference_std": reference_std,
            "mean_shift": mean_diff,
            "variance_change": std_diff,
        },
        "sample_sizes": {"current": len(current_data), "reference": len(reference_data)},
    }


@poet(domain="ml_monitoring", optimize_for="reliability")
def monitor_model_performance(
    predictions: List[float], actuals: Optional[List[float]] = None, model_name: str = "model", performance_window: int = 100
) -> Dict[str, Any]:
    """
    Monitor ML model performance metrics

    POET enhances with:
    - Statistical performance analysis (P)
    - Multiple performance metrics (O)
    - Performance degradation detection (E)
    - Learning optimal performance thresholds (T)
    """

    if not predictions:
        return {"status": "no_data", "model_name": model_name, "error": "No predictions provided"}

    # Basic performance monitoring
    pred_array = np.array(predictions)

    # Prediction distribution analysis
    pred_mean = np.mean(pred_array)
    pred_std = np.std(pred_array)
    pred_range = np.max(pred_array) - np.min(pred_array)

    # Performance metrics (enhanced by POET when actuals available)
    performance_metrics = {
        "prediction_mean": pred_mean,
        "prediction_std": pred_std,
        "prediction_range": pred_range,
        "sample_count": len(predictions),
    }

    if actuals is not None and len(actuals) == len(predictions):
        actual_array = np.array(actuals)

        # Basic error metrics (POET will enhance with advanced metrics)
        mae = np.mean(np.abs(pred_array - actual_array))
        mse = np.mean((pred_array - actual_array) ** 2)
        rmse = np.sqrt(mse)

        # Simple correlation
        correlation = np.corrcoef(pred_array, actual_array)[0, 1] if len(predictions) > 1 else 0.0

        performance_metrics.update({"mae": mae, "mse": mse, "rmse": rmse, "correlation": correlation, "has_ground_truth": True})
    else:
        performance_metrics["has_ground_truth"] = False

    # Performance status (POET will enhance with learned thresholds)
    if performance_metrics.get("correlation", 1.0) < 0.8:
        status = "degraded"
        alert_level = "high"
    elif performance_metrics.get("prediction_std", 0) > 10.0:  # Example threshold
        status = "unstable"
        alert_level = "medium"
    else:
        status = "healthy"
        alert_level = "low"

    return {
        "model_name": model_name,
        "status": status,
        "alert_level": alert_level,
        "performance_metrics": performance_metrics,
        "monitoring_window": performance_window,
        "timestamp": "2025-06-14T10:00:00Z",  # Would be actual timestamp
    }


def generate_sample_data():
    """Generate sample data for demonstration"""
    np.random.seed(42)  # Reproducible results

    # Reference data (training distribution)
    reference_data = np.random.normal(100, 15, 1000).tolist()

    # Current data scenarios
    scenarios = {
        "no_drift": np.random.normal(100, 15, 500).tolist(),  # Same distribution
        "mean_shift": np.random.normal(120, 15, 500).tolist(),  # Mean shifted
        "variance_change": np.random.normal(100, 25, 500).tolist(),  # Higher variance
        "distribution_change": np.random.exponential(50, 500).tolist(),  # Different distribution
    }

    # Model performance data
    true_values = np.random.normal(50, 10, 200)
    good_predictions = true_values + np.random.normal(0, 2, 200)  # Low error
    bad_predictions = true_values + np.random.normal(0, 8, 200)  # High error

    return reference_data, scenarios, true_values, good_predictions, bad_predictions


def main():
    """Demonstrate ML monitoring with POET"""
    print("📊 POET ML Monitoring - Production Example")
    print("=" * 60)

    # Generate sample data
    reference_data, drift_scenarios, true_values, good_preds, bad_preds = generate_sample_data()

    print("\n1. Feature Drift Detection:")
    print("   POET adds ML domain expertise to statistical testing")

    drift_results = []

    for scenario_name, current_data in drift_scenarios.items():
        try:
            result = detect_feature_drift(
                current_data=current_data, reference_data=reference_data, feature_name=f"feature_{scenario_name}", method="ks_test"
            )

            drift_results.append((scenario_name, result))
            drift_data = result.unwrap()

            status = "🚨 DRIFT" if drift_data["drift_detected"] else "✅ STABLE"
            print(f"   {scenario_name:20} → {status} (score: {drift_data['drift_score']:.3f})")
            print(f"      Mean shift: {drift_data['statistics']['mean_shift']:.3f}")
            print(f"      Variance change: {drift_data['statistics']['variance_change']:.3f}")

        except Exception as e:
            DXA_LOGGER.error(f"Error in drift detection for {scenario_name}: {e}")
            print(f"   ❌ Error in {scenario_name}: {e}")

    print("\n2. Model Performance Monitoring:")
    print("   POET enhances with statistical performance analysis")

    performance_results = []

    performance_scenarios = [
        ("good_model", good_preds, true_values, "Model performing well"),
        ("degraded_model", bad_preds, true_values, "Model showing degradation"),
        ("prediction_only", good_preds[:100], None, "No ground truth available"),
    ]

    for scenario_name, predictions, actuals, description in performance_scenarios:
        try:
            result = monitor_model_performance(
                predictions=predictions.tolist(),
                actuals=actuals.tolist() if actuals is not None else None,
                model_name=scenario_name,
                performance_window=100,
            )

            performance_results.append((scenario_name, result))
            perf_data = result.unwrap()

            status_icon = {"healthy": "✅", "degraded": "🚨", "unstable": "⚠️", "no_data": "❓"}.get(perf_data["status"], "❓")

            print(f"   {scenario_name:15} → {status_icon} {perf_data['status'].upper()}")
            print(f"      {description}")

            if "mae" in perf_data["performance_metrics"]:
                mae = perf_data["performance_metrics"]["mae"]
                corr = perf_data["performance_metrics"]["correlation"]
                print(f"      MAE: {mae:.3f}, Correlation: {corr:.3f}")

        except Exception as e:
            DXA_LOGGER.error(f"Error in performance monitoring for {scenario_name}: {e}")
            print(f"   ❌ Error in {scenario_name}: {e}")

    print("\n3. Learning from ML Operations Feedback:")
    print("   POET learns from real-world ML operations experience")

    # Realistic MLOps feedback scenarios
    mlops_feedback = [
        # Drift detection feedback
        ("The drift alert for feature_mean_shift was correct - we had to retrain the model", 0, "drift"),
        ("False alarm on feature_no_drift - this variation is normal in production", 0, "drift"),
        ("Threshold too sensitive - getting too many drift alerts during seasonal changes", 1, "drift"),
        # Performance monitoring feedback
        ("Model degradation correctly detected - correlation dropped due to data quality issues", 0, "performance"),
        ("The MAE threshold is too strict - this level is acceptable for our use case", 1, "performance"),
        ("Good catch on the unstable predictions - helped us identify inference pipeline bug", 1, "performance"),
    ]

    for fb_text, result_idx, feedback_type in mlops_feedback[:4]:  # First 4 examples
        try:
            if feedback_type == "drift" and result_idx < len(drift_results):
                scenario_name, result = drift_results[result_idx]
                print(f"   📝 Drift feedback for {scenario_name}:")
                print(f"      '{fb_text}'")
                feedback(result, fb_text)
                print(f"      ✅ Learning applied")

            elif feedback_type == "performance" and result_idx < len(performance_results):
                scenario_name, result = performance_results[result_idx]
                print(f"   📝 Performance feedback for {scenario_name}:")
                print(f"      '{fb_text}'")
                feedback(result, fb_text)
                print(f"      ✅ Learning applied")

        except Exception as e:
            DXA_LOGGER.error(f"Error processing feedback: {e}")
            print(f"   ❌ Error processing feedback: {e}")

    print("\n4. POET ML Domain Enhancements:")
    print("   ✅ Advanced statistical tests (KS, KL divergence, Chi-square)")
    print("   ✅ Multiple drift detection methods with automatic selection")
    print("   ✅ Statistical significance testing and confidence intervals")
    print("   ✅ Adaptive thresholds based on data characteristics")
    print("   ✅ Performance metric calculation with uncertainty bounds")
    print("   ✅ Learning from MLOps feedback to reduce false positives")
    print("   ✅ Domain-specific error handling and edge case management")

    print("\n5. Generated Artifacts:")
    print("   📁 Enhanced functions stored in .poet/ directory")
    print("   📊 Learning state and feedback history preserved")
    print("   🔧 Train methods generated for continuous improvement")
    print("   📈 Performance metrics and drift statistics tracked")

    print("\n✅ ML Monitoring demo complete!")
    print("   This demonstrates POET's value for production ML systems:")
    print("   - Zero-config statistical intelligence")
    print("   - Domain expertise without manual implementation")
    print("   - Learning from operations to reduce false alerts")
    print("   - Production-ready reliability and error handling")


if __name__ == "__main__":
    main()
