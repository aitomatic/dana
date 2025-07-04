"""
ML Monitoring Domain Template

Implements Use Case D: Adaptive adjustments to data distribution drift for ML models (POET)
Provides ML model monitoring with drift detection and adaptive threshold learning.

Features:
- Data distribution monitoring and drift detection
- Adaptive threshold adjustment based on historical performance
- Anomaly detection with self-adjusting sensitivity
- Performance tracking and automated retraining triggers
"""

from .base import BaseDomainTemplate, CodeBlock, FunctionInfo


class MLMonitoringDomain(BaseDomainTemplate):
    """
    Domain template for ML model monitoring and adaptive learning.

    Enhances ML functions with:
    - Data distribution monitoring
    - Drift detection and alerting
    - Adaptive threshold adjustment
    - Performance tracking and learning
    """

    def _generate_perceive(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate ML input validation and drift detection"""

        validation_code = """
import numpy as np
from typing import Any
from dana.frameworks.poet.storage import POETStorage

# === ML Input Validation ===
# Basic validation for ML inputs
input_stats = {}
for param_name, param_value in locals().items():
    if isinstance(param_value, (list, np.ndarray)) and len(param_value) > 0:
        # Validate data distribution properties
        if isinstance(param_value[0], (int, float)):
            data_array = np.array(param_value)
            
            # Check for NaN/inf values
            if np.any(np.isnan(data_array)) or np.any(np.isinf(data_array)):
                raise ValueError(f"Parameter '{param_name}' contains NaN or infinite values")
            
            # Calculate distribution statistics
            data_mean = np.mean(data_array)
            data_std = np.std(data_array)
            data_min = np.min(data_array)
            data_max = np.max(data_array)
            data_median = np.median(data_array)
            
            input_stats[param_name] = {
                "mean": float(data_mean),
                "std": float(data_std),
                "min": float(data_min),
                "max": float(data_max),
                "median": float(data_median),
                "count": len(data_array)
            }
            
            log(f"Data stats for {param_name}: mean={data_mean:.3f}, std={data_std:.3f}")

# === Load Historical Baselines ===
poet_storage = POETStorage()
drift_thresholds = {
    "mean_drift": 2.0,    # Default: 2 standard deviations
    "std_drift": 0.5,     # Default: 50% change in variance
    "range_drift": 3.0    # Default: 3x range expansion
}

try:
    # Load adaptive thresholds if available
    threshold_key = f"{func_info.name}_drift_thresholds"
    if poet_storage.exists(threshold_key):
        saved_thresholds = poet_storage.load_training_data(threshold_key)
        drift_thresholds.update(saved_thresholds.get("thresholds", {}))
        log(f"Loaded adaptive drift thresholds")
        
    # Load baseline statistics
    baseline_key = f"{func_info.name}_baseline_stats"
    baseline_stats = {}
    if poet_storage.exists(baseline_key):
        baseline_stats = poet_storage.load_training_data(baseline_key).get("stats", {})
        log(f"Loaded baseline statistics for {len(baseline_stats)} parameters")
        
except Exception as e:
    log(f"Could not load ML monitoring data: {e}")
    baseline_stats = {}

# === Drift Detection ===
drift_detected = False
drift_details = []

for param_name, current_stats in input_stats.items():
    if param_name in baseline_stats:
        baseline = baseline_stats[param_name]
        
        # Check mean drift
        mean_drift = abs(current_stats["mean"] - baseline["mean"]) / (baseline["std"] + 1e-6)
        if mean_drift > drift_thresholds["mean_drift"]:
            drift_detected = True
            drift_details.append({
                "parameter": param_name,
                "type": "mean_drift",
                "baseline_mean": baseline["mean"],
                "current_mean": current_stats["mean"],
                "drift_score": mean_drift
            })
            
        # Check variance drift
        std_ratio = current_stats["std"] / (baseline["std"] + 1e-6)
        if std_ratio > (1 + drift_thresholds["std_drift"]) or std_ratio < (1 - drift_thresholds["std_drift"]):
            drift_detected = True
            drift_details.append({
                "parameter": param_name,
                "type": "std_drift",
                "baseline_std": baseline["std"],
                "current_std": current_stats["std"],
                "drift_score": abs(std_ratio - 1)
            })
            
        # Check range drift
        baseline_range = baseline["max"] - baseline["min"]
        current_range = current_stats["max"] - current_stats["min"]
        range_ratio = current_range / (baseline_range + 1e-6)
        if range_ratio > drift_thresholds["range_drift"]:
            drift_detected = True
            drift_details.append({
                "parameter": param_name,
                "type": "range_drift",
                "baseline_range": baseline_range,
                "current_range": current_range,
                "drift_score": range_ratio
            })

if drift_detected:
    log(f"⚠️ Data drift detected: {len(drift_details)} anomalies found")
    for detail in drift_details[:3]:  # Show first 3
        log(f"  - {detail['parameter']}: {detail['type']} (score: {detail['drift_score']:.2f})")

# Store validation results
validated_inputs = {
    "input_stats": input_stats,
    "baseline_stats": baseline_stats,
    "drift_detected": drift_detected,
    "drift_details": drift_details,
    "drift_thresholds": drift_thresholds
}
""".strip()

        return CodeBlock(
            code=validation_code,
            dependencies=["numpy", "dana.poet.storage"],
            imports=["import numpy as np", "from dana.frameworks.poet.storage import POETStorage"],
            metadata={"phase": "perceive", "domain": "ml_monitoring", "drift_detection": True, "adaptive_thresholds": True},
        )

    def _generate_operate(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate ML operation with monitoring and adaptation"""

        # Call parent for basic retry logic
        parent_block = super()._generate_operate(func_info)

        # Add ML-specific monitoring
        enhanced_operation = f"""
{parent_block.code}

# === ML Model Execution with Monitoring ===
import time

# Track model performance metrics
model_start_time = time.time()
prediction_metadata = {{
    "drift_detected": validated_inputs["drift_detected"],
    "drift_score": len(validated_inputs["drift_details"]),
    "input_distribution": validated_inputs["input_stats"]
}}

# If significant drift detected, adjust model behavior
if validated_inputs["drift_detected"] and len(validated_inputs["drift_details"]) > 2:
    log("⚠️ Significant drift detected - model may need retraining")
    prediction_metadata["needs_retraining"] = True
    
    # Could implement adaptive strategies here:
    # - Use ensemble of models
    # - Apply input normalization
    # - Increase uncertainty estimates
    
# Store prediction context
prediction_metadata["execution_time"] = time.time() - model_start_time
prediction_metadata["model_version"] = getattr(locals().get('model'), 'version', 'unknown')

# === Anomaly Detection ===
# Check if result seems anomalous based on historical patterns
if isinstance(result, (int, float, list, np.ndarray)):
    result_array = np.array(result) if isinstance(result, (list, np.ndarray)) else np.array([result])
    
    # Simple anomaly detection based on result distribution
    if len(result_array) > 0 and np.all(np.isfinite(result_array)):
        result_mean = np.mean(result_array)
        result_std = np.std(result_array)
        
        # Store for anomaly detection
        prediction_metadata["result_stats"] = {{
            "mean": float(result_mean),
            "std": float(result_std),
            "min": float(np.min(result_array)),
            "max": float(np.max(result_array))
        }}

# Add metadata to execution context
execution_metadata.update(prediction_metadata)
""".strip()

        return CodeBlock(
            code=enhanced_operation,
            dependencies=parent_block.dependencies + ["time", "numpy"],
            imports=parent_block.imports + ["import time", "import numpy as np"],
            metadata={**parent_block.metadata, "domain": "ml_monitoring", "drift_adaptation": True, "anomaly_detection": True},
        )

    def _generate_enforce(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate ML result validation with adaptive thresholds"""

        # Call parent for basic enforcement
        parent_block = super()._generate_enforce(func_info)

        # Add ML-specific validation
        ml_enforcement = f"""
{parent_block.code}

# === ML Result Validation ===
from dana.frameworks.poet.storage import POETStorage

# Load adaptive anomaly thresholds
poet_storage = POETStorage()
anomaly_thresholds = {{
    "result_mean_range": (-1000, 1000),  # Default wide range
    "result_std_max": 100,               # Default max std
    "confidence_min": 0.5                # Default min confidence
}}

try:
    anomaly_key = f"{{func_info.name}}_anomaly_thresholds"
    if poet_storage.exists(anomaly_key):
        saved_thresholds = poet_storage.load_training_data(anomaly_key)
        anomaly_thresholds.update(saved_thresholds.get("thresholds", {{}}))
except Exception as e:
    log(f"Using default anomaly thresholds: {{e}}")

# Validate result statistics
anomaly_detected = False
anomaly_reasons = []

if "result_stats" in execution_metadata:
    result_stats = execution_metadata["result_stats"]
    
    # Check if result mean is in expected range
    if not (anomaly_thresholds["result_mean_range"][0] <= result_stats["mean"] <= anomaly_thresholds["result_mean_range"][1]):
        anomaly_detected = True
        anomaly_reasons.append(f"Result mean {{result_stats['mean']:.2f}} outside expected range")
        
    # Check if result variance is reasonable
    if result_stats["std"] > anomaly_thresholds["result_std_max"]:
        anomaly_detected = True
        anomaly_reasons.append(f"Result std {{result_stats['std']:.2f}} exceeds threshold")

# Check model confidence if available
if hasattr(final_result, 'confidence') or isinstance(final_result, dict) and 'confidence' in final_result:
    confidence = final_result.confidence if hasattr(final_result, 'confidence') else final_result['confidence']
    if confidence < anomaly_thresholds["confidence_min"]:
        anomaly_detected = True
        anomaly_reasons.append(f"Model confidence {{confidence:.2f}} below threshold")

if anomaly_detected:
    log(f"⚠️ Anomalous result detected: {{', '.join(anomaly_reasons)}}")
    
# === Performance Tracking ===
performance_score = 1.0

# Penalize for drift
if validated_inputs["drift_detected"]:
    drift_penalty = min(0.3, len(validated_inputs["drift_details"]) * 0.1)
    performance_score -= drift_penalty
    
# Penalize for anomalies
if anomaly_detected:
    anomaly_penalty = min(0.3, len(anomaly_reasons) * 0.1)
    performance_score -= anomaly_penalty
    
# Bonus for fast execution
exec_time = execution_metadata.get("execution_time", 1.0)
if exec_time < 0.1:
    performance_score += 0.1

performance_score = max(0, min(1, performance_score))  # Clamp to [0,1]

# Store ML validation metadata
ml_validation_metadata = {{
    "anomaly_detected": anomaly_detected,
    "anomaly_reasons": anomaly_reasons,
    "performance_score": performance_score,
    "drift_detected": validated_inputs["drift_detected"],
    "needs_retraining": execution_metadata.get("needs_retraining", False)
}}

validation_metadata.update(ml_validation_metadata)
log(f"ML monitoring score: {{performance_score:.2f}}")
""".strip()

        return CodeBlock(
            code=ml_enforcement,
            dependencies=parent_block.dependencies + ["dana.poet.storage"],
            imports=parent_block.imports + ["from dana.frameworks.poet.storage import POETStorage"],
            metadata={
                **parent_block.metadata,
                "domain": "ml_monitoring",
                "anomaly_validation": True,
                "adaptive_thresholds": True,
                "performance_tracking": True,
            },
        )

    def _generate_train(self, func_info: FunctionInfo) -> CodeBlock | None:
        """Generate comprehensive learning phase for adaptive ML monitoring"""

        train_code = """
# === TRAIN PHASE: Adaptive ML Learning ===
from dana.frameworks.poet.storage import POETStorage
import time
import numpy as np

if execution_id and final_result:
    try:
        poet_storage = POETStorage()
        
        # 1. Update baseline statistics (rolling average)
        baseline_key = f"{func_info.name}_baseline_stats"
        baseline_data = {}
        if poet_storage.exists(baseline_key):
            baseline_data = poet_storage.load_training_data(baseline_key)
            
        current_stats = validated_inputs["input_stats"]
        baseline_stats = baseline_data.get("stats", {})
        
        # Update baselines with exponential moving average
        alpha = 0.1  # Learning rate
        for param_name, new_stats in current_stats.items():
            if param_name in baseline_stats:
                # Blend old and new statistics
                old_stats = baseline_stats[param_name]
                baseline_stats[param_name] = {
                    "mean": (1 - alpha) * old_stats["mean"] + alpha * new_stats["mean"],
                    "std": (1 - alpha) * old_stats["std"] + alpha * new_stats["std"],
                    "min": min(old_stats["min"], new_stats["min"]),
                    "max": max(old_stats["max"], new_stats["max"]),
                    "median": (1 - alpha) * old_stats["median"] + alpha * new_stats["median"],
                    "count": old_stats["count"] + new_stats["count"]
                }
            else:
                baseline_stats[param_name] = new_stats
                
        baseline_data["stats"] = baseline_stats
        baseline_data["last_updated"] = time.time()
        baseline_data["total_observations"] = baseline_data.get("total_observations", 0) + 1
        poet_storage.save_training_data(baseline_key, baseline_data)
        
        # 2. Adapt drift thresholds based on false positive rate
        if not validated_inputs["drift_detected"] or performance_score > 0.8:
            # Good performance - can tighten thresholds slightly
            threshold_key = f"{func_info.name}_drift_thresholds"
            threshold_data = {}
            if poet_storage.exists(threshold_key):
                threshold_data = poet_storage.load_training_data(threshold_key)
                
            thresholds = threshold_data.get("thresholds", validated_inputs["drift_thresholds"])
            
            # Adaptive adjustment
            if performance_score > 0.9:
                # Tighten thresholds for better sensitivity
                thresholds["mean_drift"] *= 0.95
                thresholds["std_drift"] *= 0.95
            elif validated_inputs["drift_detected"] and performance_score < 0.6:
                # Loosen thresholds to reduce false positives
                thresholds["mean_drift"] *= 1.05
                thresholds["std_drift"] *= 1.05
                
            # Keep thresholds in reasonable range
            thresholds["mean_drift"] = max(0.5, min(5.0, thresholds["mean_drift"]))
            thresholds["std_drift"] = max(0.2, min(1.0, thresholds["std_drift"]))
            
            threshold_data["thresholds"] = thresholds
            threshold_data["last_adjusted"] = time.time()
            poet_storage.save_training_data(threshold_key, threshold_data)
            
        # 3. Update anomaly thresholds based on result distribution
        if "result_stats" in execution_metadata and not anomaly_detected:
            anomaly_key = f"{func_info.name}_anomaly_thresholds"
            anomaly_data = {}
            if poet_storage.exists(anomaly_key):
                anomaly_data = poet_storage.load_training_data(anomaly_key)
                
            result_stats = execution_metadata["result_stats"]
            current_thresholds = anomaly_data.get("thresholds", anomaly_thresholds)
            
            # Expand acceptable range based on observed results
            margin = 3 * result_stats["std"]  # 3-sigma rule
            new_min = result_stats["mean"] - margin
            new_max = result_stats["mean"] + margin
            
            # Update with conservative expansion
            current_range = current_thresholds.get("result_mean_range", [-1000, 1000])
            current_thresholds["result_mean_range"] = [
                min(current_range[0], new_min),
                max(current_range[1], new_max)
            ]
            
            # Update std threshold
            current_thresholds["result_std_max"] = max(
                current_thresholds.get("result_std_max", 100),
                result_stats["std"] * 2
            )
            
            anomaly_data["thresholds"] = current_thresholds
            anomaly_data["last_updated"] = time.time()
            poet_storage.save_training_data(anomaly_key, anomaly_data)
            
        # 4. Track retraining recommendations
        if needs_retraining:
            retrain_key = f"{func_info.name}_retrain_log"
            retrain_data = {}
            if poet_storage.exists(retrain_key):
                retrain_data = poet_storage.load_training_data(retrain_key)
                
            retrain_log = retrain_data.get("log", [])
            retrain_log.append({
                "timestamp": time.time(),
                "execution_id": execution_id,
                "drift_details": drift_details[:5],  # Keep top 5
                "performance_score": performance_score
            })
            
            # Keep only recent entries
            retrain_log = retrain_log[-100:]
            
            # Check if retraining is urgently needed
            recent_scores = [entry["performance_score"] for entry in retrain_log[-10:]]
            if len(recent_scores) >= 5 and np.mean(recent_scores) < 0.6:
                log("🚨 URGENT: Model retraining recommended - consistent poor performance")
                
            retrain_data["log"] = retrain_log
            retrain_data["last_updated"] = time.time()
            poet_storage.save_training_data(retrain_key, retrain_data)
            
        log(f"ML adaptive learning: Updated baselines and thresholds (performance: {performance_score:.2f})")
        
    except Exception as e:
        log(f"ML adaptive learning failed: {e}")
""".strip()

        return CodeBlock(
            code=train_code,
            dependencies=["dana.poet.storage", "time", "numpy"],
            imports=["from dana.frameworks.poet.storage import POETStorage", "import time", "import numpy as np"],
            metadata={
                "phase": "train",
                "domain": "ml_monitoring",
                "adaptive_learning": True,
                "baseline_updating": True,
                "threshold_adaptation": True,
                "retraining_detection": True,
            },
        )
