# Design Document: Struct Implementation for Dana Language

```text
Author: Christopher Nguyen
Version: 0.5
Date: 2025-06-09
Status: Design Phase
```

## Problem Statement

Dana language currently lacks struct support despite being documented and referenced in the language specification. Users cannot define custom data structures, limiting the language's expressiveness and forcing workarounds using dictionaries. This impacts:

- **Code clarity**: Complex data represented as dictionaries lacks type safety
- **Developer experience**: No IDE support for field completion or validation  
- **Language completeness**: Core language feature missing from implementation
- **AI integration**: LLMs cannot leverage structured data types effectively

Without struct support, Dana cannot fulfill its promise as a domain-aware language for complex agent interactions.

## Goals

- **Implement complete struct functionality** following Go's approach (data only, no methods)
- **Enable external functions** with multiple signatures based on first argument type
- **Ensure seamless integration** with existing Dana type system and execution model
- **Maintain performance** comparable to dictionary operations
- **Support polymorphic functions** operating on struct types via function dispatch

## Non-Goals

- Struct inheritance or complex OOP features (following Go's simplicity)
- Methods defined within structs (external functions only, like Go)
- Immutable structs (all structs mutable by default)
- Complex generic types or templating
- Breaking changes to existing code

## Proposed Solution

Implement structs following Go's design philosophy:

1. **Structs contain only data** (fields with types)
2. **Functions operate on structs externally** via polymorphic dispatch
3. **Multiple function signatures** with struct type as first parameter
4. **Runtime type-based function selection**

### User Experience Examples

Here's how developers will use structs in Dana:

#### Basic Struct Definition and Usage
```dana
# Define domain-specific data structures
struct UserProfile:
    user_id: str
    display_name: str
    email: str
    is_active: bool
    preferences: dict

struct Document:
    id: str
    title: str
    content: str
    created_at: str
    tags: list

# Create instances with named arguments
user = UserProfile(
    user_id="usr_123",
    display_name="Alice Developer",
    email="alice@example.com",
    is_active=true,
    preferences={"theme": "dark", "notifications": true}
)

doc = Document(
    id="doc_456",
    title="Project Readme",
    content="This is a comprehensive guide...",
    created_at="2025-01-09",
    tags=["documentation", "guide"]
)

# Field access and modification
log(f"Welcome {user.display_name}!")
user.email = "alice.developer@example.com"
doc.tags.append("important")
```

#### Polymorphic Functions (Go-style Methods)
```dana
# Define functions that operate on different struct types
def validate(user: UserProfile) -> bool:
    return "@" in user.email and len(user.user_id) > 0

def validate(doc: Document) -> bool:
    return len(doc.title) > 0 and len(doc.content) > 10

def analyze(user: UserProfile, metric: str) -> dict:
    return {
        "engagement": user.preferences.get("notifications", false),
        "activity": user.is_active
    }

def analyze(doc: Document, metric: str) -> dict:
    return {
        "readability": len(doc.content.split()) / 100,
        "categorization": len(doc.tags)
    }

# Function dispatch based on first argument type
user_valid = validate(user)      # Calls validate(user: UserProfile)
doc_valid = validate(doc)        # Calls validate(doc: Document)

user_metrics = analyze(user, "engagement")  # UserProfile version
doc_metrics = analyze(doc, "readability")   # Document version
```

#### Method-like Syntax (Syntactic Sugar)
```dana
# These are equivalent ways to call functions:
result1 = validate(user)        # Direct function call
result2 = user.validate()       # Method-like syntax

analysis1 = analyze(doc, "readability")     # Direct function call  
analysis2 = doc.analyze("readability")     # Method-like syntax

# Works with variadic arguments too
def search(doc: Document, *terms: str, **options: any) -> list:
    case_sensitive = options.get("case_sensitive", false)
    results = []
    for term in terms:
        if case_sensitive:
            matches = find_exact_matches(doc.content, term)
        else:
            matches = find_case_insensitive_matches(doc.content, term)
        results.extend(matches)
    return results

# Both calling styles work:
matches1 = search(doc, "guide", "comprehensive", case_sensitive=true)
matches2 = doc.search("guide", "comprehensive", case_sensitive=true)
```

#### Real-World Agent Integration
```dana
# AI-powered struct processing
struct AnalysisRequest:
    data_source: str
    analysis_type: str
    parameters: dict
    priority: int

def process(request: AnalysisRequest) -> dict:
    # AI-powered analysis based on request type
    analysis_prompt = f"Analyze {request.data_source} for {request.analysis_type}"
    
    result = reason(analysis_prompt, {
        "parameters": request.parameters,
        "priority": request.priority
    })
    
    return {
        "analysis": result,
        "timestamp": get_current_time(),
        "status": "completed"
    }

def process(user: UserProfile) -> dict:
    # User-specific processing
    recommendations = reason(
        f"Generate personalized recommendations for {user.display_name}",
        {"preferences": user.preferences, "activity": user.is_active}
    )
    
    return {
        "recommendations": recommendations,
        "user_id": user.user_id
    }

# Usage in agent workflows
analysis_req = AnalysisRequest(
    data_source="user_behavior_logs",
    analysis_type="engagement_patterns",
    parameters={"timeframe": "30_days"},
    priority=1
)

# Polymorphic dispatch handles the right function
user_insights = process(user)           # UserProfile version
analysis_results = process(analysis_req) # AnalysisRequest version

# Method syntax works naturally
quick_analysis = analysis_req.process()
```

#### Integration with Existing Dana Features
```dana
# Struct instances work with all Dana features
struct ProcessingStep:
    name: str
    input_type: str
    output_type: str
    config: dict

def execute(step: ProcessingStep, data: any) -> any:
    log(f"Executing step: {step.name}")
    # Implementation based on step configuration
    return transformed_data

# Pipeline composition with structs
validation_step = ProcessingStep(
    name="data_validation",
    input_type="raw_data",
    output_type="validated_data", 
    config={"strict_mode": true}
)

analysis_step = ProcessingStep(
    name="statistical_analysis",
    input_type="validated_data",
    output_type="analysis_results",
    config={"confidence_level": 0.95}
)

# Struct instances in pipelines
processed_data = raw_data | validation_step.execute | analysis_step.execute

# Struct instances in scopes
private:user_session = UserProfile(...)
public:system_config = ProcessingStep(...)

# LLM integration with struct types
enhanced_user = reason(
    "Enhance user profile with AI-generated insights",
    {"input": user, "__dana_desired_type": UserProfile}
)
```

### High-Level Approach

```dana
# Struct definition (data only, like Go)
struct Point:
    x: int
    y: int

struct Document:
    name: str
    content: str

# External functions with multiple signatures (polymorphic)
def scan(document: Document, pattern: str) -> list:
    # Scan document content for pattern
    return matches

def scan(image: Image, threshold: float) -> dict:
    # Scan image for features
    return features

# Usage - function dispatch based on first argument type
doc = Document(name="readme.txt", content="Hello world")
results = scan(doc, "Hello")  # Calls scan(document: Document, ...)

# Syntactic sugar: struct.function() calls function(struct, ...)
results = doc.scan("Hello")   # Equivalent to scan(doc, "Hello")
```

### Struct Method Signature Rules

**Critical Contract: For polymorphic struct methods, the struct type MUST be the first named parameter.**

```dana
# ✅ Valid struct method signatures
def scan(doc: Document, pattern: str) -> list:                    # Basic struct method
def scan(doc: Document, *patterns: str) -> list:                  # With variadic args
def scan(doc: Document, pattern: str, **options: any) -> list:    # With keyword args
def scan(doc: Document, *patterns: str, **options: any) -> list:  # With both variadic

# ❌ Invalid struct method signatures
def scan(*args, doc: Document) -> list:          # Struct not first named parameter
def scan(**kwargs) -> list:                      # No way to identify struct type
def scan(pattern: str, doc: Document) -> list:   # Struct not first parameter
```

**Rationale**: The first named parameter determines the struct type for polymorphic dispatch. Variadic arguments (`*args`, `**kwargs`) don't interfere with this rule since they're not "named" parameters in the signature.

This follows Go's receiver-based method approach where the receiver type (first parameter) determines method dispatch.

## Proposed Design

### System Architecture

```
Dana Grammar (.lark)
    ↓
AST Nodes (StructDefinition, StructLiteral)
    ↓
Parser/Transformer (StructTransformer)
    ↓
Type System (StructType registration)
    ↓
Function Dispatch (Type-based function selection)
    ↓
Execution Engine (StructExecutor)
    ↓
Runtime Objects (StructInstance)
```

### Core Components

#### 1. Grammar Extensions (`dana_grammar.lark`)

```lark
compound_stmt: struct_def | if_stmt | while_stmt | ...

struct_def: "struct" NAME ":" block
struct_field: NAME ":" basic_type

# Struct instantiation
atom: struct_literal | variable | NUMBER | ...
struct_literal: NAME "(" [struct_arguments] ")"
struct_arguments: struct_arg ("," struct_arg)*
struct_arg: NAME "=" expr

# Method-like syntax (syntactic sugar)
trailer: "(" [arguments] ")" | "[" expr "]" | "." NAME
```

#### 2. AST Node Definitions

```python
@dataclass
class StructDefinition(Statement):
    name: str
    fields: list[StructField]
    location: SourceLocation

@dataclass
class StructField:
    name: str
    type_hint: TypeHint
    location: SourceLocation

@dataclass  
class StructLiteral(Expression):
    struct_name: str
    arguments: list[StructArgument]
    location: SourceLocation

@dataclass
class StructArgument:
    name: str
    value: Expression
    location: SourceLocation
```

#### 3. Type System Integration

```python
class StructType:
    def __init__(self, name: str, fields: dict[str, TypeHint]):
        self.name = name
        self.fields = fields
        
    def validate_instantiation(self, args: dict[str, Any]) -> bool:
        # Validate required fields and types
        
class StructTypeRegistry:
    _types: dict[str, StructType] = {}
    
    @classmethod
    def register(cls, struct_type: StructType):
        cls._types[struct_type.name] = struct_type
```

#### 4. Function Dispatch System (Go-style)

```python
class FunctionDispatcher:
    """Handles polymorphic function dispatch based on first named parameter type"""
    
    def __init__(self):
        self._functions: dict[str, list[DanaFunction]] = {}
    
    def register_function(self, func: DanaFunction):
        """Register function with its signature"""
        self._functions.setdefault(func.name, []).append(func)
    
    def find_function(self, name: str, args: list[Any]) -> DanaFunction:
        """Find matching function based on first named parameter type"""
        candidates = self._functions.get(name, [])
        
        for func in candidates:
            if self._signature_matches_with_variadic(func, args):
                return func
        
        raise FunctionNotFoundError(f"No function '{name}' matches argument types")
    
    def _signature_matches_with_variadic(self, func: DanaFunction, args: list[Any]) -> bool:
        """Check if function signature matches provided arguments (handles *args/**kwargs)"""
        named_params = func.get_named_parameters()  # Excludes *args/**kwargs
        
        # First named parameter must be struct type for struct methods
        if args and isinstance(args[0], StructInstance):
            if not named_params or named_params[0].type_hint.name != args[0]._type.name:
                return False
        
        # Check if remaining args can be satisfied by the signature
        return self._can_satisfy_signature(func, args)
    
    def _can_satisfy_signature(self, func: DanaFunction, args: list[Any]) -> bool:
        """Check if args can satisfy function signature with variadic support"""
        named_params = func.get_named_parameters()
        min_args = len([p for p in named_params if not p.has_default])
        max_args = len(named_params) if not func.has_variadic_args() else float('inf')
        
        return min_args <= len(args) <= max_args
```

#### 5. Runtime Representation

```python
class StructInstance:
    """Runtime representation of struct instance (Go-style data container)"""
    
    def __init__(self, struct_type: StructType, values: dict[str, Any]):
        self._type = struct_type
        self._values = values
        
    def __getattr__(self, name: str) -> Any:
        """Field access"""
        if name in self._type.fields:
            return self._values.get(name)
        raise AttributeError(f"'{self._type.name}' has no field '{name}'")
        
    def __setattr__(self, name: str, value: Any):
        """Field assignment"""
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in self._type.fields:
            self._values[name] = value
        else:
            raise AttributeError(f"'{self._type.name}' has no field '{name}'")
    
    def call_method(self, method_name: str, args: list[Any]) -> Any:
        """Syntactic sugar: struct.method() -> method(struct, ...)"""
        dispatcher = get_function_dispatcher()
        func = dispatcher.find_function(method_name, [self] + args)
        return func.execute([self] + args)
```

### Data Models and APIs

#### Struct Definition Processing
1. **Parse struct definition** → `StructDefinition` AST node
2. **Extract field information** → `StructField` list with type hints
3. **Register struct type** → `StructTypeRegistry.register()`
4. **Store for runtime access** → Available for instantiation

#### Function Registration and Dispatch
```python
# Multiple function signatures for same name
def process_document(doc: Document, action: str) -> str:
    return f"Processing document {doc.name} with action {action}"

def process_document(doc: Document, config: ProcessConfig) -> Result:
    return process_with_config(doc, config)

def process_image(img: Image, filters: list) -> Image:
    return apply_filters(img, filters)

# Registration happens automatically during function definition parsing
# Dispatch happens at call time based on argument types
```

#### Method-like Syntax (Syntactic Sugar)
```python
# These are equivalent:
result1 = scan(document, "pattern")      # Direct function call
result2 = document.scan("pattern")       # Method-like syntax

# Implementation: document.scan("pattern") transforms to scan(document, "pattern")
```

### Error Handling

```python
class StructDefinitionError(DanaRuntimeError):
    """Raised when struct definition is invalid"""
    
class StructInstantiationError(DanaRuntimeError):
    """Raised when struct instantiation fails"""
    
class StructFieldError(DanaRuntimeError):
    """Raised when accessing invalid struct field"""

class FunctionDispatchError(DanaRuntimeError):
    """Raised when no matching function found for given types"""
```

Error messages follow Dana standard:
```
"Function dispatch failed: No function 'scan' accepts arguments (Document, int). 
Available signatures: scan(Document, str), scan(Image, float). 
Check argument types or define matching function signature."
```

## Proposed Implementation

### Technical Specifications

#### Phase 1: Foundation & Grammar (Week 1)
```python
# 1. Grammar extension - struct definitions only (no methods)
struct_def: "struct" NAME ":" _NL _INDENT struct_fields _DEDENT
struct_fields: struct_field+
struct_field: NAME ":" basic_type _NL

# 2. AST nodes for data-only structs
@dataclass
class StructDefinition(Statement):
    name: str
    fields: list[StructField]  # No methods, fields only
    location: SourceLocation
```

#### Phase 2: Function Dispatch System (Week 2)
```python
# 1. Function dispatcher for polymorphic functions
class PolymorphicFunctionRegistry:
    def register(self, name: str, signature: FunctionSignature, impl: Callable):
        pass
    
    def dispatch(self, name: str, args: list[Any]) -> Callable:
        pass

# 2. Integration with existing function system
def execute_function_call(self, node: FunctionCall) -> Any:
    # Try polymorphic dispatch first
    if args and isinstance(args[0], StructInstance):
        func = polymorphic_registry.dispatch(node.name, args)
        return func(*args)
    # Fall back to regular function lookup
    return regular_function_call(node)
```

#### Phase 3: Method Syntax Sugar (Week 3)
```python
# Transform obj.method(args) → method(obj, args)
def execute_attribute_access_call(self, obj: Any, method: str, args: list[Any]) -> Any:
    if isinstance(obj, StructInstance):
        # Syntactic sugar: obj.method(args) becomes method(obj, args)
        return self.execute_function_call(method, [obj] + args)
    else:
        # Regular attribute access
        return getattr(obj, method)(*args)
```

#### Phase 4: Integration & Optimization (Week 4)
```python
# 1. Performance optimization for function dispatch
class CachedFunctionDispatcher:
    def __init__(self):
        self._cache: dict[tuple, DanaFunction] = {}
    
    def dispatch(self, name: str, arg_types: tuple) -> DanaFunction:
        cache_key = (name, arg_types)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        func = self._find_function(name, arg_types)
        self._cache[cache_key] = func
        return func
```

### Key Algorithms

#### Function Dispatch Algorithm (Go-style)
```python
def dispatch_function(name: str, args: list[Any]) -> DanaFunction:
    """
    Dispatch function based on argument types, prioritizing first argument
    (following Go's receiver-based method dispatch)
    """
    candidates = function_registry.get_functions(name)
    
    # 1. Try exact type matches first
    for func in candidates:
        if exact_signature_match(func, args):
            return func
    
    # 2. Try compatible type matches (with coercion)
    for func in candidates:
        if compatible_signature_match(func, args):
            return func
    
    # 3. No match found
    available_sigs = [func.signature_string() for func in candidates]
    provided_types = [type(arg).__name__ for arg in args]
    
    raise FunctionDispatchError(
        f"No function '{name}' matches types ({', '.join(provided_types)}). "
        f"Available: {', '.join(available_sigs)}"
    )

def exact_signature_match(func: DanaFunction, args: list[Any]) -> bool:
    """Check if arguments exactly match function signature"""
    if len(args) != len(func.parameters):
        return False
    
    for param, arg in zip(func.parameters, args):
        if isinstance(arg, StructInstance):
            if param.type_hint.name != arg._type.name:
                return False
        elif type(arg) != param.type_hint.python_type:
            return False
    
    return True
```

#### Method Syntax Transformation
```python
def transform_method_call(obj_expr: Expression, method_name: str, args: list[Expression]) -> FunctionCall:
    """
    Transform obj.method(args) into method(obj, args)
    This provides Go-style method syntax while keeping functions external
    """
    return FunctionCall(
        name=method_name,
        arguments=[obj_expr] + args,
        location=obj_expr.location
    )
```

### Testing Strategy

#### Unit Tests
```python
def test_struct_definition():
    """Test basic struct definition parsing"""
    code = """
    struct Point:
        x: int
        y: int
    """
    ast = parse_dana_code(code)
    struct_def = ast.statements[0]
    assert isinstance(struct_def, StructDefinition)
    assert struct_def.name == "Point"
    assert len(struct_def.fields) == 2

def test_function_dispatch():
    """Test polymorphic function dispatch"""
    code = """
    struct Point:
        x: int
        y: int
    
    struct User:
        name: str
    
    def describe(point: Point) -> str:
        return f"Point({point.x}, {point.y})"
    
    def describe(user: User) -> str:
        return f"User: {user.name}"
    
    p = Point(x=5, y=10)
    u = User(name="Alice")
    
    point_desc = describe(p)
    user_desc = describe(u)
    """
    result = execute_dana_code(code)
    assert result.get_variable('point_desc') == "Point(5, 10)"
    assert result.get_variable('user_desc') == "User: Alice"

def test_method_syntax_sugar():
    """Test obj.method() → method(obj) transformation"""
    code = """
    struct Document:
        content: str
    
    def scan(doc: Document, pattern: str) -> bool:
        return pattern in doc.content
    
    doc = Document(content="Hello world")
    found1 = scan(doc, "Hello")      # Direct call
    found2 = doc.scan("Hello")       # Method syntax
    """
    result = execute_dana_code(code)
    assert result.get_variable('found1') == True
    assert result.get_variable('found2') == True
```

### Dependencies

- **Core Language**: Dana grammar, AST, parser, transformer infrastructure
- **Function System**: Enhanced function registry for polymorphic dispatch
- **Type System**: Existing type hint and basic type support
- **Error Handling**: Dana exception hierarchy

### Monitoring & Validation

- **Performance benchmarks**: Compare struct vs dictionary performance
  - Target: Struct field access within 10% of dict access time
  - Target: Struct instantiation within 15% of dict creation time
  - Measurement: Use pytest-benchmark for consistent timing
- **Memory usage tracking**: Monitor memory overhead of struct instances
  - Target: Memory overhead < 20% compared to equivalent dictionaries
  - Measurement: Use memory_profiler for heap analysis
- **Error rate monitoring**: Track struct-related runtime errors
- **Type validation metrics**: Monitor type coercion success/failure rates

## Design Review Checklist

- [x] **Security review completed**: No execution of untrusted code, safe field access
- [x] **Performance impact assessed**: Minimal overhead compared to dictionaries
- [x] **Error handling comprehensive**: Clear error messages and recovery paths
- [x] **Testing strategy defined**: Unit, integration, and performance tests planned
- [x] **Documentation planned**: Grammar, API, and usage examples defined
- [x] **Backwards compatibility checked**: No breaking changes to existing code

## Implementation Phases

### Phase 1: Foundation & Architecture
- [ ] Define core components and interfaces
- [ ] Extend Dana grammar with struct definitions (data only)
- [ ] Create AST node classes for structs
- [ ] Establish architectural patterns for function dispatch

### Phase 2: Core Functionality
- [ ] Implement struct instantiation and field access
- [ ] Create polymorphic function registry system
- [ ] Focus on happy path scenarios for basic operations
- [ ] Create working examples of struct usage

### Phase 3: Error Handling & Edge Cases
- [ ] Add comprehensive error detection for struct operations
- [ ] Test failure scenarios (invalid fields, type mismatches)
- [ ] Handle edge cases in function dispatch
- [ ] Implement clear, actionable error messages

### Phase 4: Advanced Features & Integration
- [ ] Implement obj.method() → method(obj) transformation
- [ ] Add sophisticated function dispatch with caching
- [ ] Test complex interactions with existing Dana features
- [ ] Ensure seamless integration with type system

### Phase 5: Integration & Performance Testing
- [ ] Test real-world scenarios with complex struct hierarchies
- [ ] Validate performance benchmarks vs dictionaries
- [ ] Run regression tests against existing functionality
- [ ] Comprehensive unit test suite (>90% coverage)

### Phase 6: Polish & Documentation
- [ ] Update language specification documents
- [ ] Create migration guides and usage examples
- [ ] Update VSCode syntax highlighting
- [ ] Final validation and sign-off

**Completion Criteria for Each Phase:**
- ✅ 100% test pass rate for implemented features
- ✅ No regressions in existing functionality  
- ✅ Error handling covers all failure scenarios
- ✅ Documentation updated for new features
- ✅ Performance within 10% of baseline (dictionaries)

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "struct_design_doc", "content": "Create comprehensive struct implementation design document", "status": "completed", "priority": "high"}]