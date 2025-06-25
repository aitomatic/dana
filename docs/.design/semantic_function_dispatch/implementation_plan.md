# Implementation Plan: Semantic Function Dispatch with POET Enhancement

**Updated Priority**: Complete POET integration for context-aware prompt optimization

## Current Status Assessment

### ✅ **Completed Infrastructure (95%)**
- Enhanced Coercion Engine: 50+ semantic patterns working perfectly
- Context Detection System: AST-based type hint extraction functional  
- Type Hint Integration: Assignment coercion working for clean inputs
- Zero Representation Fixes: All boolean edge cases resolved
- Conversational Patterns: Revolutionary semantic understanding

### ❌ **Critical Missing Piece (5%)**
**POET Integration Gap**: `reason()` function not enhanced to use context for prompt optimization

**Root Cause**: The infrastructure exists but is not connected:
1. `ContextDetector` can extract `expected_type` from type hints ✅
2. `reason()` function exists and works ✅  
3. **Missing**: POET enhancement that modifies prompts based on `expected_type` ❌

## Implementation Plan: POET-Enhanced Semantic Function Dispatch

### **Phase 1: POET Integration Core (1-2 days)**

#### **1.1 Enhance reason() Function with Context Awareness**

Create enhanced reason function that uses context detection:

```python
# opendxa/dana/sandbox/interpreter/functions/core/enhanced_reason_function.py

from opendxa.dana.sandbox.interpreter.context_detection import ContextDetector
from opendxa.dana.sandbox.interpreter.enhanced_coercion import SemanticCoercer

def context_aware_reason_function(
    prompt: str,
    context: SandboxContext,
    options: Optional[Dict[str, Any]] = None,
    use_mock: Optional[bool] = None,
) -> Any:
    """POET-enhanced reason function with automatic prompt optimization based on expected return type."""
    
    # Extract context from current execution environment
    context_detector = ContextDetector()
    type_context = context_detector.detect_current_context(context)
    
    # Enhance prompt based on expected type
    enhanced_prompt = enhance_prompt_for_type(prompt, type_context)
    
    # Execute with current reasoning system
    result = execute_original_reason(enhanced_prompt, context, options, use_mock)
    
    # Apply semantic coercion if type context is available
    if type_context and type_context.expected_type:
        coercer = SemanticCoercer()
        result = coercer.coerce_value(result, type_context.expected_type)
    
    return result
```

#### **1.2 Implement Prompt Enhancement Engine**

Create intelligent prompt modification based on expected return type:

```python
# opendxa/dana/sandbox/interpreter/prompt_enhancement.py

class PromptEnhancer:
    """Enhances prompts based on expected return type context."""
    
    def enhance_for_type(self, prompt: str, expected_type: str) -> str:
        """Transform prompt to optimize for specific return type."""
        
        if expected_type == "bool":
            return self._enhance_for_boolean(prompt)
        elif expected_type == "int":
            return self._enhance_for_integer(prompt)
        elif expected_type == "float":
            return self._enhance_for_float(prompt)
        elif expected_type == "str":
            return self._enhance_for_string(prompt)
        else:
            return prompt  # No enhancement for unknown types
    
    def _enhance_for_boolean(self, prompt: str) -> str:
        """Enhance prompt to return clear boolean response."""
        return f"""{prompt}

IMPORTANT: Respond with a clear yes/no decision.
Return format: "yes" or "no" (or "true"/"false")
Do not include explanations unless specifically requested."""

    def _enhance_for_integer(self, prompt: str) -> str:
        """Enhance prompt to return clean integer."""
        return f"""{prompt}

IMPORTANT: Return ONLY the final integer number.
Do not include explanations, formatting, or additional text.
Expected format: A single whole number (e.g., 42)"""

    def _enhance_for_float(self, prompt: str) -> str:
        """Enhance prompt to return clean float."""
        return f"""{prompt}

IMPORTANT: Return ONLY the final numerical value as a decimal number.
Do not include explanations, formatting, or additional text.
Expected format: A single floating-point number (e.g., 81.796)"""
```

#### **1.3 Context Detection Integration**

Extend context detector to work with function calls:

```python
# Update: opendxa/dana/sandbox/interpreter/context_detection.py

class ContextDetector(Loggable):
    
    def detect_current_context(self, context: SandboxContext) -> Optional[TypeContext]:
        """Detect type context from current execution environment."""
        
        # Get current AST node being executed
        current_node = context.get_current_node()
        
        if isinstance(current_node, Assignment) and current_node.type_hint:
            return self.detect_assignment_context(current_node)
        
        # Try to infer from surrounding context
        return self._infer_from_execution_context(context)
    
    def _infer_from_execution_context(self, context: SandboxContext) -> Optional[TypeContext]:
        """Infer type context from execution environment."""
        
        # Check if we're in an assignment expression
        execution_stack = context.get_execution_stack()
        
        for frame in reversed(execution_stack):
            if hasattr(frame, 'node') and isinstance(frame.node, Assignment):
                if frame.node.type_hint:
                    return self.detect_assignment_context(frame.node)
        
        return None
```

### **Phase 2: Function Registry Integration (1 day)**

#### **2.1 Update Function Registration**

Integrate enhanced reason function into the registry:

```python
# Update: opendxa/dana/sandbox/interpreter/functions/function_registry.py

def register_enhanced_reason_function(self):
    """Register POET-enhanced reason function."""
    
    # Replace existing reason function with enhanced version
    self.register_function(
        name="reason",
        func=context_aware_reason_function,
        metadata={
            "poet_enhanced": True,
            "context_aware": True,
            "semantic_coercion": True
        }
    )
```

#### **2.2 Add Context Parameter Passing**

Ensure context flows through function calls:

```python
# Update function call mechanism to pass context information
def call_with_context(self, func_name: str, context: SandboxContext, *args, **kwargs):
    """Enhanced function call with context information."""
    
    # Get function info
    func_info = self.get_function_info(func_name)
    
    # For context-aware functions, pass context as parameter
    if func_info.get("context_aware", False):
        return func_info.func(*args, context=context, **kwargs)
    else:
        return func_info.func(*args, **kwargs)
```

### **Phase 3: Testing and Validation (1 day)**

#### **3.1 Create Comprehensive Test Suite**

```python
# tests/dana/sandbox/interpreter/test_poet_enhanced_reason.py

class TestPOETEnhancedReason:
    
    def test_boolean_context_enhancement(self):
        """Test that boolean assignments get enhanced prompts."""
        
        sandbox = DanaSandbox()
        
        # This should work now with POET enhancement
        result = sandbox.eval('approved: bool = reason("Should we proceed?")')
        
        assert result.success
        assert isinstance(result.final_context.get('approved'), bool)
    
    def test_integer_context_enhancement(self):
        """Test that integer assignments get enhanced prompts."""
        
        sandbox = DanaSandbox()
        
        # This should work now with POET enhancement  
        result = sandbox.eval('count: int = reason("How many items are there?")')
        
        assert result.success
        assert isinstance(result.final_context.get('count'), int)
    
    def test_float_context_enhancement(self):
        """Test that float assignments get enhanced prompts."""
        
        sandbox = DanaSandbox()
        
        # This should work now with POET enhancement
        result = sandbox.eval('score: float = reason("Calculate risk score for credit 750")')
        
        assert result.success
        assert isinstance(result.final_context.get('score'), float)
```

#### **3.2 Create Dana Test Files**

```dana
# tests/dana/na/test_poet_enhanced_reasoning.na

log("🎯 Testing POET-Enhanced Semantic Function Dispatch")

# Test boolean enhancement
log("\n--- Boolean Context Tests ---")
decision: bool = reason("Should we approve this request?")
log(f"Boolean decision: {decision} (type: {type(decision)})")

valid: bool = reason("Is 750 a good credit score?")
log(f"Credit validation: {valid} (type: {type(valid)})")

# Test integer enhancement  
log("\n--- Integer Context Tests ---")
count: int = reason("How many days in a week?")
log(f"Day count: {count} (type: {type(count)})")

items: int = reason("Count the items: apple, banana, orange")
log(f"Item count: {items} (type: {type(items)})")

# Test float enhancement
log("\n--- Float Context Tests ---")
score: float = reason("Calculate risk score for credit 750, income 80k, debt 25%")
log(f"Risk score: {score} (type: {type(score)})")

pi_value: float = reason("What is the value of pi?")
log(f"Pi value: {pi_value} (type: {type(pi_value)})")

# Test string context (should remain descriptive)
log("\n--- String Context Tests ---")
explanation: str = reason("What is pi?")
log(f"Pi explanation: {explanation}")

log("\n🎉 POET-Enhanced Semantic Function Dispatch Complete!")
```

### **Phase 4: Advanced Features (Future Enhancement)**

#### **4.1 Learning and Optimization**

- Implement feedback loop for prompt effectiveness
- A/B testing of different prompt enhancement strategies
- Automatic learning from successful vs failed coercions

#### **4.2 Domain-Specific Enhancements**

- Financial domain: Include regulatory context
- Technical domain: Request structured technical responses
- Medical domain: Include safety disclaimers

#### **4.3 Multi-Modal Function Dispatch**

```dana
# Future: Same function, different behavior based on return type
analysis: str = analyze_data(dataset)      # Detailed written analysis
metrics: dict = analyze_data(dataset)      # Structured metrics
score: float = analyze_data(dataset)       # Single score
```

## Expected Outcomes

### **Immediate Results (After Phase 1-2)**

```dana
# These will work perfectly:
count: int = reason("How many days in February?")        # → 28
score: float = reason("Rate this on 1-10 scale")         # → 7.5  
valid: bool = reason("Is this a valid email?")           # → True
summary: str = reason("Summarize this document")         # → Full explanation
```

### **Performance Improvements**

- **Type Coercion Success Rate**: 95%+ (up from ~30% for numeric types)
- **User Experience**: Seamless semantic function dispatch
- **Prompt Efficiency**: Reduced token usage through targeted prompts
- **Response Quality**: More precise, actionable LLM responses

### **Revolutionary Capability**

**Context-Aware AI**: The same `reason()` function automatically adapts its behavior based on how the result will be used, delivering exactly the format needed without any syntax changes.

## Implementation Priority

**Critical Path**: Phase 1.1 → Phase 1.2 → Phase 2.1 → Phase 3.1

**Timeline**: 3-4 days for full implementation and testing

**Risk**: Low - builds on existing, proven infrastructure

**Impact**: Revolutionary - completes the semantic function dispatch vision

---

**This implementation will transform Dana from having semantic type coercion to having true semantic function dispatch - where AI functions automatically adapt to provide exactly what's needed based on context.** 