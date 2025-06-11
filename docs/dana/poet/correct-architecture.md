# POET Correct Architecture

Based on analysis of the actual POET implementation, this document clarifies the correct architecture where engineers write simple business logic and POET runtime provides enterprise capabilities.

## 🏗️ Correct POET Architecture

### What Engineers Write (Simple Operate Functions)
```dana
@poet(domain="financial_services", retries=3)
def assess_credit_risk(credit_score: int, income: float, debt_ratio: float) -> str:
    # 5 lines of simple business logic
    if credit_score >= 750 and debt_ratio <= 0.3:
        return "approved"
    elif credit_score >= 650 and debt_ratio <= 0.45:
        return "conditional"
    else:
        return "declined"
```

### What POET Runtime Automatically Provides

#### POEExecutor Implementation (`opendxa/dana/poet/mvp_poet.py`)
```python
class POEExecutor:
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # P: Domain plugin processes inputs
            perceived_input = self.domain_plugin.process_inputs(args, kwargs)
            
            # O: Execute function with reliability infrastructure
            result = self._operate_with_retry(func, perceived_input)
            
            # E: Domain plugin validates output
            validated_result = self.domain_plugin.validate_output(result, perceived_input)
            
            # T: Optional parameter learning
            if self.enable_training:
                self._learn_from_execution(perceived_input, validated_result)
                
            return validated_result
```

## 🧠 Domain Plugins Provide Intelligence

### Available Plugins (Production Ready)
1. **financial_services.py**: Credit normalization, FCRA compliance, audit trails
2. **building_management.py**: Equipment protection, energy optimization, safety interlocks  
3. **semiconductor.py**: Process validation, SPC monitoring, equipment safety
4. **llm_optimization.py**: Prompt optimization, response validation, cost management

### Plugin Interface
```python
class DomainPlugin:
    def process_inputs(self, args, kwargs):
        """P-stage: Normalize and validate inputs"""
        # financial_services: "excellent"→780, "$50K"→50000, "25%"→0.25
        # building_management: Temperature conversion, occupancy processing
        
    def validate_output(self, result, input_data):
        """E-stage: Add compliance and validation"""
        # financial_services: FCRA compliance, audit trails
        # building_management: Safety interlocks, energy validation
```

## 📊 Intelligence Distribution: 80% Common + 20% Domain

### 80% Generalizable (POEExecutor Runtime)
- Retry logic with exponential backoff
- Timeout handling and monitoring
- Error recovery and categorization
- Performance metrics collection
- Parameter learning algorithms

### 20% Domain-Specific (Plugins)
| Domain | Input Processing (P) | Output Validation (E) |
|--------|---------------------|----------------------|
| Financial | Credit score, income, ratio normalization | FCRA compliance, audit trails |
| Building | Temperature conversion, occupancy analysis | Safety interlocks, energy validation |
| Manufacturing | Process parameter validation | SPC monitoring, equipment protection |
| LLM | Prompt optimization, context formatting | Quality validation, cost optimization |

## 🎯 Key Benefits

### For Engineers
- **90% less code**: Focus on 5-10 lines of business logic
- **Automatic enterprise capabilities**: Reliability, compliance built-in
- **Domain expertise**: Industry intelligence without domain knowledge

### Architecture Example
**Without POET (Manual Enterprise Logic - 50+ lines)**:
```python
def manual_credit_assessment(raw_data):
    # Input validation and normalization (10 lines)
    # Retry logic and error handling (15 lines)
    # Core business logic (5 lines) 
    # Compliance validation (10 lines)
    # Audit trail generation (8 lines)
    # Performance monitoring (5 lines)
```

**With POET (Simple Business Logic - 5 lines)**:
```dana
@poet(domain="financial_services")
def simple_credit_assessment(score: int, income: float, debt_ratio: float) -> str:
    return "approved" if score >= 700 and debt_ratio <= 0.3 else "declined"
```

## ✅ Current Implementation Status

### Production Ready (POET Core)
- ✅ **POETExecutor**: Complete P→O→E pipeline (`opendxa/dana/poet/mvp_poet.py`)
- ✅ **Domain Plugins**: 4 production plugins with input/output processing
- ✅ **Reliability**: Automatic retries, timeout handling, error recovery
- ✅ **Examples**: Industry demonstrations in `examples/dana/04_poet_examples/`

### Optional (T-Stage Learning)
- 🔄 **Parameter Learning**: Basic retry/timeout optimization
- 🔄 **Statistical Learning**: Advanced pattern recognition algorithms
- 🔄 **Metrics**: Performance tracking and learning effectiveness

## 🚀 Usage Patterns

### Basic Enhancement
```dana
@poet(retries=3, timeout=30.0)
def my_function(input: str) -> str:
    return process_data(input)
```

### Domain Intelligence
```dana
@poet(domain="financial_services")
def credit_function(score, income, debt_ratio) -> str:
    return "approved" if score >= 700 else "declined"
```

### With Learning
```dana
@poet(domain="llm_optimization", enable_training=true)
def reasoning_function(prompt: str) -> str:
    return reason(prompt)
```

## 🔗 Related Documentation

- **[Getting Started](getting-started.md)** - Write your first POET function
- **[API Reference](api-reference.md)** - Complete configuration options  
- **[Examples](../../../examples/dana/04_poet_examples/)** - Industry demonstrations
- **[Implementation](../../.implementation/poet/)** - Technical design docs

---

**Summary**: POET's value is in the **80/20 architecture** where engineers write **simple business functions** (20% effort) and POET runtime provides **enterprise capabilities** (80% value) through domain intelligence and reliability infrastructure. 