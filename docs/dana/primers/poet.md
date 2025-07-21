# POET Primer

**What it is**: POET enhances any function with intelligent processing - neural context understanding on inputs, deterministic execution, symbolic validation on outputs, and adaptive learning from feedback.

## Core Concept

```dana
# Basic function
def assess_credit(score: int, income: float) -> str:
    return "approved" if score >= 700 else "declined"

# POET-enhanced function
@poet(domain="financial_services", retries=3)
def assess_credit(score: int, income: float) -> str:
    return "approved" if score >= 700 else "declined"

# Same function, now has:
# - Context injection & fault tolerance (perceive)
# - Deterministic execution with reliability (operate)
# - Output formatting & validation (enforce)
# - Adaptive learning from feedback (train)
```

## The POET Pipeline

**P**erceive → **O**perate → **E**nforce → **T**rain

- **P**: Context injection & normalization (`"excellent"` → 780, `"$50K"` → 50000)
- **O**: Your function + deterministic execution with fault tolerance
- **E**: Output formatting, validation, and structured results
- **T**: Learning from execution patterns to improve over time

## Domain Intelligence

| Domain | Context Injection | Output Validation |
|--------|-------------------|-------------------|
| **financial_services** | Credit score normalization | Compliance checking, audit trails |
| **building_management** | Sensor data interpretation | Safety rule enforcement |
| **llm_optimization** | Prompt context optimization | Response quality validation |

## Quick Example

```dana
@poet(domain="financial_services")
def simple_credit_check(score: int, income: float) -> str:
    return "approved" if score >= 700 and income >= 50000 else "declined"

# Test with varied inputs - POET normalizes automatically
result1 = simple_credit_check(720, 65000)           # Standard format
result2 = simple_credit_check("good", "$50K")       # POET handles conversion
```

**Bottom line**: Add `@poet()` to any function for intelligent input processing, deterministic execution, and adaptive learning. 