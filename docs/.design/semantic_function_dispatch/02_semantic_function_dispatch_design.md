# Semantic Function Dispatch Design for Dana

## Executive Summary

**Revolutionary Approach**: Functions should adapt their behavior based on the **expected return type context**, not just coerce results after execution. This enables truly semantic, context-aware function dispatch.

## Core Concept: Context-Aware Function Invocation

### The Paradigm Shift

**Current Approach (Post-Execution Coercion)**:
```dana
# Function executes the same way, then result gets coerced
result = reason("what is pi?")  # Always returns same string
pi: float = result              # Then tries to coerce string → float
```

**Proposed Approach (Pre-Execution Context Awareness)**:
```dana
# Function receives context about expected return type and adapts behavior
pi: float = reason("what is pi?")   # Function KNOWS to return numeric value → 3.14159265...
story: str = reason("what is pi?")  # Function KNOWS to return narrative → "Pi is an irrational number..."
approx: int = reason("what is pi?") # Function KNOWS to return integer → 3
```

## Design Principles

### 1. **Semantic Function Dispatch**
Functions analyze their **expected return type context** to determine optimal response strategy:

```dana
# Same function call, different execution paths based on context
temperature: float = reason("What's the temperature?")    # Returns: 72.5
status: bool = reason("What's the temperature?")          # Returns: True (if temp is normal)
description: str = reason("What's the temperature?")      # Returns: "It's a comfortable 72 degrees"
alert: int = reason("What's the temperature?")            # Returns: 0 (no alert level)
```

### 2. **Context Propagation**
The type context flows **into** the function, not just applied **after**:

```dana
# Type hint provides semantic context to the function execution
value: float = ask_ai("How much does this cost?")
# → LLM prompt: "Return a numeric float value for: How much does this cost?"

description: str = ask_ai("How much does this cost?") 
# → LLM prompt: "Return a descriptive string for: How much does this cost?"

affordable: bool = ask_ai("How much does this cost?")
# → LLM prompt: "Return a boolean (affordable/expensive) for: How much does this cost?"
```

### 3. **Multi-Modal Function Behavior**
Functions become **polymorphic based on expected return semantics**:

```dana
# Mathematical queries adapt to expected precision/type
pi_precise: float = calculate("pi to 10 decimals")     # → 3.1415926536
pi_simple: int = calculate("pi to 10 decimals")       # → 3
pi_fraction: str = calculate("pi to 10 decimals")     # → "22/7 (approximately)"
pi_available: bool = calculate("pi to 10 decimals")   # → True
```

## Implementation Architecture

### Function Context Injection

```python
class ContextAwareFunction:
    def __call__(self, *args, expected_type=None, **kwargs):
        # Function receives context about expected return type
        if expected_type == bool:
            return self._execute_boolean_strategy(*args, **kwargs)
        elif expected_type == int:
            return self._execute_integer_strategy(*args, **kwargs)
        elif expected_type == float:
            return self._execute_float_strategy(*args, **kwargs)
        elif expected_type == str:
            return self._execute_string_strategy(*args, **kwargs)
        else:
            return self._execute_default_strategy(*args, **kwargs)
```

### LLM Function Context Enhancement

```python
class SemanticLLMFunction(ContextAwareFunction):
    def _execute_boolean_strategy(self, query, **kwargs):
        enhanced_prompt = f"""
        Return a clear boolean answer (yes/no, true/false) for:
        {query}
        
        Respond with only: 'yes', 'no', 'true', or 'false'
        """
        return self.llm_call(enhanced_prompt)
    
    def _execute_float_strategy(self, query, **kwargs):
        enhanced_prompt = f"""
        Return a precise numeric value as a decimal number for:
        {query}
        
        Respond with only the number (e.g., '3.14159', '42.0', '0.5')
        """
        return self.llm_call(enhanced_prompt)
        
    def _execute_string_strategy(self, query, **kwargs):
        enhanced_prompt = f"""
        Provide a detailed, descriptive response for:
        {query}
        
        Give a complete explanation or narrative response.
        """
        return self.llm_call(enhanced_prompt)
```

## Concrete Examples

### Mathematical Queries
```dana
# Same question, different semantic contexts
pi: float = reason("what is pi?")
# → Function strategy: Return precise decimal
# → LLM Response: "3.14159265358979323846"
# → Result: 3.14159265358979323846

pi: int = reason("what is pi?") 
# → Function strategy: Return rounded integer
# → LLM Response: "3"
# → Result: 3

pi: str = reason("what is pi?")
# → Function strategy: Return educational explanation
# → LLM Response: "Pi is an irrational number representing the ratio of a circle's circumference to its diameter..."
# → Result: "Pi is an irrational number..."

pi: bool = reason("what is pi?")
# → Function strategy: Return existence/validity check
# → LLM Response: "true"
# → Result: True
```

### Decision Making
```dana
# Decision queries with different semantic expectations
proceed: bool = reason("Should we deploy to production?")
# → Function strategy: Return clear yes/no decision
# → LLM Response: "no"
# → Result: False

confidence: float = reason("Should we deploy to production?")
# → Function strategy: Return confidence percentage
# → LLM Response: "0.3"  
# → Result: 0.3

reasons: str = reason("Should we deploy to production?")
# → Function strategy: Return detailed reasoning
# → LLM Response: "We should wait because the test coverage is only 60%..."
# → Result: "We should wait because..."

risk_level: int = reason("Should we deploy to production?")
# → Function strategy: Return risk score (1-10)
# → LLM Response: "7"
# → Result: 7
```

### Data Analysis
```dana
# Analysis functions adapt to expected output format
trend: bool = analyze_data("sales are increasing")
# → Function strategy: Return trend direction (up/down)
# → Result: True

growth_rate: float = analyze_data("sales are increasing") 
# → Function strategy: Return percentage growth
# → Result: 0.15

summary: str = analyze_data("sales are increasing")
# → Function strategy: Return detailed analysis
# → Result: "Sales have shown a 15% increase over the past quarter..."

alert_priority: int = analyze_data("sales are increasing")
# → Function strategy: Return priority level (0-10)
# → Result: 2
```

## Type Context Detection

### Assignment Context
```dana
# Direct assignment - type hint provides context
result: bool = reason("Is it ready?")  # Boolean context detected
```

### Variable Declaration Context
```dana
# Variable with type annotation
temperature: float = get_sensor_reading()  # Float context detected
```

### Function Parameter Context
```dana
def process_decision(approved: bool):
    pass

# Function call context provides type hint
process_decision(reason("Should we proceed?"))  # Boolean context from parameter type
```

### Comparison Context  
```dana
# Comparison operations suggest boolean context
if reason("Is system healthy?"):  # Boolean context inferred
    pass
```

### Arithmetic Context
```dana
# Arithmetic operations suggest numeric context
total = count + reason("How many more?")  # Numeric context inferred
```

## Advanced Semantic Patterns

### Conditional Response Strategies
```dana
# Function can provide different answers based on context appropriateness
complexity: int = reason("How complex is this algorithm?")
# → If answerable numerically: Returns 1-10 scale
# → If not numerically measurable: Returns error with suggestion

complexity: str = reason("How complex is this algorithm?")  
# → Always provides qualitative description
```

### Fallback Strategies
```dana
# Graceful degradation when context cannot be satisfied
price: float = reason("What's the price of happiness?")
# → Function recognizes abstract question
# → Option 1: Return error with explanation
# → Option 2: Return best-effort numeric interpretation
# → Option 3: Return NaN with warning
```

## Implementation Phases

### Phase 1: Core Infrastructure
1. **Context Detection**: Identify expected return type from AST
2. **Function Registry**: Register context-aware functions
3. **Basic LLM Enhancement**: Add type-specific prompt engineering

### Phase 2: Semantic Enhancement  
1. **Advanced Prompt Strategies**: Sophisticated context-to-prompt mapping
2. **Multi-Strategy Functions**: Functions with multiple execution paths
3. **Fallback Handling**: Graceful degradation for impossible contexts

### Phase 3: Advanced Features
1. **Confidence Scoring**: Functions return confidence in context appropriateness
2. **Cross-Function Learning**: Shared context understanding across function calls
3. **Dynamic Strategy Selection**: AI-driven selection of optimal response strategy

## Breaking Changes and Migration

### Expected Changes
1. **Function Behavior**: Same function call may return different results
2. **Type Safety**: Stricter enforcement of type contexts
3. **LLM Prompting**: Fundamental changes to how LLM functions operate

### Migration Strategy
1. **Backwards Compatibility Mode**: Environment flag for old behavior
2. **Gradual Rollout**: Phase-by-phase activation of context awareness
3. **Clear Documentation**: Examples showing before/after behavior

## Configuration and Control

### Global Settings
```bash
DANA_SEMANTIC_DISPATCH=enabled|disabled           # Default: enabled
DANA_CONTEXT_STRICTNESS=strict|normal|permissive  # Default: normal
DANA_FALLBACK_STRATEGY=error|warning|best_effort  # Default: warning
```

### Per-Function Control
```dana
# Explicit control over context behavior
result = reason("question", context_mode="strict")    # Must satisfy context or error
result = reason("question", context_mode="permissive") # Best effort, no errors
```

## Questions for Agreement

1. **Should this be the default behavior** or opt-in per function?
2. **How aggressive should context adaptation be?** (strict vs permissive)
3. **What should happen when context cannot be satisfied?** (error vs fallback)
4. **Should we support mixed contexts** (e.g., union types)?
5. **How should this interact with existing coercion?** (replace vs complement)

---

**This approach makes Dana functions truly semantic and context-aware, delivering exactly what the user intends based on how they plan to use the result.** 