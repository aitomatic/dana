# POET Dana Language Examples
# ===========================

This directory contains **Dana language examples** demonstrating POET's function enhancement capabilities. These examples show how to use POET decorators in Dana code to create intelligent, learning functions.

## 🎯 What These Examples Demonstrate

POET (Perceive → Operate → Enforce → Train) transforms simple Dana functions into intelligent systems through automatic enhancement:

### **Core POET Architecture in Dana**
```dana
@poet(domain="ml_monitoring", optimize_for="accuracy")
def detect_anomaly(value: float, threshold: float) -> dict:
    # Simple business logic in Dana
    is_anomaly = value > threshold
    return {"is_anomaly": is_anomaly, "value": value}
```

**What POET automatically adds:**
- **P (Perceive)**: Input validation and normalization
- **O (Operate)**: Error handling, retries, timeout management  
- **E (Enforce)**: Output validation and domain-specific compliance
- **T (Train)**: Learning from feedback to improve over time

## 📁 Example Files

### 1. **Basic Enhancement** (`01_basic_enhancement.na`)
**Demonstrates**: Core POET functionality with Dana syntax

```dana
@poet()
def calculate_sum(a: int, b: int) -> int:
    return a + b

result = calculate_sum(5, 3)
log(f"Enhanced result: {result}")
log(f"Execution ID: {result._poet['execution_id']}")
```

**Key Features:**
- ✅ Zero-config function enhancement
- ✅ Automatic execution tracking
- ✅ Domain-specific intelligence (`domain="ml_monitoring"`)
- ✅ POETResult wrapper with metadata

### 2. **Feedback Learning** (`02_feedback_learning.na`)
**Demonstrates**: Universal feedback and learning capabilities

```dana
@poet(optimize_for="accuracy")
def classify_sentiment(text: str) -> dict:
    # Simple rule-based logic
    return {"sentiment": "positive", "confidence": 0.7}

# Universal feedback - any format works
feedback(result, "The prediction was perfect!")
feedback(result, {"rating": 4, "comment": "Good accuracy"})
feedback(result, 0.8)  # Just a number
```

**Key Features:**
- ✅ Learning-enabled functions (`optimize_for` parameter)
- ✅ Universal feedback API - accepts any format
- ✅ LLM-powered feedback translation
- ✅ Automatic function improvement over time

### 3. **ML Monitoring** (`03_ml_monitoring.na`)
**Demonstrates**: Production ML monitoring with domain expertise

```dana
@poet(domain="ml_monitoring", optimize_for="reliability")
def detect_feature_drift(current_mean: float, reference_mean: float,
                        current_std: float, reference_std: float) -> dict:
    # Simple statistical comparison
    drift_score = abs(current_mean - reference_mean) / reference_std
    return {"drift_detected": drift_score > 2.0, "score": drift_score}
```

**Key Features:**
- ✅ Statistical drift detection with ML domain intelligence
- ✅ Model performance monitoring
- ✅ Data quality validation
- ✅ Production-ready ML operations patterns

## 🚀 Running the Examples

### Prerequisites
```bash
# Ensure OpenDXA is installed
uv sync

# Start the Dana REPL (if needed)
uv run dana
```

### Run Individual Examples
```bash
# Basic enhancement example
uv run python -m opendxa.dana.exec.dana examples/dana/poet/01_basic_enhancement.na

# Feedback learning example  
uv run python -m opendxa.dana.exec.dana examples/dana/poet/02_feedback_learning.na

# ML monitoring example
uv run python -m opendxa.dana.exec.dana examples/dana/poet/03_ml_monitoring.na
```

## 🔧 What You'll See

### **Automatic API Service Management**
- POET automatically starts local API server on first `@poet()` use
- No manual configuration required
- Transparent client-server communication
- Automatic cleanup at program exit

### **Function Enhancement in Action**
```
🚀 POET Basic Enhancement - Dana Example
==================================================

1. Basic Enhancement:
   @poet() adds P→O→E phases automatically
   calculate_sum(5, 3) = {'value': 8, 'execution_id': 'abc123...'}
   Enhanced: True
   Execution ID: abc123-def456-...

2. Domain-Specific Enhancement:
   @poet(domain='ml_monitoring') adds ML expertise
   detect_anomaly(5.0, 2.0) = {'is_anomaly': True, 'value': 5.0, ...}
   Function: detect_anomaly
   Version: v1
```

### **Learning and Feedback**
```
🧠 POET Feedback Learning - Dana Example
==================================================

1. Sentiment Classification with Learning:
   'This product is amazing!' → positive (0.70)
   
2. Providing Universal Feedback:
   Feedback 1: The first prediction was perfect!
   ✅ Processed feedback for execution abc123...
   
   Feedback 2: {"rating": 4, "comment": "Good accuracy"}
   ✅ Processed feedback for execution def456...
```

## 🎯 Key POET Concepts in Dana

### **1. Decorator Syntax**
```dana
@poet()                           # Basic enhancement
@poet(domain="ml_monitoring")     # Domain-specific intelligence
@poet(optimize_for="accuracy")    # Enable learning
@poet(retries=3, timeout=30.0)   # Custom configuration
```

### **2. Result Wrapping**
```dana
result = enhanced_function(args)
actual_value = result.unwrap()           # Get the actual result
execution_id = result._poet['execution_id']  # Get execution metadata
enhanced = result._poet['enhanced']      # Check if enhancement applied
```

### **3. Feedback Interface**
```dana
import opendxa.dana.poet.decorator.py as poet_module

# Any format works
poet_module.feedback(result, "Great job!")
poet_module.feedback(result, {"score": 9, "notes": "Very accurate"})
poet_module.feedback(result, 0.95)
```

### **4. Dana-Specific Patterns**
```dana
# Assignment (not +=)
count = count + 1

# Absolute value (no abs() function)
if value < 0:
    value = -value

# Boolean literals
is_valid = true
is_error = false

# List iteration
for item in items:
    # Process item
```

## 🔍 Dana vs Python Differences

### **Function Definitions**
```dana
# Dana
def my_function(a: int, b: float) -> str:
    return f"Result: {a + b}"

# Python (for comparison)  
def my_function(a: int, b: float) -> str:
    return f"Result: {a + b}"
```

### **Variable Assignment**
```dana
# Dana - only = assignment
counter = counter + 1
total = total + value

# Python (for comparison)
counter += 1
total += value
```

### **Imports**
```dana
# Dana - importing Python modules
import dana.frameworks.poet.decorator.py as poet_module

# Python (for comparison)
from dana.frameworks.poet.decorator import feedback
```

## 🛠️ Architecture Behind the Examples

### **POET Enhancement Pipeline**
1. **Source Code Analysis**: Dana functions parsed and analyzed
2. **Transpilation**: Functions enhanced with P→O→E intelligence
3. **Execution**: Enhanced functions run with tracking and monitoring
4. **Learning**: Feedback processed to improve future executions

### **Automatic Infrastructure**
- **API Service**: Local server started automatically
- **Client Management**: HTTP client lifecycle managed
- **Resource Cleanup**: Automatic shutdown and cleanup
- **Error Handling**: Graceful fallback to original functions

## 📈 Benefits Demonstrated

### **Development Productivity**
- **Before POET**: Complex ML monitoring requires 100+ lines
- **After POET**: Simple Dana function + `@poet()` decorator
- **Productivity Gain**: 90% reduction in infrastructure code

### **Zero Configuration**
- No setup required - just add `@poet()` decorator
- Automatic domain intelligence injection
- Universal feedback interface
- Self-managing infrastructure

### **Production Ready**
- Automatic error handling and retries
- Execution tracking and monitoring
- Learning from operational feedback
- Domain-specific compliance and validation

## 🎓 Learning Path

### **Beginner**: Start Here
1. Run `01_basic_enhancement.na` to see core functionality
2. Notice how simple functions become intelligent automatically
3. Observe execution tracking and result wrapping

### **Intermediate**: Add Learning
1. Run `02_feedback_learning.na` to see feedback capabilities
2. Try different feedback formats (text, JSON, numbers)
3. See how functions learn from operational feedback

### **Advanced**: Production Patterns
1. Run `03_ml_monitoring.na` for production ML scenarios
2. Understand domain-specific enhancements
3. Explore statistical intelligence and data quality validation

## 🔗 Related Documentation

- **[Dana Language Reference](../README.md)**: Complete Dana syntax
- **[POET Architecture](../../../docs/.implementation/poet/)**: Technical details
- **[OpenDXA Overview](../../../README.md)**: Framework overview

## 🎉 Next Steps

1. **Run the examples** to see POET enhancement in action
2. **Modify the functions** to experiment with different domains
3. **Add your own feedback** to see learning capabilities
4. **Create custom functions** using POET patterns

---

**Ready to enhance your Dana functions with POET?** Start with `01_basic_enhancement.na` and experience automatic intelligence!