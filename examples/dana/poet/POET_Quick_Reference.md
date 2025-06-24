# POET Quick Reference - Four Use Cases

## 🎯 Overview
POET enhances functions with Plan→Observe→Execute (+ optional Train) phases automatically.

## 📐 Use Case A: Mathematical Operations (POE)
**Domain:** `mathematical_operations`  
**Purpose:** Bulletproof math without boilerplate

```python
@poet(domain="mathematical_operations", retries=2)
def safe_divide(a: float, b: float) -> float:
    return a / b
```

**What it adds:**
- ✓ Division by zero detection (caught in validation, not runtime)
- ✓ NaN/Infinity input checking
- ✓ Numerical stability monitoring
- ✓ Automatic retry logic
- ✓ Clear error messages

**User interaction:**
```python
result = safe_divide(10, 0)  # ValueError: "Division by zero: parameter 'b' cannot be zero"
```

---

## 🤖 Use Case B: LLM Optimization (POE)
**Domain:** `llm_optimization`  
**Purpose:** Reliable LLM interactions

```python
@poet(domain="llm_optimization", retries=3, timeout=30)
def reason_about(question: str) -> str:
    return llm.query(question)
```

**What it adds:**
- ✓ Prompt validation and optimization
- ✓ Retry with exponential backoff
- ✓ Token usage monitoring
- ✓ Response quality validation
- ✓ Rate limit handling

**User interaction:**
```python
answer = reason_about("What is quantum computing?")  # Automatic retries if LLM fails
```

---

## 🎯 Use Case C: Prompt Optimization (POET with Learning)
**Domain:** `prompt_optimization`  
**Purpose:** Self-improving prompts through A/B testing

```python
@poet(domain="prompt_optimization", optimize_for="clarity")
def explain_concept(concept: str, audience: str) -> str:
    prompt = f"Explain {concept} to {audience}"
    return llm.query(prompt)
```

**What it adds:**
- ✓ Automatic A/B testing of prompt variants
- ✓ Performance tracking (speed, quality, tokens)
- ✓ Learning from user feedback
- ✓ Best variants rise to the top
- ✓ Continuous improvement

**User interaction:**
```python
# Step 1: Use normally
result = explain_concept("AI", "child")

# Step 2: Provide feedback (optional)
feedback(result._poet.execution_id, "too complex")

# Step 3: Future calls use better prompts automatically
```

---

## 📊 Use Case D: ML Monitoring (POET with Adaptive Learning)
**Domain:** `ml_monitoring`  
**Purpose:** Self-adjusting ML monitoring

```python
@poet(domain="ml_monitoring", optimize_for="accuracy")
def predict_churn(features: list[float]) -> float:
    return model.predict(features)
```

**What it adds:**
- ✓ Input distribution monitoring
- ✓ Drift detection with adaptive thresholds
- ✓ Anomaly detection that learns
- ✓ Performance tracking
- ✓ Retraining recommendations

**User interaction:**
```python
# Normal prediction
prob = predict_churn([0.7, 0.8, 0.6])  # Works normally

# Unusual data triggers alert
prob = predict_churn([0.1, 0.1, 0.1])  # ⚠️ Drift detected

# System adapts thresholds over time automatically
```

---

## 🔑 Key Differences

| Use Case | Domain | Learning? | Primary Benefit |
|----------|---------|-----------|-----------------|
| A | `mathematical_operations` | No | Automatic validation & reliability |
| B | `llm_optimization` | No | Robust LLM interactions |
| C | `prompt_optimization` | Yes | Self-improving prompts |
| D | `ml_monitoring` | Yes | Adaptive drift detection |

## 💡 Usage Tips

1. **Start Simple**: Just add `@poet(domain="...")` - sensible defaults handle the rest
2. **Call Normally**: Enhanced functions work exactly like regular functions
3. **Provide Feedback** (C & D only): `feedback(result._poet.execution_id, "feedback")`
4. **Monitor Logs**: POET logs important events and adaptations
5. **Trust the System**: POET learns and improves automatically

## 🚀 From Prototype to Production
```python
# Before POET: Complex validation and error handling
def divide(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Arguments must be numeric")
    if math.isnan(a) or math.isnan(b):
        raise ValueError("Arguments cannot be NaN")
    if b == 0:
        raise ValueError("Cannot divide by zero")
    # ... more validation ...
    return a / b

# After POET: Clean and simple
@poet(domain="mathematical_operations")
def divide(a: float, b: float) -> float:
    return a / b
```

**One decorator. Complete reliability. That's POET.**