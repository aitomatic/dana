# POET Configuration Guide

Comprehensive guide to configuring POET (Parameter Optimization Engine + Training) for different use cases, environments, and performance requirements.

## 🎯 Configuration Overview

POET offers flexible configuration options that balance simplicity with power:
- **Zero Configuration**: Works out-of-the-box with sensible defaults
- **Domain Intelligence**: Pre-built configurations for specific industries
- **Fine-Tuning**: Detailed control for performance optimization
- **Environment Profiles**: Different settings for dev, test, and production

## 🚀 Quick Configuration Examples

### Minimal Setup
```dana
# Just add the decorator - POET handles everything else
@poet()
def my_function(input: str) -> str:
    return reason(input)
```

### Domain-Specific Setup
```dana
# Get industry expertise automatically
@poet(domain="financial_services")
def credit_assessment(data: dict) -> dict:
    return assess_creditworthiness(data)
```

### Performance-Tuned Setup
```dana
# Optimized for production workloads
@poet(
    domain="manufacturing",
    timeout=25.0,
    retries=5,
    enable_training=true,
    learning_algorithm="statistical"
)
def quality_control(measurements: list) -> dict:
    return analyze_quality(measurements)
```

## ⚙️ Configuration Parameters

### Core Parameters

#### `domain: Optional[str] = None`
Specifies the industry domain for specialized intelligence.

**Available Domains**:
- `"financial_services"` - Banking, credit, compliance
- `"manufacturing"` - Quality control, process optimization
- `"healthcare"` - HIPAA compliance, clinical validation
- `"building_management"` - HVAC, energy optimization
- `"llm_optimization"` - LLM performance tuning

**Example**:
```dana
@poet(domain="healthcare")
def patient_data_processor(medical_records: dict) -> dict:
    return process_patient_data(medical_records)
    # Automatic: HIPAA compliance, clinical validation
```

#### `enable_training: bool = True`
Controls whether the T-stage learning algorithms are active.

**When to Enable**:
- ✅ Production systems (recommended)
- ✅ Long-running applications
- ✅ Functions called frequently (>10 times)

**When to Disable**:
- ❌ One-time scripts
- ❌ Development testing
- ❌ Functions with highly variable behavior

**Example**:
```dana
# Enable learning for production
@poet(enable_training=true)
def production_function(data: dict) -> dict:
    return process_data(data)

# Disable learning for testing
@poet(enable_training=false)
def test_function(data: dict) -> dict:
    return process_data(data)
```

#### `learning_algorithm: str = "statistical"`
Selects the learning algorithm for parameter optimization.

**Options**:
- `"statistical"` - Advanced statistical learning (recommended)
- `"heuristic"` - Simple rule-based learning

**Statistical Learning Features**:
- Gradient-based optimization
- Exponential weighted moving averages
- Thompson sampling
- Adaptive learning rates
- Convergence detection

**Heuristic Learning Features**:
- Simple success/failure tracking
- Linear parameter adjustments
- Basic moving averages

**Example**:
```dana
# Production: Use statistical learning
@poet(learning_algorithm="statistical")
def production_api(request: dict) -> dict:
    return call_external_service(request)

# Development: Use heuristic learning for faster iteration
@poet(learning_algorithm="heuristic")  
def dev_function(data: dict) -> dict:
    return experimental_processing(data)
```

### Performance Parameters

#### `timeout: Optional[float] = None`
Maximum execution time in seconds. If `None`, POET learns optimal timeout.

**Guidelines**:
- Start with `None` to let POET learn optimal values
- Set explicitly for strict SLA requirements
- Consider function complexity and external dependencies

**Example**:
```dana
# Auto-optimize timeout
@poet()  # timeout=None (default)
def adaptive_function(data: dict) -> dict:
    return process_with_variable_time(data)

# Fixed timeout for SLA compliance
@poet(timeout=5.0)
def sla_critical_function(request: dict) -> dict:
    return fast_processing_required(request)

# Longer timeout for complex operations
@poet(timeout=60.0)
def complex_analysis(dataset: list) -> dict:
    return deep_analysis(dataset)
```

#### `retries: int = 3`
Number of retry attempts for failed executions.

**Guidelines**:
- Default `3` works for most scenarios
- Increase for unreliable external services
- Decrease for expensive operations
- POET optimizes retry patterns over time

**Example**:
```dana
# Standard retry logic
@poet(retries=3)
def standard_function(data: dict) -> dict:
    return reliable_operation(data)

# High-reliability external API
@poet(retries=7)
def external_api_call(request: dict) -> dict:
    return call_unreliable_service(request)

# Expensive operation - minimal retries
@poet(retries=1)
def expensive_computation(large_dataset: list) -> dict:
    return compute_intensive_analysis(large_dataset)
```

#### `quality_threshold: float = 0.8`
Minimum acceptable output quality score (0.0 to 1.0).

**Guidelines**:
- `0.8` is suitable for most applications
- Increase for critical systems requiring high accuracy
- Decrease for experimental or exploratory functions

**Example**:
```dana
# Standard quality requirements
@poet(quality_threshold=0.8)
def standard_analysis(data: dict) -> dict:
    return general_analysis(data)

# High-accuracy requirements
@poet(quality_threshold=0.95)
def critical_diagnosis(medical_data: dict) -> dict:
    return medical_diagnosis(medical_data)

# Exploratory analysis - lower threshold
@poet(quality_threshold=0.6)
def experimental_feature(data: dict) -> dict:
    return try_new_algorithm(data)
```

### Learning Parameters

#### `learning_rate: float = 0.1`
Controls how quickly learning algorithms adapt parameters.

**Guidelines**:
- `0.1` (default) balances stability and adaptation speed
- Increase (`0.2-0.5`) for rapidly changing environments
- Decrease (`0.05-0.01`) for stable, production systems

**Example**:
```dana
# Fast adaptation for dynamic environments
@poet(learning_rate=0.3)
def dynamic_market_analysis(market_data: dict) -> dict:
    return analyze_volatile_market(market_data)

# Stable learning for production systems
@poet(learning_rate=0.05)
def stable_production_service(request: dict) -> dict:
    return process_standard_request(request)
```

#### `convergence_threshold: float = 0.005`
Threshold for detecting parameter convergence (stability).

**Guidelines**:
- Lower values require more stable convergence
- Higher values allow faster convergence detection
- Affects when learning switches from exploration to exploitation

**Example**:
```dana
# Strict convergence requirements
@poet(convergence_threshold=0.001)
def precision_system(data: dict) -> dict:
    return high_precision_processing(data)

# Faster convergence for agile development
@poet(convergence_threshold=0.01)
def development_function(data: dict) -> dict:
    return iterative_processing(data)
```

## 🏗️ Environment-Specific Configurations

### Development Environment
Focus on fast iteration and debugging.

```dana
@poet(
    enable_training=false,        # Disable learning for consistent behavior
    timeout=5.0,                 # Short timeout for quick feedback
    retries=1,                   # Minimal retries to surface issues quickly
    learning_algorithm="heuristic"  # Simple learning when enabled
)
def dev_function(data: dict) -> dict:
    return experimental_logic(data)
```

### Testing Environment
Balance realistic behavior with test repeatability.

```dana
@poet(
    enable_training=true,         # Enable learning to test learning behavior
    timeout=10.0,                # Moderate timeout for test reliability
    retries=2,                   # Limited retries for faster test execution
    learning_algorithm="heuristic", # Predictable learning behavior
    learning_rate=0.2            # Faster learning for test iteration
)
def test_function(data: dict) -> dict:
    return production_like_logic(data)
```

### Staging Environment
Mirror production settings with monitoring.

```dana
@poet(
    enable_training=true,         # Full learning enabled
    timeout=20.0,                # Production-like timeout
    retries=3,                   # Standard retry behavior
    learning_algorithm="statistical", # Production learning algorithm
    quality_threshold=0.85       # Slightly relaxed for staging
)
def staging_function(data: dict) -> dict:
    return production_logic(data)
```

### Production Environment
Optimized for reliability and performance.

```dana
@poet(
    domain="your_industry",       # Domain expertise
    enable_training=true,         # Continuous improvement
    timeout=30.0,                # Conservative timeout
    retries=5,                   # Robust retry logic
    learning_algorithm="statistical", # Advanced learning
    quality_threshold=0.9,       # High quality requirements
    learning_rate=0.05,          # Stable learning
    convergence_threshold=0.002  # Strict convergence
)
def production_function(data: dict) -> dict:
    return mission_critical_logic(data)
```

## 🏭 Industry-Specific Configurations

### Financial Services
```dana
@poet(
    domain="financial_services",
    timeout=15.0,                # Quick response for customer-facing systems
    retries=5,                   # High reliability for financial data
    quality_threshold=0.95,      # High accuracy for financial decisions
    enable_training=true,        # Continuous compliance optimization
    learning_algorithm="statistical"
)
def financial_risk_assessment(application: dict) -> dict:
    return assess_credit_risk(application)
    # Automatic: FCRA compliance, audit trails, risk thresholds
```

### Manufacturing
```dana
@poet(
    domain="manufacturing",
    timeout=10.0,                # Real-time process control
    retries=3,                   # Balance reliability with timing
    quality_threshold=0.9,       # High quality for safety
    enable_training=true,        # Process optimization
    learning_rate=0.1           # Balanced adaptation for process stability
)
def quality_control_check(measurements: list) -> dict:
    return analyze_product_quality(measurements)
    # Automatic: Statistical process control, defect detection
```

### Healthcare
```dana
@poet(
    domain="healthcare",
    timeout=20.0,                # Allow time for thorough analysis
    retries=7,                   # High reliability for patient safety
    quality_threshold=0.95,      # Critical accuracy for medical decisions
    enable_training=true,        # Continuous clinical optimization
    learning_rate=0.05          # Conservative learning for safety
)
def patient_diagnosis_support(medical_data: dict) -> dict:
    return analyze_patient_condition(medical_data)
    # Automatic: HIPAA compliance, clinical validation
```

## 🔧 Advanced Configuration Patterns

### High-Frequency Trading Systems
```dana
@poet(
    domain="financial_services",
    timeout=0.1,                 # Ultra-low latency requirement
    retries=0,                   # No retries - speed critical
    quality_threshold=0.99,      # Extremely high accuracy
    enable_training=true,        # Continuous optimization
    learning_rate=0.3,          # Fast adaptation to market changes
    convergence_threshold=0.001  # Precise parameter stability
)
def high_frequency_trading(market_data: dict) -> dict:
    return execute_trade_decision(market_data)
```

### Batch Processing Systems
```dana
@poet(
    timeout=300.0,               # Long timeout for batch processing
    retries=2,                   # Limited retries for large batches
    quality_threshold=0.85,      # Balanced quality for bulk processing
    enable_training=true,        # Optimize batch performance
    learning_rate=0.05,         # Stable learning for consistent batches
    learning_algorithm="statistical"
)
def batch_data_processor(batch: list) -> dict:
    return process_large_batch(batch)
```

### Real-Time Analytics
```dana
@poet(
    domain="llm_optimization",
    timeout=2.0,                 # Fast response for real-time queries
    retries=1,                   # Minimal retries for speed
    quality_threshold=0.8,       # Balanced quality vs speed
    enable_training=true,        # Optimize for query patterns
    learning_rate=0.2           # Adapt to changing query patterns
)
def real_time_analytics(query: dict) -> dict:
    return generate_insights(query)
```

## 📊 Monitoring and Debugging Configuration

### Enable Comprehensive Monitoring
```dana
@poet(
    domain="your_domain",
    enable_training=true,
    # Monitoring configuration
    enable_detailed_logging=true,
    performance_monitoring=true,
    learning_metrics_collection=true
)
def monitored_function(data: dict) -> dict:
    return process_with_monitoring(data)

# Check learning status
status = monitored_function.get_learning_status()
log(f"Learning effectiveness: {status['online_learning']['success_rate']}")

# Get optimization recommendations
recommendations = monitored_function.get_learning_recommendations()
for rec in recommendations:
    log(rec)
```

### A/B Testing Configuration
```dana
# Configuration A: Conservative
@poet(
    timeout=20.0,
    retries=3,
    learning_rate=0.05
)
def conservative_function(data: dict) -> dict:
    return process_conservatively(data)

# Configuration B: Aggressive
@poet(
    timeout=10.0,
    retries=5,
    learning_rate=0.2
)
def aggressive_function(data: dict) -> dict:
    return process_aggressively(data)
```

## 🎛️ Dynamic Configuration

### Runtime Configuration Updates
```dana
# Initial configuration
@poet(domain="financial_services")
def adaptive_function(data: dict) -> dict:
    return process_financial_data(data)

# Update configuration based on conditions
if is_peak_hours():
    adaptive_function.update_config({
        "timeout": 5.0,
        "retries": 7,
        "learning_rate": 0.3
    })
else:
    adaptive_function.update_config({
        "timeout": 15.0,
        "retries": 3,
        "learning_rate": 0.1
    })
```

### Configuration Profiles
```dana
# Define configuration profiles
DEVELOPMENT_CONFIG = {
    "enable_training": false,
    "timeout": 5.0,
    "retries": 1,
    "learning_algorithm": "heuristic"
}

PRODUCTION_CONFIG = {
    "enable_training": true,
    "timeout": 30.0,
    "retries": 5,
    "learning_algorithm": "statistical",
    "quality_threshold": 0.9
}

# Apply profile based on environment
config = PRODUCTION_CONFIG if is_production() else DEVELOPMENT_CONFIG

@poet(**config)
def environment_aware_function(data: dict) -> dict:
    return process_data(data)
```

## 🚨 Common Configuration Issues

### Issue: Learning Not Converging
**Symptoms**: Parameters keep changing, no stable optimization
**Solutions**:
```dana
# Reduce learning rate for more stable convergence
@poet(learning_rate=0.02)

# Tighten convergence threshold
@poet(convergence_threshold=0.001)

# Switch to statistical learning
@poet(learning_algorithm="statistical")
```

### Issue: Function Timing Out Frequently
**Symptoms**: High timeout rate, poor performance
**Solutions**:
```dana
# Increase timeout and let POET optimize
@poet(timeout=60.0)

# Increase retries for better reliability
@poet(retries=7)

# Enable training to learn optimal timeout
@poet(enable_training=true)
```

### Issue: Quality Issues
**Symptoms**: Poor output quality, validation failures
**Solutions**:
```dana
# Increase quality threshold
@poet(quality_threshold=0.95)

# Add domain expertise
@poet(domain="your_industry")

# Enable training for quality optimization
@poet(enable_training=true)
```

## 🎯 Best Practices

### 1. Start Simple, Optimize Later
```dana
# Start with defaults
@poet()
def new_function(data: dict) -> dict:
    return process_data(data)

# Add domain expertise when available
@poet(domain="financial_services")

# Fine-tune based on monitoring data
@poet(
    domain="financial_services",
    timeout=15.0,  # Based on performance data
    quality_threshold=0.9  # Based on business requirements
)
```

### 2. Use Environment-Specific Profiles
```dana
# Create reusable configuration profiles
from dana.frameworks.poet.config import EnvironmentProfile

dev_profile = EnvironmentProfile.development()
prod_profile = EnvironmentProfile.production()

@poet(**prod_profile.for_domain("financial_services"))
def production_function(data: dict) -> dict:
    return process_data(data)
```

### 3. Monitor and Iterate
```dana
@poet(enable_training=true, domain="your_domain")
def monitored_function(data: dict) -> dict:
    return process_data(data)

# Regular monitoring
def check_performance():
    status = monitored_function.get_learning_status()
    if status['online_learning']['success_rate'] < 0.8:
        log("Performance degradation detected - investigating")
        recommendations = monitored_function.get_learning_recommendations()
        for rec in recommendations:
            log(f"Recommendation: {rec}")
```

---

**Next Steps**: Explore **[API Reference](api-reference.md)** for detailed parameter documentation or Production Deployment for scaling considerations *(Coming Soon)*.
