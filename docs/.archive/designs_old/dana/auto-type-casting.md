# Dana Auto Type Casting: DWIM Design

**Status**: Proposed  
**Version**: 1.0  
**Date**: January 2025

## Overview

This document proposes implementing **smart, conservative auto type casting** in Dana to support the **"Do What I Mean" (DWIM)** philosophy. The goal is to make Dana more user-friendly and intuitive for agent reasoning while maintaining type safety where it matters.

## Current State

Dana currently has:

- ✅ Strong typing with explicit type checking via `TypeChecker`
- ✅ Support for int, float, string, bool, collections  
- ✅ F-string preference for string formatting
- ❌ No automatic type conversions (strict typing)
- ❌ Requires explicit conversions for mixed-type operations

## Motivation

Agent reasoning benefits from intuitive, "just works" behavior:

```dana
# These should work intuitively
private:count = 42
private:message = "Items: " + private:count    # Currently fails, should work

private:x = 5        # int
private:y = 3.14     # float  
private:sum = private:x + private:y           # Currently fails, should work (8.14)

if private:count == "42":                     # String comparison, should work
    log.info("Match found")
```

## Design Principles

### 1. **Conservative Safety First**
- Only allow conversions that are mathematically/logically safe
- Reject lossy conversions (float → int)
- Preserve original behavior where possible

### 2. **Intuitive DWIM Behavior**
- Mixed arithmetic should work (int + float → float)
- String building should be natural ("Count: " + 42)
- Comparisons should be flexible ("42" == 42)

### 3. **Configurable Control**
- Environment variable control: `DANA_AUTO_COERCION=1/0`
- Default: enabled for user-friendliness
- Can be disabled for strict typing

### 4. **Clear Error Messages**
- When coercion fails, explain why
- Suggest explicit conversions when appropriate

## Coercion Rules

### ✅ **Safe Upward Numeric Promotion**
```dana
private:x = 5        # int
private:y = 3.14     # float
private:result = private:x + private:y  # int → float (result: 8.14)
```
**Rule**: `int` can safely promote to `float` in arithmetic contexts.

### ✅ **String Building Convenience**
```dana
private:message = "Count: " + 42        # int → string (result: "Count: 42")
private:debug = "Value: " + 3.14        # float → string (result: "Value: 3.14") 
private:status = "Ready: " + true       # bool → string (result: "Ready: true")
```
**Rule**: Numbers and booleans can convert to strings for concatenation.

### ✅ **Flexible Comparisons**
```dana
if private:count == "42":               # string "42" → int 42 for comparison
    log.info("Match!")
    
if private:price == "9.99":             # string "9.99" → float 9.99
    log.info("Price match!")
```
**Rule**: Numeric strings can convert to numbers for comparison.

### ✅ **Liberal Boolean Context**
```dana
if private:count:           # Any non-zero number → true
    log.info("Has items")
    
if private:message:         # Any non-empty string → true
    log.info("Has message")
    
if private:items:           # Any non-empty collection → true
    log.info("Has items")
```
**Rule**: Standard truthiness applies in conditional contexts.

### ❌ **Rejected Unsafe Conversions**
```dana
private:x = 3.14
private:y = int(private:x)  # Must be explicit - lossy conversion
```
**Rule**: Lossy conversions require explicit casting.

## Function Return Values & LLM Responses

### **The Challenge**

Function return values, especially from `reason()` and other LLM functions, often come back as strings but need to be used in different contexts:

```dana
# Current problems without auto-casting:
private:answer = reason("What is 5 + 3?")      # Returns "8" (string)
private:result = private:answer + 2            # Currently fails - string + int

private:decision = reason("Should we proceed? Answer yes or no")  # Returns "yes"
if private:decision:                           # String "yes" is always truthy
    # This doesn't work as expected
```

### **Enhanced LLM Response Coercion**

We propose **intelligent LLM response coercion** that automatically detects and converts common patterns:

#### ✅ **Boolean-like Responses**
```dana
private:decision = reason("Should we proceed? Answer yes or no")
# "yes" → true, "no" → false, "1" → true, "0" → false
if private:decision:  # Now works intuitively!
    log.info("Proceeding...")
```

**Supported patterns**: `yes/no`, `true/false`, `1/0`, `correct/incorrect`, `valid/invalid`, `ok/not ok`

#### ✅ **Numeric Responses**
```dana
private:count = reason("How many items are there?")
# "42" → 42, "3.14" → 3.14
private:total = private:count + 10  # Now works: 42 + 10 = 52
```

#### ✅ **Mixed Operations**
```dana
private:price = reason("What's the base price?")  # Returns "29.99"
private:tax = 2.50
private:total = private:price + private:tax       # "29.99" + 2.50 → 32.49

private:message = "Total cost: $" + private:total  # Auto string conversion
```

### **Smart vs. Conservative Modes**

#### **Conservative Mode** (Default)
- Only converts clearly unambiguous responses
- `"42"` → `42`, `"yes"` → `true`, `"3.14"` → `3.14`
- Mixed content stays as string: `"The answer is 42"` → `"The answer is 42"`

#### **Smart Mode** (Optional)
- More aggressive pattern matching
- Could extract numbers from text: `"The answer is 42"` → `42`
- Configurable via `DANA_LLM_SMART_COERCION=1`

### **Implementation Strategy**

```python
# In TypeCoercion class
@staticmethod
def coerce_llm_response(value: str) -> Any:
    """Intelligently coerce LLM responses to appropriate types."""
    if not isinstance(value, str):
        return value
        
    cleaned = value.strip().lower()
    
    # Boolean-like responses
    if cleaned in ["yes", "true", "1", "correct", "valid", "ok"]:
        return True
    if cleaned in ["no", "false", "0", "incorrect", "invalid"]:
        return False
        
    # Numeric responses
    try:
        if cleaned.isdigit() or (cleaned.startswith('-') and cleaned[1:].isdigit()):
            return int(cleaned)
        return float(cleaned)  # Try float conversion
    except ValueError:
        pass
        
    return value  # Keep as string if no clear conversion
```

## Implementation Architecture

### Core Component: `TypeCoercion` Class

Located in `opendxa/dana/sandbox/interpreter/type_coercion.py`:

```python
class TypeCoercion:
    @staticmethod
    def can_coerce(value: Any, target_type: type) -> bool:
        """Check if coercion is safe and recommended."""
        
    @staticmethod 
    def coerce_value(value: Any, target_type: type) -> Any:
        """Perform safe coercion or raise TypeError."""
        
    @staticmethod
    def coerce_binary_operands(left: Any, right: Any, operator: str) -> Tuple[Any, Any]:
        """Smart coercion for binary operations."""
        
    @staticmethod
    def coerce_to_bool(value: Any) -> bool:
        """Convert to boolean using Dana's truthiness rules."""
    
    @staticmethod
    def coerce_llm_response(value: str) -> Any:
        """Intelligently coerce LLM responses to appropriate types."""
        
    @staticmethod
    def coerce_to_bool_smart(value: Any) -> bool:
        """Enhanced boolean coercion with LLM-aware logic."""
```

### Integration Points

#### 1. **Expression Executor Integration**
Modify `ExpressionExecutor.execute_binary_expression()`:

```python
def execute_binary_expression(self, node: BinaryExpression, context: SandboxContext) -> Any:
    left_raw = self.parent.execute(node.left, context)
    right_raw = self.parent.execute(node.right, context)
    
    if TypeCoercion.should_enable_coercion():
        left, right = TypeCoercion.coerce_binary_operands(
            left_raw, right_raw, node.operator.value
        )
    else:
        left, right = left_raw, right_raw
    
    # Perform operation with potentially coerced operands
    ...
```

#### 2. **Function Call Integration**
Modify function call handling to apply LLM coercion:

```python
def execute_function_call(self, node: FunctionCall, context: SandboxContext) -> Any:
    result = # ... normal function execution
    
    # Apply LLM coercion for reason() and similar functions
    if (TypeCoercion.should_enable_llm_coercion() and 
        node.name in ["reason", "llm_call", "ask_ai"]):
        result = TypeCoercion.coerce_llm_response(result)
    
    return result
```

#### 3. **Conditional Statement Integration**
Modify conditional evaluation for truthiness:

```python
def evaluate_condition(self, condition_expr: Any, context: SandboxContext) -> bool:
    value = self.evaluate_expression(condition_expr, context)
    
    if TypeCoercion.should_enable_coercion():
        return TypeCoercion.coerce_to_bool_smart(value)  # LLM-aware
    else:
        return bool(value)  # Standard Python truthiness
```

## Configuration Control

### Environment Variables
```bash
export DANA_AUTO_COERCION=1         # Enable basic auto-casting (default)
export DANA_LLM_AUTO_COERCION=1     # Enable LLM response coercion (default)
export DANA_LLM_SMART_COERCION=0    # Disable aggressive pattern matching (default)
```

### Runtime Control
```python
from opendxa.dana.sandbox.interpreter.type_coercion import TypeCoercion

# Check if enabled
basic_enabled = TypeCoercion.should_enable_coercion()
llm_enabled = TypeCoercion.should_enable_llm_coercion()
```

## Benefits

### ✅ **Enhanced User Experience**
- More intuitive for agent reasoning tasks
- Reduces friction in common operations
- "Just works" for mixed-type scenarios
- **Natural LLM integration** - reason() results work seamlessly

### ✅ **Backward Compatibility**
- Can be disabled for existing strict-typing workflows
- Preserves current behavior when disabled
- No breaking changes to existing code

### ✅ **Predictable Rules**
- Clear, documented conversion rules
- Conservative approach minimizes surprises
- Type-safe where it matters

## Migration Strategy

### Phase 1: Implementation (Current)
- ✅ Implement `TypeCoercion` class
- ✅ Create comprehensive test suite
- ✅ Document conversion rules
- ✅ Add LLM response coercion

### Phase 2: Integration
- [ ] Integrate with `ExpressionExecutor`
- [ ] Add conditional evaluation support
- [ ] Add function call integration for LLM responses
- [ ] Update error messages

### Phase 3: Testing & Validation
- [ ] Test with existing Dana programs
- [ ] Validate agent reasoning improvements
- [ ] Test reason() function integration
- [ ] Performance impact assessment

### Phase 4: Documentation & Release
- [ ] Update language documentation
- [ ] Create migration guide
- [ ] Release with feature flag

## Real-World Examples

### Agent Reasoning Tasks
```dana
# Temperature monitoring agent
private:current_temp = sensor.get_temperature()  # Returns 98.6
private:threshold = reason("What's the safe temperature threshold?")  # Returns "100"

if private:current_temp > private:threshold:     # 98.6 > "100" → 98.6 > 100.0
    log.warn("Temperature alert: " + private:current_temp)  # Auto string conversion
    
# Decision making
private:should_proceed = reason("Should we deploy? Answer yes or no")  # Returns "yes"
if private:should_proceed:  # "yes" → true
    deploy_system()
```

### Data Processing with LLM Enhancement
```dana
# Inventory management with AI assistance
private:count = inventory.get_count()            # Returns 42
private:reorder_level = reason("What should be the reorder level for this item?")  # Returns "20"

if private:count < private:reorder_level:        # 42 < "20" → 42 < 20 (false)
    log.info("Stock level sufficient")
else:
    private:order_qty = reason("How many should we reorder?")  # Returns "50"
    place_order(private:order_qty)               # "50" → 50
```

### Mixed Calculation Scenarios
```dana
# Budget calculation with AI input
private:base_budget = 1000.00                   # Float
private:ai_adjustment = reason("What percentage adjustment should we make? Just the number")  # Returns "15"

# This should work: 1000.00 * ("15" / 100) → 1000.00 * 0.15 = 150.00
private:adjustment_amount = private:base_budget * (private:ai_adjustment / 100)
private:final_budget = private:base_budget + private:adjustment_amount
```

## Conclusion

Auto type casting with conservative DWIM rules, enhanced with intelligent LLM response handling, will significantly improve Dana's usability for agent reasoning. The proposed implementation is:

- **Safe**: Only allows mathematically/logically sound conversions
- **Intuitive**: Handles common mixed-type scenarios naturally  
- **LLM-Aware**: Makes reason() and AI function results work seamlessly
- **Configurable**: Can be disabled for strict typing needs
- **Backward Compatible**: No breaking changes to existing code

This enhancement aligns with Dana's goal of being the ideal language for agent reasoning—powerful enough for complex logic, yet intuitive enough for natural language translation, with first-class support for LLM integration.

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>