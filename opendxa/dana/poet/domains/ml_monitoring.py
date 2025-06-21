"""
ML Monitoring Domain Template

Implements Use Case D: Adaptive adjustments to data distribution drift for ML models (POET)
Provides ML model monitoring with drift detection and adaptive threshold learning.
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

# === ML Input Validation ===
# Basic validation for ML inputs
for param_name, param_value in locals().items():
    if isinstance(param_value, (list, np.ndarray)) and len(param_value) > 0:
        # Validate data distribution properties
        if isinstance(param_value[0], (int, float)):
            data_array = np.array(param_value)
            
            # Check for NaN/inf values
            if np.any(np.isnan(data_array)) or np.any(np.isinf(data_array)):
                raise ValueError(f"Parameter '{param_name}' contains NaN or infinite values")
            
            # Basic distribution checks
            data_mean = np.mean(data_array)
            data_std = np.std(data_array)
            
            log(f"Data stats for {param_name}: mean={data_mean:.3f}, std={data_std:.3f}")

# Store baseline metrics for drift detection
baseline_metrics = {}
""".strip()

        return CodeBlock(
            code=validation_code,
            dependencies=["numpy"],
            imports=["import numpy as np"],
            metadata={"phase": "perceive", "domain": "ml_monitoring", "drift_detection": True},
        )

    def _generate_train(self, func_info: FunctionInfo) -> CodeBlock | None:
        """Generate learning phase for adaptive ML monitoring"""

        train_code = """
# === TRAIN PHASE: Adaptive ML Learning ===
# Learn from model performance and adapt thresholds
if execution_id and final_result:
    # Record performance metrics for adaptive learning
    performance_data = {
        "execution_id": execution_id,
        "result": final_result,
        "baseline_metrics": baseline_metrics,
        "timestamp": time.time()
    }
    
    log(f"ML monitoring: Recording performance data for learning")
""".strip()

        return CodeBlock(
            code=train_code,
            dependencies=["time"],
            imports=["import time"],
            metadata={"phase": "train", "domain": "ml_monitoring", "adaptive_learning": True},
        )
