# IPV Usage Guide: Complete Reference

## Overview

IPV (Infer-Process-Validate) is Dana's intelligent optimization pattern that automatically enhances AI interactions with **comment-aware context analysis** and **LLM-driven optimization**. This guide provides comprehensive usage examples and best practices.

## 🎯 Core Concepts

### The IPV Pattern
```
INFER: Extract context from code, comments, and type hints
   ↓
PROCESS: Use LLM to analyze context and optimize prompts  
   ↓
VALIDATE: Apply type-driven validation and formatting
```

### Comment-Aware Context Analysis
IPV automatically extracts and analyzes:
- **Comments** in your Dana code
- **Type hints** from variable assignments  
- **Surrounding code context**
- **Domain indicators** and **intent signals**

## 🚀 Basic Usage

### 1. Simple Reasoning with IPV

```dana
# Extract financial data from text
price = reason("Find the cost: Item sells for $29.99") -> float

# IPV automatically:
# - Detects financial domain from "$" symbol
# - Applies numerical extraction for float type
# - Validates and cleans the result
```

### 2. Comment-Driven Optimization

```dana
# Medical data extraction - requires high accuracy
# Patient temperature should be in Celsius
temperature = reason("Patient reports feeling feverish at 101.5°F") -> float

# IPV leverages comments to:
# - Understand medical context from comment
# - Apply temperature conversion logic
# - Ensure precise numerical extraction
```

### 3. Complex Type Handling

```dana
# Extract structured customer data
# Return as key-value pairs for database storage
customer_info = reason("John Smith, age 30, email john@example.com") -> dict

# IPV will:
# - Parse natural language into structured data
# - Return: {"name": "John Smith", "age": 30, "email": "john@example.com"}
# - Validate dictionary structure
```

## 🎛️ Advanced Usage

### 1. Multiple IPV Executors

```python
from opendxa.dana.ipv.executor import IPVReason, IPVDataProcessor, IPVAPIIntegrator

# Reasoning tasks
reasoner = IPVReason()
result = reasoner.execute("Analyze this financial report...", context)

# Data processing tasks  
processor = IPVDataProcessor()
analysis = processor.execute("Find trends in sales data", context, data=sales_data)

# API integration tasks
integrator = IPVAPIIntegrator()
api_result = integrator.execute("Get weather for San Francisco", context)
```

### 2. Custom Configuration

```python
from opendxa.dana.ipv.config import IPVConfig

# Create custom configuration
config = IPVConfig(
    max_iterations=3,          # Maximum retry attempts
    enable_caching=True,       # Cache similar requests
    fallback_strategy="simple", # Fallback to basic processing
    custom_system_message="You are a financial analysis expert..."
)

# Use with IPV executor
reasoner = IPVReason()
result = reasoner.execute(intent, context, config=config)
```

### 3. Debug Mode and Monitoring

```python
# Enable debug mode for detailed logging
reasoner = IPVReason()
reasoner.set_debug_mode(True)

result = reasoner.execute("Complex analysis task...", context)

# Get execution history
history = reasoner.get_execution_history()
print(f"Processed {len(history)} requests")

# Get performance statistics
stats = reasoner.get_performance_stats()
print(f"Average processing time: {stats['average_duration']:.2f}s")
print(f"Success rate: {stats['success_rate']:.1%}")
```

## 📊 Type-Driven Validation Examples

### Numerical Types

```dana
# Float extraction with validation
price = reason("The item costs twenty-nine dollars and ninety-nine cents") -> float
# Result: 29.99

# Integer extraction  
count = reason("We have fifteen items in stock") -> int
# Result: 15

# Boolean extraction
approved = reason("The request was approved by management") -> bool  
# Result: true
```

### Structured Types

```dana
# Dictionary extraction
product = reason("iPhone 14, $999, 128GB storage, Blue color") -> dict
# Result: {"name": "iPhone 14", "price": 999, "storage": "128GB", "color": "Blue"}

# List extraction
colors = reason("Available in red, blue, green, and yellow") -> list
# Result: ["red", "blue", "green", "yellow"]
```

### Complex Validation

```dana
# JSON-structured response
config = reason("Set timeout to 30 seconds, retries to 3, debug mode on") -> dict
# Result: {"timeout": 30, "retries": 3, "debug": true}
```

## 🔧 Integration Patterns

### 1. Dana Function Integration

```python
# opendxa/dana/sandbox/interpreter/functions/core/my_function.py

from opendxa.dana.ipv.executor import IPVReason

def smart_extract_function(prompt: str, context: Any) -> Any:
    """Enhanced extraction function using IPV."""
    
    # Create IPV executor
    executor = IPVReason()
    
    # Execute with context-aware optimization
    result = executor.execute(prompt, context)
    
    return result
```

### 2. Custom IPV Executor

```python
class IPVCustomAnalyzer(IPVExecutor):
    """Custom IPV executor for specialized analysis."""
    
    def infer_phase(self, intent: str, context: Any, **kwargs) -> Dict[str, Any]:
        """Custom inference logic."""
        return {
            "operation_type": "custom_analysis",
            "domain": self._detect_custom_domain(intent),
            "complexity": self._assess_complexity(intent),
        }
    
    def process_phase(self, intent: str, enhanced_context: Dict[str, Any], **kwargs) -> Any:
        """Custom processing with specialized prompts."""
        domain = enhanced_context.get("domain")
        
        if domain == "scientific":
            system_msg = "You are a scientific research assistant..."
        else:
            system_msg = "You are a general analysis assistant..."
            
        # Enhanced prompt based on domain
        enhanced_prompt = f"[{domain.upper()} ANALYSIS]\n{intent}"
        
        return self._execute_llm_call(enhanced_prompt, context, {
            "system_message": system_msg,
            "temperature": 0.3,  # Lower temperature for scientific accuracy
        })
    
    def validate_phase(self, result: Any, enhanced_context: Dict[str, Any], **kwargs) -> Any:
        """Custom validation logic."""
        # Apply domain-specific validation
        return self._apply_custom_validation(result, enhanced_context)
```

## 🎨 Best Practices

### 1. Effective Comments

```dana
# ✅ Good: Specific, actionable context
# Financial analysis - extract currency values in USD
# Round to 2 decimal places for accounting accuracy
revenue = reason("Q3 revenue was $1.2M") -> float

# ❌ Poor: Vague or redundant
# Get some number
value = reason("Extract the number") -> float
```

### 2. Type Hint Strategy

```dana
# ✅ Good: Use specific types for better validation
customer_data = reason("Parse customer info") -> dict  # Structured data
item_count = reason("How many items?") -> int         # Whole numbers
price_total = reason("Calculate total") -> float       # Decimal precision
```

### 3. Error Handling

```python
from opendxa.dana.common.exceptions import SandboxError

try:
    result = reasoner.execute(complex_prompt, context)
except SandboxError as e:
    # Handle IPV execution errors
    print(f"IPV execution failed: {e}")
    # Fallback to simpler processing
    result = simple_fallback_function(complex_prompt)
```

## 🔍 Debugging and Troubleshooting

### 1. Debug Mode Output

```python
reasoner.set_debug_mode(True)
result = reasoner.execute("Analyze financial data...", context)

# Debug output shows:
# - Context extraction results
# - LLM prompt enhancement
# - Validation steps
# - Performance metrics
```

### 2. Common Issues

**Issue: Type validation fails**
```python
# Solution: Check expected type matches intent
price = reason("The cost is high") -> float  # ❌ No numerical data
price = reason("The cost is $29.99") -> float  # ✅ Clear numerical value
```

**Issue: Context not extracted**
```python
# Solution: Ensure proper comment placement
# Place comments directly above the relevant code
# Use descriptive variable names
financial_total = reason("Calculate sum") -> float  # ✅ Clear context
```

**Issue: Poor performance**
```python
# Solution: Use caching for repeated requests
config = IPVConfig(enable_caching=True)
reasoner.execute(intent, context, config=config)
```

## 📈 Performance Optimization

### 1. Caching Strategy
```python
# Enable caching for repeated patterns
config = IPVConfig(enable_caching=True, cache_ttl=300)  # 5-minute cache
```

### 2. Batch Processing
```python
# Process multiple similar requests together
requests = [
    ("Extract price from: $29.99", context1),
    ("Extract price from: $45.00", context2),
    ("Extract price from: $12.50", context3),
]

results = []
for intent, ctx in requests:
    results.append(reasoner.execute(intent, ctx))
```

### 3. Mock Mode for Testing
```python
import os

# Enable mock mode for testing
os.environ["OPENDXA_MOCK_LLM"] = "true"

# IPV will use mock responses instead of real LLM calls
result = reasoner.execute("Test prompt", context)
```

## 🔮 Future Enhancements

### Planned Features
- **Cross-language context analysis** for multi-file projects
- **Learning from user corrections** to improve accuracy
- **Domain-specific optimization packages** for finance, medical, legal
- **Integration with external knowledge bases**
- **Real-time performance monitoring dashboard**

---

## Quick Reference

### IPV Executors
- `IPVReason` - General reasoning and extraction
- `IPVDataProcessor` - Data analysis and processing  
- `IPVAPIIntegrator` - API calls and integrations

### Key Methods
- `executor.execute(intent, context, **kwargs)` - Main execution
- `executor.set_debug_mode(enabled)` - Toggle debugging
- `executor.get_execution_history()` - Get request history
- `executor.get_performance_stats()` - Get performance metrics

### Configuration
- `IPVConfig(max_iterations, enable_caching, fallback_strategy)`
- Environment variable: `OPENDXA_MOCK_LLM=true` for testing

This guide provides everything needed to effectively use IPV in your Dana applications. For advanced customization, see the [IPV Architecture Documentation](../designs/ipv-optimization.md). 