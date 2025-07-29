# POET Primer: Declarative Function Enhancement

**POET** transforms simple functions into enterprise-grade systems through declarative decorators and runtime enhancement.

## 🎯 Core Concept

POET is a **decorator-based framework** that wraps your functions with enterprise capabilities:

```dana
# What you write (simple business logic)
@poet(domain="financial_services")
def assess_credit(score: int, income: float, debt_ratio: float) -> str:
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"

# What POET provides automatically:
# - Input normalization ("excellent"→780, "$50K"→50000)
# - Retry logic and error handling
# - Compliance validation and audit trails
# - Performance monitoring and optimization
```

## 🔄 The POET Pipeline

POET enhances functions through four stages:

### **P: Perceive** (Input Processing)
- **Domain plugins** normalize and validate inputs
- **Examples**: `"excellent"` → 780, `"$50K"` → 50000.0, `"25%"` → 0.25

### **O: Operate** (Execution + Reliability)  
- **Your function** executes with enterprise reliability
- **Automatic**: retries, timeouts, error recovery, monitoring

### **E: Enforce** (Output Validation)
- **Domain plugins** validate outputs and add compliance
- **Examples**: FCRA compliance, safety interlocks, audit trails

### **T: Train** (Optional Learning)
- **Parameter optimization** based on execution patterns
- **Learns**: optimal retry counts, timeout values, success patterns

## 🧩 Domain Intelligence

POET includes production-ready domain plugins:

| Domain | Input Processing | Output Validation |
|--------|------------------|-------------------|
| **financial_services** | Credit score normalization, income parsing | FCRA compliance, audit trails |
| **building_management** | Temperature conversion, equipment status | Safety interlocks, energy validation |
| **llm_optimization** | Prompt optimization, context formatting | Quality validation, cost optimization |
| **semiconductor** | Process validation, recipe parsing | SPC monitoring, equipment protection |

## 🚀 Usage Patterns

### Basic Reliability Enhancement
```dana
@poet(retries=3, timeout=30.0)
def my_function(input: str) -> str:
    return process_data(input)
```

### Domain Intelligence
```dana
@poet(domain="financial_services")
def credit_assessment(score: int, income: float, debt_ratio: float) -> str:
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"
```

### Learning-Enabled Systems
```dana
@poet(domain="llm_optimization", enable_training=true)
def enhanced_reasoning(prompt: str) -> str:
    return reason(prompt)
```

### Production Configuration
```dana
@poet(
    domain="building_management",
    retries=2,
    timeout=15.0,
    enable_training=false,
    collect_metrics=true
)
def hvac_control(target: float, current: float, occupancy: int) -> dict:
    return {"temperature": target, "mode": "normal"}
```

## 🎯 Key Benefits

### For Engineers
- **90% less code**: Focus on business logic only
- **Automatic enterprise capabilities**: Reliability, compliance, monitoring
- **Domain expertise**: Industry intelligence without domain knowledge
- **Consistent patterns**: Same `@poet()` decorator across all domains

### For Operations
- **Built-in reliability**: Retry logic, timeout handling, error recovery
- **Industry compliance**: Domain plugins ensure regulatory requirements
- **Performance monitoring**: Automatic metrics and optimization
- **Consistent behavior**: Same runtime characteristics across functions

## 🔧 Imperative Usage (Future)

POET can be extended to support imperative syntax for dynamic scenarios:

```dana
# Declarative (current)
@poet(domain="financial_services")
def assess_credit(score: int, income: float) -> str:
    return "approved" if score >= 700 else "declined"

# Imperative (future extension)
def dynamic_assessment(score: int, income: float, domain: str) -> str:
    return poet.enhance(assess_credit, domain=domain)(score, income)
```

## 📊 Intelligence Distribution

### **80% Common Intelligence** (Runtime Infrastructure)
- Retry logic with exponential backoff
- Timeout handling and monitoring  
- Error categorization and recovery
- Performance metrics collection
- Parameter learning algorithms

### **20% Domain-Specific Intelligence** (Plugins)
- Input normalization per industry
- Output validation and compliance
- Industry-specific optimizations
- Regulatory requirement enforcement

## 🎓 Quick Start

1. **Write a simple function** with your business logic
2. **Add the `@poet()` decorator** with appropriate domain
3. **POET automatically provides** enterprise capabilities
4. **Optional**: Enable learning with `enable_training=true`

```dana
# Complete example
@poet(domain="financial_services", retries=3, enable_training=true)
def simple_credit_assessment(score: int, income: float, debt_ratio: float) -> str:
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"

# Test with varied inputs - POET normalizes automatically
result1 = simple_credit_assessment(720, 65000.0, 0.28)
result2 = simple_credit_assessment("good", "$50K", "25%")
```

---

**Next Steps**: 
- **[Getting Started](getting-started.md)** - Write your first POET function
- **[Configuration Guide](configuration.md)** - Domain plugins and runtime options  
- **[API Reference](api-reference.md)** - Complete decorator and configuration API 