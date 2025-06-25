# POET Decorators Reference

## Overview

POET decorators provide automatic enhancement for functions with **Perceive-Operate-Enforce-Train** capabilities. This reference covers both Python and Dana decorator usage, configuration options, and integration patterns.

## Quick Reference

| Decorator | Language | Purpose | Example |
|-----------|----------|---------|---------|
| `@poet()` | Python | Enhance Python functions with POET pipeline | `@poet(domain="llm_optimization")` |
| `@poet` | Dana | Enhance Dana functions with POET pipeline | `@poet(domain="financial_services")` |
| `poet()` | Dana | Runtime enhancement function | `poet("reason", ["prompt"])` |

## Python `@poet()` Decorator

### Basic Syntax

```python
from opendxa.dana.poet import poet

@poet(domain="llm_optimization", timeout=30.0, retries=3, enable_training=True)
def my_enhanced_function(prompt: str, context: SandboxContext) -> str:
    """Your function gets automatic POET enhancement."""
    # Your business logic here
    return process_prompt(prompt)
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | `str` | `None` | Domain specialization for intelligent processing |
| `timeout` | `float` | `30.0` | Maximum execution time in seconds |
| `retries` | `int` | `3` | Number of retry attempts on failure |
| `enable_training` | `bool` | `True` | Whether to learn from execution patterns |
| `collect_metrics` | `bool` | `True` | Whether to collect performance metrics |

### Available Domains

| Domain | Purpose | Optimizations |
|--------|---------|---------------|
| `"llm_optimization"` | LLM prompt optimization | Enhanced prompting, cost optimization |
| `"financial_services"` | Financial analysis | Risk assessment, compliance validation |
| `"building_management"` | HVAC and facility control | Energy optimization, comfort balancing |
| `"semiconductor"` | Manufacturing processes | Yield optimization, quality control |
| `"healthcare"` | Medical applications | Safety validation, evidence-based reasoning |
| `"manufacturing"` | Industrial processes | Efficiency optimization, quality assurance |
| `"logistics"` | Supply chain operations | Route optimization, resource allocation |

### Python Examples

#### 1. Enhanced LLM Function

```python
from opendxa.dana.poet import poet
from opendxa.dana.sandbox.sandbox_context import SandboxContext

@poet(domain="llm_optimization", timeout=30.0, retries=3)
def enhanced_reasoning(prompt: str, context: SandboxContext) -> str:
    """
    Enhanced reasoning with automatic optimization.
    
    POET automatically provides:
    - Prompt optimization for better LLM responses
    - Retry logic on failures
    - Output validation and quality checks
    - Performance monitoring and learning
    """
    # Your core reasoning logic
    return llm_resource.generate(prompt)

# Usage - POET handles optimization automatically
result = enhanced_reasoning("Analyze market trends", context)
```

#### 2. Financial Analysis Function

```python
@poet(domain="financial_services", timeout=45.0, retries=2)
def assess_portfolio_risk(
    portfolio_data: dict, 
    context: SandboxContext
) -> dict:
    """
    Assess financial portfolio risk with regulatory compliance.
    
    POET provides:
    - Financial domain intelligence
    - Regulatory compliance validation  
    - Risk calculation optimization
    - Audit trail generation
    """
    # Your risk assessment logic
    risk_score = calculate_risk_metrics(portfolio_data)
    return {"risk_score": risk_score, "compliance_status": "approved"}

# Usage
portfolio = {"stocks": 0.7, "bonds": 0.2, "cash": 0.1}
risk_assessment = assess_portfolio_risk(portfolio, context)
```

#### 3. Building Management Function

```python
@poet(domain="building_management", timeout=20.0, enable_training=True)
def optimize_hvac_settings(
    current_temp: float,
    target_temp: float, 
    occupancy: int,
    context: SandboxContext
) -> dict:
    """
    Optimize HVAC settings for energy efficiency and comfort.
    
    POET provides:
    - Energy optimization algorithms
    - Comfort vs efficiency balancing
    - Occupancy-based adjustments
    - Seasonal learning patterns
    """
    # Your HVAC control logic
    settings = calculate_optimal_hvac(current_temp, target_temp, occupancy)
    return settings

# Usage
hvac_command = optimize_hvac_settings(22.5, 23.0, 45, context)
```

### Error Handling

POET automatically handles common error scenarios:

```python
@poet(domain="llm_optimization", retries=3)
def robust_analysis(data: str, context: SandboxContext) -> dict:
    """Function with automatic error handling and retries."""
    
    # If this fails, POET automatically:
    # 1. Logs the failure with context
    # 2. Retries up to 3 times
    # 3. Applies domain-specific recovery strategies
    # 4. Returns detailed error information if all attempts fail
    
    if not data.strip():
        raise ValueError("Empty input data")
    
    return {"analysis": process_complex_data(data)}
```

## Dana `@poet` Decorator

### Basic Syntax

```dana
# Dana decorator syntax - no parentheses for simple cases
@poet
def simple_enhanced_function(input: str) -> str:
    return input.upper()

# Dana decorator with parameters
@poet(domain="financial_services", timeout=30.0, retries=3)
def financial_analysis(portfolio: dict) -> dict:
    risk_score = calculate_risk(portfolio)
    return {"risk": risk_score, "recommendation": "hold"}
```

### Dana Configuration Examples

#### 1. LLM Optimization

```dana
@poet(domain="llm_optimization", timeout=30.0, retries=3)
def enhanced_reasoning(query: str) -> str:
    # POET automatically optimizes prompts and handles retries
    return reason(f"Provide detailed analysis: {query}")

# Usage
result = enhanced_reasoning("What are the key market trends?")
```

#### 2. Financial Services

```dana
@poet(domain="financial_services", timeout=45.0, enable_training=true)
def assess_credit_risk(
    credit_score: int, 
    annual_income: float, 
    debt_ratio: float
) -> str:
    # POET adds financial domain intelligence and compliance
    if credit_score >= 700 and debt_ratio <= 0.3:
        return "low_risk"
    elif credit_score >= 600 and debt_ratio <= 0.5:
        return "medium_risk"
    else:
        return "high_risk"

# Usage - automatic financial compliance and validation
risk_level = assess_credit_risk(720, 75000.0, 0.25)
```

#### 3. Building Management

```dana
@poet(domain="building_management", timeout=20.0, collect_metrics=true)
def control_hvac_zone(
    current_temp: float,
    setpoint: float,
    occupancy: bool,
    outdoor_temp: float
) -> dict:
    # POET adds energy optimization and comfort balancing
    temp_error = current_temp - setpoint
    
    if abs(temp_error) <= 1.0:
        return {"heating": 0, "cooling": 0, "fan_speed": 20, "mode": "maintain"}
    elif temp_error < -1.0:
        heating_level = min(100, abs(temp_error) * 30)
        return {"heating": heating_level, "cooling": 0, "fan_speed": 60, "mode": "heating"}
    else:
        cooling_level = min(100, temp_error * 30)
        return {"heating": 0, "cooling": cooling_level, "fan_speed": 60, "mode": "cooling"}

# Usage - automatic energy optimization
hvac_settings = control_hvac_zone(22.5, 23.0, true, 18.0)
```

## Runtime `poet()` Function (Dana)

### Syntax

```dana
poet(function_name: str, arguments: list, **config) -> any
```

### Examples

#### 1. Basic Runtime Enhancement

```dana
# Apply POET to any function call at runtime
enhanced_result = poet("reason", ["Analyze customer feedback"])
```

#### 2. Domain-Specific Enhancement

```dana
# Financial domain enhancement
financial_result = poet(
    "calculate_risk", 
    [portfolio_data], 
    domain="financial_services",
    timeout=30.0,
    retries=2
)
```

#### 3. Complex Configuration

```dana
# Full configuration example
result = poet(
    "complex_analysis",
    [large_dataset],
    domain="manufacturing",
    timeout=60.0,
    retries=5,
    enable_training=true,
    collect_metrics=true
)
```

## Best Practices

### 1. Domain Selection

Choose the most specific domain for your use case:

```python
# ✅ Good - specific domain
@poet(domain="financial_services")
def calculate_loan_risk(): pass

# ❌ Less optimal - generic domain  
@poet(domain="llm_optimization")
def calculate_loan_risk(): pass
```

### 2. Timeout Configuration

Set realistic timeouts based on operation complexity:

```python
# ✅ Good - appropriate timeouts
@poet(timeout=10.0)   # Simple operations
@poet(timeout=30.0)   # Standard LLM calls  
@poet(timeout=60.0)   # Complex analysis

# ❌ Too short - may cause premature failures
@poet(timeout=1.0)    # Too short for LLM calls
```

### 3. Retry Strategy

Configure retries based on operation reliability:

```python
# ✅ Good - appropriate retry counts
@poet(retries=3)      # Standard reliability
@poet(retries=1)      # Fast operations, low latency requirements
@poet(retries=5)      # Critical operations, high reliability needs

# ❌ Problematic
@poet(retries=0)      # No error recovery
@poet(retries=10)     # Excessive retries, slow failure recovery
```

### 4. Training and Metrics

Enable learning for production functions:

```python
# ✅ Good - enable learning in production
@poet(enable_training=True, collect_metrics=True)
def production_function(): pass

# ✅ Good - disable learning for testing
@poet(enable_training=False, collect_metrics=False)  
def test_function(): pass
```

## Integration Patterns

### 1. Existing Function Enhancement

```python
# Before - regular function
def analyze_data(data: str) -> dict:
    return {"result": process(data)}

# After - POET-enhanced
@poet(domain="llm_optimization", timeout=30.0, retries=3)
def analyze_data(data: str, context: SandboxContext) -> dict:
    return {"result": process(data)}
```

### 2. Mixed Enhancement Strategies

```python
# Some functions use decorators
@poet(domain="financial_services")
def calculate_risk(data): pass

# Others use runtime enhancement  
def process_data(data):
    # Apply POET only when needed
    if is_complex(data):
        return poet("complex_analysis", [data], domain="manufacturing")
    else:
        return simple_analysis(data)
```

### 3. Conditional Enhancement

```dana
# Dana function with conditional POET usage
def adaptive_processing(data: str, use_poet: bool) -> str:
    if use_poet:
        return poet("enhanced_analysis", [data], domain="llm_optimization")
    else:
        return basic_analysis(data)
```

## Error Handling and Debugging

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `POET decorator error: Unknown parameter 'xyz'` | Invalid parameter name | Use valid parameters: domain, timeout, retries, enable_training, collect_metrics |
| `POET decorator error: Domain must be a string` | Wrong domain type | Use string domain names like "financial_services" |
| `POET decorator error: Domain cannot be empty` | Empty domain string | Provide a valid domain or omit the parameter |
| `POET decorator error: Timeout must be positive` | Negative timeout | Use positive timeout values in seconds |
| `POET decorator error: Retries must be non-negative` | Negative retries | Use 0 or positive integer for retries |

### Debugging Tips

1. **Enable Debug Logging**:
   ```python
   import logging
   logging.getLogger('opendxa.dana.poet').setLevel(logging.DEBUG)
   ```

2. **Check Domain Availability**:
   ```python
   from opendxa.dana.poet.domains import get_available_domains
   print("Available domains:", get_available_domains())
   ```

3. **Validate Configuration**:
   ```python
   from opendxa.dana.poet import POEConfig
   config = POEConfig(domain="financial_services", timeout=30.0)
   print("Configuration valid:", config.is_valid())
   ```

## Performance Considerations

### 1. Overhead

POET adds minimal overhead:
- **Initialization**: ~1-2ms per function call
- **Domain Processing**: ~5-10ms depending on domain complexity  
- **Retry Logic**: Only activates on failures
- **Learning**: Asynchronous, no blocking overhead

### 2. Memory Usage

- **Domain Plugins**: ~50-100KB per domain loaded
- **Metrics Collection**: ~1KB per function execution
- **Learning Data**: Configurable retention policies

### 3. Optimization Tips

```python
# ✅ Good - reuse domain instances
@poet(domain="financial_services")  # Domain loaded once
def func1(): pass

@poet(domain="financial_services")  # Reuses existing domain
def func2(): pass

# ✅ Good - disable features when not needed
@poet(enable_training=False, collect_metrics=False)  # Minimal overhead
def simple_function(): pass
```

## Migration Guide

### From Regular Functions

```python
# Step 1: Add context parameter
def old_function(data: str) -> str:
    return process(data)

def new_function(data: str, context: SandboxContext) -> str:
    return process(data)

# Step 2: Add POET decorator
@poet(domain="appropriate_domain")
def new_function(data: str, context: SandboxContext) -> str:
    return process(data)

# Step 3: Update callers to pass context
result = new_function(data, context)
```

### From Other Enhancement Patterns

```python
# From manual retry logic
def old_function(data):
    for attempt in range(3):
        try:
            return process(data)
        except Exception:
            continue
    raise Exception("All attempts failed")

# To POET enhancement
@poet(retries=3)
def new_function(data, context):
    return process(data)  # POET handles retries automatically
```

## Related Documentation

- [POET Architecture Overview](../../../reference/02_dana_runtime_and_execution/poet_architecture_decisions.md)
- [Domain Plugin Development](../../../design/03_core_capabilities_resources/poet_domain_plugins.md)
- [POET Usage Guide](../poet-usage-guide.md)
- [Dana Syntax Reference](../dana-syntax.md) 