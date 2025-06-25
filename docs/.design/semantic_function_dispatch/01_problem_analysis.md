# Semantic Type Coercion Design Specification for Dana

## Design Philosophy

Dana's semantic type coercion should follow the **"Do What I Mean" (DWIM)** philosophy while maintaining **predictability** and **type safety**. The system should be:

1. **Context-Aware**: Consider the intended use context (type hints, operators, function expectations)
2. **Semantically Intelligent**: Understand natural language patterns beyond exact matches
3. **Consistent**: Same input produces same output in equivalent contexts
4. **Safe**: Prefer explicit errors over silent unexpected behavior
5. **Configurable**: Allow users to control coercion aggressiveness

## Core Design Principles

### 1. **Context-Driven Coercion**

Type coercion behavior should be influenced by the **intended target type**:

```dana
# Type hint should guide coercion strategy
decision: bool = reason("Should we proceed?")    # "yes" → True, "no" → False  
count: int = reason("How many items?")           # "5" → 5, "zero" → 0
temperature: float = reason("What's the temp?")  # "98.6" → 98.6, "normal" → ???
name: str = reason("What's your name?")          # Always remains string
```

**Principle**: The declared type hint is the primary signal for coercion strategy.

### 2. **Hierarchical Coercion Strategy**

Coercion should follow a clear hierarchy:

1. **Type Hint Context** (highest priority)
2. **Operator Context** (binary operations, comparisons)
3. **Function Context** (LLM functions vs regular functions)
4. **Default Behavior** (conservative, safety-first)

### 3. **Enhanced Semantic Pattern Matching**

Beyond exact matches, support partial semantic understanding:

```dana
# Current: Only exact matches
"yes" → True ✓
"no" → False ✓
"maybe" → string ✗

# Proposed: Partial semantic matching
"yes please" → True (contains positive signal)
"no way" → False (contains negative signal)  
"absolutely not" → False (strong negative)
"sure thing" → True (strong positive)
"definitely" → True (strong positive)
"never" → False (strong negative)
```

**Principle**: Detect semantic intent even in conversational responses.

### 4. **Consistent Zero and Numeric Handling**

All zero representations should behave consistently within the same type context:

```dana
# Boolean context - all should be False
bool("0") → False
bool("0.0") → False
bool("-0") → False
bool("false") → False

# Numeric context - preserve type precision
int("0") → 0
float("0.0") → 0.0
int("-0") → 0
```

**Principle**: Semantic equivalence should produce consistent results.

## Proposed Behavior Specifications

### Boolean Coercion

#### Positive Indicators (→ True)
- **Exact**: `"true"`, `"yes"`, `"1"`, `"ok"`, `"correct"`, `"valid"`, `"right"`
- **Partial**: `"yes please"`, `"sure thing"`, `"absolutely"`, `"definitely"`, `"of course"`
- **Conversational**: `"yep"`, `"yeah"`, `"sure"`, `"okay"`

#### Negative Indicators (→ False)  
- **Exact**: `"false"`, `"no"`, `"0"`, `"incorrect"`, `"invalid"`, `"wrong"`
- **Partial**: `"no way"`, `"absolutely not"`, `"definitely not"`, `"never"`
- **Conversational**: `"nope"`, `"nah"`, `"not really"`

#### Ambiguous Cases (→ String, with warning?)
- `"maybe"`, `"perhaps"`, `"sometimes"`, `"depends"`

### Numeric Coercion

#### Integer Context
```dana
count: int = "5" → 5
count: int = "zero" → 0  
count: int = "3.14" → ERROR (lossy conversion)
count: int = "five" → ERROR (complex parsing not supported)
```

#### Float Context  
```dana
temp: float = "98.6" → 98.6
temp: float = "5" → 5.0 (safe upward conversion)
temp: float = "normal" → ERROR (semantic but non-numeric)
```

### String Coercion
Always safe - any value can become a string:
```dana
message: str = 42 → "42"
message: str = True → "true"  
message: str = [1,2,3] → "[1, 2, 3]"
```

## Context-Specific Behaviors

### Assignment Context
```dana
# Type hint drives coercion strategy
approved: bool = reason("Is it approved?")  # Prioritize boolean coercion
count: int = reason("How many?")            # Prioritize numeric coercion
```

### Binary Operation Context  
```dana
# Operator suggests intended types
"5" + 3 → 8 (numeric promotion)
"5" + " items" → "5 items" (string concatenation)
"yes" == True → True (boolean comparison)
```

### Function Call Context
```dana
# LLM functions get enhanced semantic coercion
reason("proceed?") → smart boolean coercion
ask_ai("count?") → smart numeric coercion

# Regular functions get standard coercion  
len("hello") → 5 (no special LLM handling)
```

## Error Handling Strategy

### Graceful Degradation
1. **Try context-appropriate coercion**
2. **If fails, try generic coercion**  
3. **If fails, provide clear error with suggestions**

### Error Message Template
```
"Cannot coerce '{value}' to {target_type} in {context}. 
 Attempted: {coercion_attempts}
 Suggestion: {helpful_suggestion}
 Similar valid values: {examples}"
```

Example:
```
Cannot coerce 'maybe' to bool in assignment context.
Attempted: exact match, partial semantic match
Suggestion: Use explicit values like 'yes'/'no' or 'true'/'false'
Similar valid values: "yes", "no", "true", "false"
```

## Configuration Options

### Environment Variables
```bash
DANA_SEMANTIC_COERCION=strict|normal|aggressive  # Default: normal
DANA_PARTIAL_MATCHING=true|false                 # Default: true  
DANA_CONVERSATIONAL_PATTERNS=true|false          # Default: false
DANA_COERCION_WARNINGS=true|false                # Default: true
```

### Programmatic Control
```dana
# Per-context configuration
with coercion_mode("strict"):
    result = risky_operation()

# Global configuration  
configure_coercion(semantic_matching=True, warnings=True)
```

## Implementation Strategy

### Phase 1: Foundation
1. **Unified TypeCoercion class** with context awareness
2. **Fix existing inconsistencies** (zero handling, context conflicts)
3. **Add type hint integration** in assignment handler

### Phase 2: Enhanced Semantics  
1. **Partial pattern matching** for boolean coercion
2. **Conversational pattern recognition**
3. **Improved error messages** with suggestions

### Phase 3: Advanced Features
1. **Configurable coercion modes**
2. **Context-specific optimization**
3. **Performance improvements** and caching

## Breaking Changes

### Expected Breaking Changes
1. **Zero handling**: `"0"` may become consistently `False` in boolean contexts
2. **Type hint enforcement**: Stricter type checking with type hints
3. **LLM function behavior**: Enhanced coercion may change existing behavior

### Migration Strategy
1. **Deprecation warnings** for ambiguous cases
2. **Configuration flags** to maintain old behavior temporarily
3. **Clear migration guide** with before/after examples

## Test Requirements

### Core Test Cases
```dana
# Context-dependent behavior
decision: bool = "yes" → True
count: int = "yes" → ERROR  

# Partial semantic matching
response: bool = "no way" → False
response: bool = "absolutely" → True

# Consistency across contexts
if "0": → False
bool("0") → False  
"0" == False → True
```

### Edge Cases
- Mixed language responses
- Scientific notation
- Unicode and special characters
- Very long strings
- Performance with large datasets

---

## Questions for Agreement

1. **Should we support conversational patterns** like "yep", "nah"?
2. **How aggressive should partial matching be?** (e.g., "not really" → False?)
3. **Should type hints be mandatory** for reliable coercion?
4. **What's the breaking change tolerance?** Can we change existing behavior?
5. **Should we add coercion warnings** for ambiguous cases?

**Please review and let me know which aspects you'd like to modify or discuss further.** 