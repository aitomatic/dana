# POET Primer

## TL;DR (1 minute read)

```dana
# Instead of this (Python - fragile):
def assess_credit(score: int, income: float) -> str:
    return "approved" if score >= 700 else "declined"

assess_credit("excellent", "$50K")  # ❌ TypeError

# Do this (Dana - robust):
@poet(domain="financial_services", retries=3)
def assess_credit(score: int, income: float) -> str:
    return "approved" if score >= 700 else "declined"

assess_credit("excellent", "$50K")  # ✅ "approved" (POET converts to 780, 50000)
assess_credit(None, 65000)          # ✅ "declined" (POET uses defaults)

# More examples:
@poet(domain="sensors", timeout=30)
def process_sensor(temp: float, humidity: float) -> dict:
    return {"status": "normal" if temp < 80 else "warning"}

@poet(domain="api", validation=true)
def api_call(user_id: str) -> dict:
    return fetch_user_data(user_id)
```

---

**What it is**: POET enhances any function with intelligent processing - like Python's decorators but with neural context understanding, deterministic execution, symbolic validation, and adaptive learning from feedback.

## Why Should You Care?

**The Problem**: In Python, you write functions that break when inputs are unexpected:

```python
# Your typical Python function - fragile!
def assess_credit(score: int, income: float) -> str:
    return "approved" if score >= 700 else "declined"

# What happens with real-world data?
assess_credit("excellent", "$50K")  # TypeError: '>=' not supported
assess_credit(720, "65000")         # TypeError: '>=' not supported
assess_credit(None, 65000)          # TypeError: '>=' not supported
```

**The Solution**: POET decorators that handle the messy real world automatically:

```dana
@poet(domain="financial_services", retries=3)
def assess_credit(score: int, income: float) -> str:
    return "approved" if score >= 700 else "declined"

# Now handles everything gracefully:
assess_credit("excellent", "$50K")  # Works! POET converts to (780, 50000)
assess_credit(720, "65000")         # Works! POET converts to (720, 65000)
assess_credit(None, 65000)          # Works! POET uses defaults or retries
```

**Why You'll Love This**:
- **Exactly Like Python**: Same function syntax, same decorator pattern
- **Unlike Python**: Automatic input normalization and error recovery
- **Just like Python!**: Easy to add to existing code with `@poet()`

## The Big Picture

POET follows a 4-step pipeline that happens automatically:

**P**erceive → **O**perate → **E**nforce → **T**rain

```dana
# Your function (the "Operate" step)
@poet(domain="financial_services")
def simple_credit_check(score: int, income: float) -> str:
    return "approved" if score >= 700 and income >= 50000 else "declined"

# What POET does behind the scenes:
# 1. PERCEIVE: "excellent" → 780, "$50K" → 50000
# 2. OPERATE: Your function runs with clean data
# 3. ENFORCE: Validates output format and compliance rules
# 4. TRAIN: Learns from patterns to improve future calls
```

## How to Use POET (Python Style)

**Basic Usage** - Just like Python decorators:

```dana
# Exactly like Python decorators
@poet()
def my_function(x: int, y: str) -> bool:
    return x > 100 and y == "valid"

# With domain-specific intelligence
@poet(domain="financial_services")
def credit_check(score: int, income: float) -> str:
    return "approved" if score >= 700 else "declined"

# With retry logic (like Python's tenacity but smarter)
@poet(domain="building_management", retries=5)
def sensor_reading(temp: float, humidity: float) -> dict:
    return {"status": "normal" if temp < 80 else "warning"}
```

## Real-World Examples (Python-Style)

**Before (Pure Python - Fragile)**:
```python
def process_sensor_data(temp, humidity, pressure):
    # Manual validation everywhere
    if not isinstance(temp, (int, float)):
        temp = float(temp) if temp else 0.0
    if isinstance(humidity, str):
        humidity = float(humidity.replace('%', ''))
    if pressure is None:
        pressure = 1013.25  # Default atmospheric pressure
    
    # Your actual logic
    return {
        "status": "normal" if temp < 80 and humidity < 60 else "warning",
        "temp": temp,
        "humidity": humidity,
        "pressure": pressure
    }
```

**After (POET-Enhanced - Robust)**:
```dana
@poet(domain="building_management")
def process_sensor_data(temp: float, humidity: float, pressure: float) -> dict:
    # Clean, focused logic - POET handles the messy input processing
    return {
        "status": "normal" if temp < 80 and humidity < 60 else "warning",
        "temp": temp,
        "humidity": humidity,
        "pressure": pressure
    }
```

## What Happens When Things Go Wrong (Python-Style Errors)

**Python's Way**:
```python
def python_function(score, income):
    try:
        score = int(score) if score else 0
        income = float(str(income).replace('$', '').replace(',', ''))
        return "approved" if score >= 700 and income >= 50000 else "declined"
    except (ValueError, TypeError):
        return "error: invalid input"  # Generic error handling
```

**POET's Way**:
```dana
@poet(domain="financial_services", retries=3)
def poet_function(score: int, income: float) -> str:
    return "approved" if score >= 700 and income >= 50000 else "declined"

# POET automatically:
# - Converts "excellent" → 780, "good" → 720, etc.
# - Handles "$50K" → 50000, "65,000" → 65000
# - Retries with different interpretations if needed
# - Returns structured errors with context
```

## Pro Tips (Python Best Practices)

**1. Choose the Right Domain**:
```dana
# For financial data
@poet(domain="financial_services")  # Handles currency, credit scores, etc.

# For sensor/IoT data  
@poet(domain="building_management")  # Handles sensor readings, units, etc.

# For AI/LLM applications
@poet(domain="llm_optimization")  # Handles prompts, responses, etc.
```

**2. Use Type Hints** (Just like Python!):
```dana
# POET uses your type hints for better conversion
@poet(domain="financial_services")
def process_loan(amount: float, term: int, credit_score: int) -> dict:
    return {"approved": amount <= 100000 and credit_score >= 700}
```

**3. Combine with Python Patterns**:
```dana
# Works with Python's async/await
@poet(domain="financial_services")
async def async_credit_check(score: int, income: float) -> str:
    # Your async logic here
    return "approved" if score >= 700 else "declined"

# Works with Python's dataclasses
@poet(domain="building_management")
def process_sensor_reading(reading: SensorData) -> dict:
    return {"status": "normal" if reading.temp < 80 else "warning"}
```

## Before vs After (Python Perspective)

**Before - Manual Input Processing**:
```python
def credit_decision(score, income, employment):
    # 20+ lines of input validation and conversion
    if isinstance(score, str):
        score_map = {"excellent": 780, "good": 720, "fair": 650}
        score = score_map.get(score, 600)
    elif not isinstance(score, (int, float)):
        score = 600
    
    if isinstance(income, str):
        income = float(income.replace('$', '').replace(',', '').replace('K', '000'))
    elif not isinstance(income, (int, float)):
        income = 0
    
    # Your actual logic (3 lines)
    return "approved" if score >= 700 and income >= 50000 else "declined"
```

**After - POET Magic**:
```dana
@poet(domain="financial_services")
def credit_decision(score: int, income: float, employment: str) -> str:
    # Just your logic - POET handles all the input processing
    return "approved" if score >= 700 and income >= 50000 else "declined"
```

## Bottom Line

POET is like Python's `@property` or `@dataclass` decorators - they make your code cleaner and more robust. But POET goes further by adding domain intelligence, automatic input normalization, and adaptive learning. 

**Just add `@poet()` to any function** and get:
- **Exactly Like Python**: Same syntax, same patterns
- **Unlike Python**: Intelligent input processing and error recovery  
- **Just like Python!**: Easy to use, easy to understand

Your functions become bulletproof while staying readable and maintainable. 