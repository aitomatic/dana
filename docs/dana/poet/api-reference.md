# POET API Reference

Complete technical reference for POET (Perceive → Operate → Enforce → Train) functions, domain plugins, and configuration options.

## Core Decorators

### `@poet()`

The main decorator that enhances simple functions with enterprise capabilities through domain intelligence and runtime infrastructure.

#### Signature
```python
@poet(
    domain: Optional[str] = None,
    retries: int = 3,
    timeout: float = 30.0,
    enable_training: bool = False,
    collect_metrics: bool = True
) -> Callable
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | `Optional[str]` | `None` | Domain plugin for industry-specific intelligence |
| `retries` | `int` | `3` | Number of retry attempts on failure |
| `timeout` | `float` | `30.0` | Maximum execution time in seconds |
| `enable_training` | `bool` | `False` | Enable T-stage parameter learning |
| `collect_metrics` | `bool` | `True` | Enable performance monitoring |

#### Example Usage
```dana
# Basic reliability enhancement
@poet(retries=3, timeout=10.0)
def simple_function(input: str) -> str:
    return reason(input)

# Domain-specific intelligence
@poet(domain="financial_services", retries=5)
def assess_credit_risk(score: int, income: float, debt_ratio: float) -> str:
    if score >= 750 and debt_ratio <= 0.3:
        return "approved"
    else:
        return "declined"

# With parameter learning
@poet(domain="llm_optimization", enable_training=true)
def enhanced_reasoning(prompt: str) -> str:
    return reason(prompt)
```

## What POET Runtime Provides

### POEExecutor Architecture
POET wraps your simple functions with a 4-stage pipeline:

1. **P (Perceive)**: Domain plugin processes inputs
   - `domain_plugin.process_inputs(args, kwargs)`
   - Input normalization and validation
   - Data format conversion

2. **O (Operate)**: Your function + reliability infrastructure
   - Automatic retry logic with exponential backoff
   - Timeout handling and monitoring
   - Error recovery and logging

3. **E (Enforce)**: Domain plugin validates outputs
   - `domain_plugin.validate_output(result, input_data)`
   - Compliance checking and audit trails
   - Output quality assurance

4. **T (Train)**: Optional parameter optimization
   - Learn optimal retry counts and timeouts
   - Track execution patterns and success rates
   - Adapt parameters based on performance

## Domain Plugins

POET includes 4 production-ready domain plugins that provide industry-specific intelligence:

### `"financial_services"`
Financial services compliance and data normalization.

**Input Processing (P-Stage)**:
- Credit score normalization: `"excellent"` → 780, `"good"` → 720, `"fair"` → 650
- Income normalization: `"$50K"` → 50000.0, `"2.5M"` → 2500000.0
- Ratio normalization: `"25%"` → 0.25, `"0.28"` → 0.28
- Employment normalization: `"2.5 years"` → 2.5, `"30 months"` → 2.5

**Output Validation (E-Stage)**:
- FCRA compliance checking
- Credit decision audit trail generation
- Risk threshold validation
- Regulatory reporting requirements

**Implementation**: `opendxa/dana/poet/domains/financial_services.py`

```dana
@poet(domain="financial_services")
def assess_credit_risk(score: int, income: float, debt_ratio: float) -> str:
    # Simple business logic - POET adds enterprise capabilities
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"

# Handles varied input formats automatically:
result1 = assess_credit_risk(720, 65000.0, 0.28)      # Standard
result2 = assess_credit_risk("good", "$65K", "28%")   # Normalized by POET
```

### `"building_management"`
HVAC control and building automation intelligence.

**Input Processing (P-Stage)**:
- Temperature unit conversion and validation
- Occupancy data processing
- Equipment status analysis
- Energy cost tier processing

**Output Validation (E-Stage)**:
- Temperature range safety checks (prevent equipment damage)
- Energy efficiency validation
- Equipment protection protocols
- Comfort zone compliance

**Implementation**: `opendxa/dana/poet/domains/building_management.py`

```dana
@poet(domain="building_management")
def set_hvac_temperature(target: float, current: float, occupancy: int) -> dict:
    # Simple control logic - POET adds safety and optimization
    if occupancy == 0:
        return {"temperature": target - 2, "mode": "eco"}
    else:
        return {"temperature": target, "mode": "normal"}
```

### `"semiconductor"`
Semiconductor manufacturing process control.

**Input Processing (P-Stage)**:
- Process parameter validation
- Equipment status monitoring
- Recipe parameter normalization
- Safety threshold checking

**Output Validation (E-Stage)**:
- Statistical process control (SPC) monitoring
- Equipment protection interlocks
- Yield optimization validation
- Process variation detection

**Implementation**: `opendxa/dana/poet/domains/semiconductor.py`

```dana
@poet(domain="semiconductor")
def control_process(temperature: float, pressure: float, flow_rate: float) -> dict:
    # Simple process control - POET adds safety and SPC monitoring
    return {"status": "normal", "adjustments": {}}
```

### `"llm_optimization"`
Large Language Model performance optimization.

**Input Processing (P-Stage)**:
- Prompt length analysis and optimization
- Context formatting for better performance
- Request parameter optimization
- Cost estimation and tracking

**Output Validation (E-Stage)**:
- Response quality validation
- Length and completeness checking
- Cost optimization reporting
- Performance metric tracking

**Implementation**: `opendxa/dana/poet/domains/llm_optimization.py`

```dana
@poet(domain="llm_optimization")
def enhanced_reasoning(prompt: str) -> str:
    # Simple reasoning - POET adds prompt optimization and quality validation
    return reason(prompt)
```

## Configuration Patterns

### Basic Reliability
```dana
@poet(retries=3, timeout=30.0)
def reliable_function(input: str) -> str:
    return process_data(input)
```

### Domain Intelligence
```dana
@poet(domain="financial_services")
def credit_function(score, income, debt_ratio) -> str:
    return "approved" if score >= 700 else "declined"
```

### Combined Configuration
```dana
@poet(domain="building_management", retries=2, timeout=15.0)
def hvac_function(target, current, occupancy) -> dict:
    return {"temperature": target}
```

### With Learning
```dana
@poet(domain="llm_optimization", enable_training=true, retries=2)
def learning_function(prompt: str) -> str:
    return reason(prompt)
```

## Runtime Implementation

### POEExecutor Class
Located in `opendxa/dana/poet/mvp_poet.py`

```python
class POEExecutor(Loggable):
    def __init__(self, config: POEConfig):
        self.config = config
        self.domain_plugin = self._load_domain_plugin()
        self.parameters = self._load_parameters() if config.enable_training else None
    
    def __call__(self, func: Callable) -> Callable:
        # Wraps function with POE pipeline
        pass
    
    def _perceive(self, args, kwargs) -> Dict[str, Any]:
        # P: Domain plugin input processing
        if self.domain_plugin:
            return self.domain_plugin.process_inputs(args, kwargs)
        return {"args": args, "kwargs": kwargs}
    
    def _operate_with_retry(self, func, perceived_input) -> Dict[str, Any]:
        # O: Execute with retry logic and timeout handling
        pass
    
    def _enforce(self, operation_result, perceived_input) -> Any:
        # E: Domain plugin output validation  
        if self.domain_plugin:
            return self.domain_plugin.validate_output(operation_result, perceived_input)
        return operation_result["result"]
```

### Domain Plugin Interface
```python
class DomainPlugin:
    def process_inputs(self, args: Tuple, kwargs: Dict) -> Dict[str, Any]:
        """P-stage: Normalize and validate inputs"""
        pass
    
    def validate_output(self, operation_result: Dict, processed_input: Dict) -> Any:
        """E-stage: Validate output and add compliance"""
        pass
```

## Performance and Metrics

### Execution Metrics
POET automatically tracks:
- **Response Time**: Function execution duration
- **Success Rate**: Percentage of successful executions  
- **Retry Patterns**: When and why retries occur
- **Domain Plugin Overhead**: P/E stage processing time (<10ms typical)

### Training Metrics (when `enable_training=true`)
- **Parameter Convergence**: How retry/timeout values stabilize
- **Learning Effectiveness**: Performance improvement over time
- **Optimization Success**: Parameter adjustment success rate

### Getting Metrics
```dana
# Metrics are automatically collected
@poet(domain="financial_services", collect_metrics=true)
def monitored_function(input: str) -> str:
    return process_input(input)

# Access via POEExecutor (implementation dependent)
# Future: metrics.get_function_stats("monitored_function")
```

## Error Handling

### POE Error Types
```python
from opendxa.dana.poet.errors import (
    POEError,           # Base POE error
    PerceiveError,      # P-stage errors
    OperateError,       # O-stage errors (includes retries exhausted)
    EnforceError,       # E-stage validation errors
    TrainError,         # T-stage learning errors
    DomainPluginError   # Domain plugin specific errors
)
```

### Error Context
POET provides rich error context:
- Function name and domain
- Execution attempt number
- Stage where error occurred (P/O/E/T)
- Domain plugin information
- Execution time and parameters

## Best Practices

### Function Design
```dana
# ✅ Good: Simple, focused business logic
@poet(domain="financial_services")
def assess_risk(score: int, income: float, debt_ratio: float) -> str:
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"

# ❌ Avoid: Complex logic that POET domain plugins should handle
@poet(domain="financial_services")
def complex_assessment(raw_data: str) -> dict:
    # Don't manually parse credit scores, handle compliance, etc.
    # Let POET domain plugins do this work
    pass
```

### Configuration
```dana
# ✅ Good: Use domain plugins for industry intelligence
@poet(domain="building_management", retries=2)

# ✅ Good: Enable training for learning systems  
@poet(domain="llm_optimization", enable_training=true)

# ✅ Good: Disable training for stable production systems
@poet(domain="financial_services", enable_training=false)
```

### Error Handling
```dana
# Functions can focus on business logic
@poet(domain="financial_services")
def simple_credit_check(score: int) -> str:
    # No need for complex error handling - POET provides this
    return "good" if score >= 650 else "poor"
```

## Migration Guide

### From Enhanced POET
```dana
# Old (complex decorator)
@enhanced_poet(
    domain="financial_services",
    enable_training=true,
    learning_algorithm="statistical",
    timeout=30.0
)

# New (simplified)
@poet(
    domain="financial_services",
    enable_training=true,
    timeout=30.0
)
```

### From Manual Implementation
```dana
# Old (manual enterprise logic)
def manual_credit_assessment(score, income, debt_ratio):
    # Manual normalization
    if isinstance(score, str):
        score = normalize_credit_score(score)
    # Manual validation
    validate_inputs(score, income, debt_ratio)
    # Business logic
    result = assess_credit(score, income, debt_ratio)
    # Manual compliance
    add_audit_trail(result)
    return result

# New (POET handles enterprise logic)
@poet(domain="financial_services")
def simple_credit_assessment(score: int, income: float, debt_ratio: float) -> str:
    # Just business logic - POET handles the rest
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"
```

---

**Next**: Explore **[Domain Plugin Development](../../.implementation/poet/04_poet_plugin_architecture.md)** to create custom industry intelligence. 