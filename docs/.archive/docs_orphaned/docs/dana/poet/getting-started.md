# Getting Started with POET

This guide shows you how to write simple business functions that POET automatically transforms into enterprise-grade systems with domain intelligence, reliability, and compliance.

## 🎯 What You'll Build

By the end of this guide, you'll understand:
- ✅ How to write simple functions that POET enhances with enterprise capabilities
- ✅ How domain plugins automatically add industry-specific intelligence
- ✅ How POET's runtime provides reliability without additional code
- ✅ The architecture that separates simple business logic from enterprise infrastructure

**Estimated Time**: 10-15 minutes

## 📋 Prerequisites

- **Dana Environment**: Dana installed with POET enabled
- **Dana Knowledge**: Basic familiarity with Dana language syntax

### Quick Environment Check
```bash
# Verify POET is available
uv run python -c "from dana.frameworks.poet import poet; print('POET ready!')"

# Test Dana execution
uv run python -m dana.core.repl.dana
```

## 🏗️ Understanding POET Architecture

POET transforms **simple functions** into **enterprise systems** through runtime enhancement:

### What Engineers Write (Simple)
```dana
@poet(domain="financial_services")
def assess_credit_risk(credit_score: int, income: float, debt_ratio: float) -> str:
    # 5 lines of core business logic
    if credit_score >= 750 and debt_ratio <= 0.3:
        return "approved"
    elif credit_score >= 650 and debt_ratio <= 0.45:
        return "conditional"
    else:
        return "declined"
```

### What POET Runtime Adds Automatically
- **P (Perceive)**: Domain plugin normalizes inputs ("excellent"→780, "$50K"→50000)
- **O (Operate)**: Retry logic, timeout handling, error recovery
- **E (Enforce)**: Domain plugin adds compliance (FCRA validation, audit trails)
- **T (Train)**: Optional parameter learning (optimize retries/timeouts)

## 🚀 Your First POET Function

### Step 1: Basic Function Enhancement

Start with the simplest possible POET function:

```dana
# basic_poet_example.na

# Simple function with automatic reliability
@poet(retries=3, timeout=10.0)
def analyze_data(input_text: str) -> str:
    """Simple analysis function enhanced by POET"""
    return reason(f"Analyze this data: {input_text}")

# Test the function
result = analyze_data("quarterly sales figures")
log(f"Analysis result: {result}")

# POET automatically provided:
# - 3 retry attempts on failure
# - 10 second timeout protection
# - Automatic error recovery
# - Performance monitoring
```

**What POET Added**: Reliability infrastructure around your 2-line function.

### Step 2: Domain Intelligence

Add industry-specific intelligence through domain plugins:

```dana
# financial_domain_example.na

# Financial services domain intelligence
@poet(domain="financial_services", retries=3)
def assess_credit_risk(credit_score: int, annual_income: float, debt_ratio: float) -> str:
    """Simple credit assessment - POET adds enterprise capabilities"""
    
    # Your simple business logic (what you focus on)
    if credit_score >= 750 and debt_ratio <= 0.3:
        return "approved"
    elif credit_score >= 650 and debt_ratio <= 0.45:
        return "conditional"
    else:
        return "declined"

# Test with normalized inputs
result1 = assess_credit_risk(720, 65000.0, 0.28)
log(f"Standard inputs: {result1}")

# Test with varied formats - POET normalizes automatically
result2 = assess_credit_risk("good", "$50K", "25%")  
log(f"Mixed formats: {result2}")

# POET financial_services plugin automatically:
# - Normalized "good" credit score to numeric value
# - Converted "$50K" to 50000.0
# - Converted "25%" to 0.25 decimal
# - Added FCRA compliance validation
# - Generated audit trail
```

### Step 3: Building Management Domain

See how different domains provide different intelligence:

```dana
# building_domain_example.na

# Building management domain intelligence
@poet(domain="building_management", timeout=5.0)
def set_hvac_temperature(target_temp: float, current_temp: float, occupancy: int) -> dict:
    """Simple HVAC control - POET adds equipment protection"""
    
    # Your simple control logic
    if occupancy == 0:
        return {"temperature": target_temp - 3, "mode": "eco"}
    elif abs(target_temp - current_temp) > 5:
        return {"temperature": target_temp, "mode": "fast"}
    else:
        return {"temperature": target_temp, "mode": "normal"}

# Test HVAC control
control_result = set_hvac_temperature(72.0, 75.0, 0)
log(f"HVAC control: {control_result}")

# POET building_management plugin automatically:
# - Added equipment safety interlocks
# - Applied energy optimization algorithms
# - Implemented temperature range validation
# - Added occupancy-aware optimizations
```

### Step 4: Learning and Optimization

Enable optional parameter learning:

```dana
# learning_example.na

# LLM optimization with learning
@poet(domain="llm_optimization", enable_training=true, retries=2)
def enhanced_reasoning(prompt: str) -> str:
    """Simple reasoning enhanced with learning"""
    return reason(prompt)

# Make multiple calls - POET learns optimal parameters
test_prompts = [
    "What is machine learning?",
    "Explain neural networks simply",
    "How does backpropagation work?"
]

for prompt in test_prompts:
    result = enhanced_reasoning(prompt)
    log(f"Q: {prompt}")
    log(f"A: {result}")
    log("---")

# POET automatically learns:
# - Optimal retry counts based on success patterns
# - Best timeout values for different prompt types
# - Prompt optimization strategies
# - Response quality validation patterns
```

## 🧠 Domain Plugins Available

POET includes production-ready domain plugins:

### 1. Financial Services (`financial_services`)
```dana
@poet(domain="financial_services")
def simple_credit_function(score, income, debt_ratio) -> str:
    # Your simple logic
    return "approved" if score >= 700 else "declined"

# Plugin automatically adds:
# - Input normalization: "$50K"→50000, "excellent"→780, "25%"→0.25
# - FCRA compliance validation
# - Audit trail generation
# - Credit score range validation (300-850)
```

### 2. Building Management (`building_management`) 
```dana
@poet(domain="building_management")
def simple_hvac_function(target, current, occupancy) -> dict:
    # Your simple logic
    return {"temp": target, "mode": "normal"}

# Plugin automatically adds:
# - Equipment safety interlocks
# - Temperature range validation (prevent equipment damage)
# - Energy optimization algorithms
# - Occupancy-aware adjustments
```

### 3. LLM Optimization (`llm_optimization`)
```dana
@poet(domain="llm_optimization")
def simple_reasoning_function(prompt) -> str:
    # Your simple logic
    return reason(prompt)

# Plugin automatically adds:
# - Prompt optimization based on length and complexity
# - Response quality validation
# - Cost optimization strategies
# - Performance monitoring
```

### 4. Semiconductor Manufacturing (`semiconductor`)
```dana
@poet(domain="semiconductor")
def simple_process_function(temperature, pressure, flow_rate) -> dict:
    # Your simple logic
    return {"status": "normal", "yield": 0.95}

# Plugin automatically adds:
# - Process parameter validation
# - Equipment safety interlocks
# - Statistical process control (SPC) monitoring
# - Equipment protection protocols
```

## 📊 What POET Runtime Provides

### POEExecutor Implementation
Located in `dana/frameworks/poet/`, the runtime provides:

1. **P (Perceive)**: `domain_plugin.process_inputs(args, kwargs)`
   - Normalizes varied input formats
   - Validates data ranges and types
   - Applies domain-specific preprocessing

2. **O (Operate)**: Your function + reliability infrastructure
   - Automatic retry logic with exponential backoff
   - Timeout handling and monitoring
   - Error recovery and logging

3. **E (Enforce)**: `domain_plugin.validate_output(result, input_data)`
   - Industry compliance validation
   - Audit trail generation
   - Output quality assurance

4. **T (Train)**: Optional parameter optimization
   - Learn optimal retry counts and timeouts
   - Track success/failure patterns
   - Adjust parameters based on execution history

## 🔧 Configuration Patterns

### Basic Reliability
```dana
@poet(retries=3, timeout=30.0)              # Just reliability
@poet(domain="your_industry")               # Domain intelligence
@poet(domain="financial_services", retries=5) # Domain + custom reliability
```

### With Learning
```dana
@poet(domain="llm_optimization", enable_training=true)  # Learn parameters
@poet(enable_training=true, retries=2)                  # Learn without domain
```

### Production Settings
```dana
@poet(
    domain="financial_services",
    retries=3,
    timeout=30.0,
    enable_training=false,    # Disable learning in production for stability
    collect_metrics=true      # Enable performance monitoring
)
```

## 🧪 Testing Your POET Functions

### Quick Test Script
```dana
# test_poet_functions.na

# Test different domain enhancements
@poet(domain="financial_services")
def test_financial(score: int, income: float, debt: float) -> str:
    return "approved" if score >= 700 and debt <= 0.3 else "declined"

@poet(domain="building_management") 
def test_building(target: float, current: float) -> dict:
    return {"temp": target, "mode": "normal"}

# Test with various input formats
log("=== Financial Services Domain ===")
log(f"Numeric inputs: {test_financial(720, 65000.0, 0.28)}")
log(f"Mixed formats: {test_financial('good', '$65K', '28%')}")

log("\\n=== Building Management Domain ===")
log(f"HVAC control: {test_building(72.0, 75.0)}")

log("\\n=== POET Benefits ===")
log("✅ Simple functions (5-10 lines)")
log("✅ Automatic enterprise capabilities")
log("✅ Domain intelligence through plugins") 
log("✅ 90% reduction in boilerplate code")
```

## 🎓 Next Steps

### Explore Domain Intelligence
- **[Configuration Guide](configuration.md)** - Complete domain plugin options *(Coming Soon)*
- **[API Reference](api-reference.md)** - Full decorator API *(Coming Soon)*
- **[Industry Examples](../../../examples/dana/04_poet_examples/)** - Real-world demonstrations *(Coming Soon)*

### Understand Runtime Architecture
- **POET Implementation** - Technical design *(Coming Soon)*
- **Domain Plugin Development** - Create custom plugins *(Coming Soon)*

### Production Deployment
- **Performance Guide** - Optimization strategies *(Coming Soon)*
- **Monitoring Guide** - Production observability *(Coming Soon)*

---

**Ready for more?** Check out the Industry Examples to see POET transform simple functions into production-grade systems across different domains! *(Coming Soon)*