# POET Examples

POET (Perceive-Operate-Enforce-Train) examples demonstrating function enhancement with learning capabilities.

## Getting Started

```bash
# Set up environment
cd /path/to/opendxa.poet
cp .env.example .env  # Add your LLM API keys

# Install dependencies
uv sync

# Run examples
python examples/poet/01_hello_world/basic_enhancement.py
python examples/poet/02_basic_usage/ml_monitoring.py
```

## Example Structure

### 01_hello_world/
Minimal working POET examples to understand core concepts:
- `basic_enhancement.py` - Simple function enhancement
- `with_feedback.py` - Basic feedback loop

### 02_basic_usage/
Common patterns and typical use cases:
- `ml_monitoring.py` - ML drift detection with domain expertise
- `api_reliability.py` - API function with automatic retries
- `data_validation.py` - Input/output validation patterns

### 03_real_world/
Production-like scenarios:
- `model_monitoring.py` - Complete ML monitoring pipeline
- `financial_analysis.py` - Financial risk assessment with learning
- `hvac_optimization.py` - Building control with feedback

### 04_advanced/
Complex feedback and learning scenarios:
- `multi_domain.py` - Multiple domain templates
- `custom_feedback.py` - Custom feedback processing
- `learning_evolution.py` - Function evolution over time

## Key Concepts Demonstrated

1. **Zero-Config Enhancement**: Functions work better immediately with `@poet()`
2. **Domain Intelligence**: `@poet(domain="ml_monitoring")` adds ML expertise
3. **Learning Loop**: `@poet(optimize_for="accuracy")` enables continuous improvement
4. **Universal Feedback**: `poet.feedback(result, "any feedback format")` works with any input
5. **Transparent Operation**: Enhanced functions return `POETResult` with execution context

## Alpha MVP Features

- ✅ Local transpilation (no remote service needed)
- ✅ P→O→E phases for all functions
- ✅ Train phase when `optimize_for` is specified
- ✅ LLM-powered feedback translation
- ✅ In-memory learning state
- ✅ ML monitoring domain template
- ✅ File-based storage in `.poet/` directory

## Running Examples

Each example is self-contained and can be run independently:

```python
# Example structure
from opendxa.dana.poet import poet

@poet(domain="ml_monitoring", optimize_for="accuracy")
def detect_drift(current_data, reference_data):
    # Your simple function
    return {"drift_detected": False, "score": 0.0}

# Enhanced function automatically includes:
# - Input validation (Perceive)
# - ML monitoring expertise (Operate)
# - Output validation (Enforce)  
# - Learning capabilities (Train)

# Usage
result = detect_drift(data1, data2)
poet.feedback(result, "The sensitivity is too high")
```