# Parameter Orchestration - Intelligent Parameter Matching

## Overview

Parameter orchestration enables intelligent parameter passing in function composition pipelines, automatically handling tuple unpacking, named parameter matching, type-guided assignment, and context injection.

## Current Parameter Passing (Foundation)

### Sequential Composition
```dana
# Current: Simple positional passing
def add_ten(x): return x + 10
def double(x): return x * 2

result = 5 | add_ten | double  # double(add_ten(5))
```

### Parallel Composition (Phase 1)
```dana  
# Phase 1: Simple list passing
def sum_all(numbers): return sum(numbers)

result = 5 | { add_ten, double } | sum_all  # sum_all([15, 10])
```

## Enhanced Parameter Orchestration (Phase 2+)

### 1. Tuple Unpacking (Phase 2)

#### Basic Tuple Unpacking
```dana
def get_dimensions(): return (10, 20, 5)  # Returns (width, height, depth)
def calculate_volume(width, height, depth): return width * height * depth

# Automatic tuple unpacking
volume = get_dimensions | calculate_volume
# Runtime: calculate_volume(*get_dimensions()) → calculate_volume(10, 20, 5)
```

#### Mixed Parameter Sources
```dana
def get_user_data(user_id): return ("Alice", 25)  # Returns (name, age)
def create_profile(name, age, department="Engineering"): return f"{name}, {age}, {department}"

# Tuple unpacking + default parameters
profile = "user123" | get_user_data | create_profile
# Runtime: create_profile("Alice", 25, department="Engineering")
```

### 2. Named Parameter Matching (Phase 2)

#### Parameter Name Matching
```dana
def fetch_order(): return {"order_id": 123, "customer": "Bob", "amount": 99.99}
def process_payment(amount, customer, tax_rate=0.08): 
    return amount * (1 + tax_rate)

# Smart parameter matching by name
total = fetch_order | process_payment
# Runtime: process_payment(amount=99.99, customer="Bob", tax_rate=0.08)
```

#### Flexible Parameter Mapping
```dana
def get_coordinates(): return {"x": 10, "y": 20}
def calculate_distance(x1, y1, x2=0, y2=0): return ((x1-x2)**2 + (y1-y2)**2)**0.5

# Maps x→x1, y→y1, uses defaults for x2, y2
distance = get_coordinates | calculate_distance
# Runtime: calculate_distance(x1=10, y1=20, x2=0, y2=0)
```

### 3. Context Injection (Phase 2)

#### Automatic Context Parameter Injection
```dana
# Context variables
private:api_key = "secret123"
public:base_url = "https://api.example.com"

def make_request(endpoint, api_key, base_url):
    return f"GET {base_url}/{endpoint} with key {api_key}"

def get_endpoint(): return "users"

# Context injection for missing parameters
result = get_endpoint | make_request
# Runtime: make_request("users", api_key="secret123", base_url="https://api.example.com")
```

#### Scoped Variable Resolution Order
```dana
# Resolution priority: local: > private: > public: > default
local:timeout = 5
private:timeout = 10
public:timeout = 30

def api_call(endpoint, timeout): return f"Call {endpoint} with timeout {timeout}"

result = "users" | api_call  # Uses local:timeout = 5
```

### 4. Type-Guided Matching (Phase 3)

#### Type-Based Parameter Assignment
```dana
def get_mixed_data(): return (42, "hello", 3.14, True)
def process_data(count: int, message: str, flag: bool, rate: float):
    return f"{message}: {count} items at {rate} with flag {flag}"

# Type-guided parameter reordering
result = get_mixed_data | process_data
# Runtime: process_data(count=42, message="hello", flag=True, rate=3.14)
```

#### Struct/Object Property Mapping
```dana
struct UserData:
    name: str
    age: int
    email: str

def format_user(name: str, age: int): return f"{name} ({age})"

user = UserData("Alice", 30, "alice@example.com")
formatted = user | format_user
# Runtime: format_user(name="Alice", age=30) - auto-extracts matching fields
```

## Orchestration Engine Architecture

### 1. Parameter Analyzer (Phase 2)
```python
class ParameterAnalyzer:
    """Analyzes function signatures and parameter requirements"""
    
    def analyze_function(self, func: SandboxFunction) -> FunctionSignature:
        """Extract parameter information from function"""
        signature = FunctionSignature(
            name=func.name,
            parameters=[],
            return_type=None
        )
        
        # Extract parameter info using inspection
        for param in inspect.signature(func).parameters.values():
            signature.parameters.append(ParameterInfo(
                name=param.name,
                type=param.annotation,
                default=param.default,
                required=param.default == inspect.Parameter.empty
            ))
        
        return signature

@dataclass
class ParameterInfo:
    name: str
    type: Any = None
    default: Any = None
    required: bool = True

@dataclass  
class FunctionSignature:
    name: str
    parameters: List[ParameterInfo]
    return_type: Any = None
```

### 2. Parameter Orchestrator (Phase 2)
```python
class ParameterOrchestrator:
    """Orchestrates parameter matching and injection"""
    
    def __init__(self, context: SandboxContext):
        self.context = context
        self.analyzer = ParameterAnalyzer()
    
    def orchestrate_call(self, func: SandboxFunction, input_data: Any) -> Any:
        """Intelligently match parameters and execute function"""
        signature = self.analyzer.analyze_function(func)
        
        # Step 1: Extract available parameters from input
        available_params = self._extract_parameters(input_data)
        
        # Step 2: Match parameters to function signature
        matched_params = self._match_parameters(signature, available_params)
        
        # Step 3: Inject missing parameters from context
        final_params = self._inject_context_parameters(signature, matched_params)
        
        # Step 4: Execute function with orchestrated parameters
        return func.execute(self.context, **final_params)
    
    def _extract_parameters(self, input_data: Any) -> Dict[str, Any]:
        """Extract parameters from various input formats"""
        if isinstance(input_data, tuple):
            return self._extract_from_tuple(input_data)
        elif isinstance(input_data, dict):
            return input_data
        elif hasattr(input_data, '__dict__'):
            return self._extract_from_object(input_data)
        else:
            return {"arg0": input_data}  # Single positional argument
    
    def _match_parameters(self, signature: FunctionSignature, available: Dict[str, Any]) -> Dict[str, Any]:
        """Match available parameters to function signature"""
        matched = {}
        
        # Try name-based matching first
        for param in signature.parameters:
            if param.name in available:
                matched[param.name] = available[param.name]
        
        # Try type-based matching for unmatched parameters
        for param in signature.parameters:
            if param.name not in matched and param.type:
                for key, value in available.items():
                    if key not in matched.values() and isinstance(value, param.type):
                        matched[param.name] = value
                        break
        
        return matched
    
    def _inject_context_parameters(self, signature: FunctionSignature, matched: Dict[str, Any]) -> Dict[str, Any]:
        """Inject missing parameters from context"""
        final = matched.copy()
        
        for param in signature.parameters:
            if param.name not in final:
                # Try context injection in order: local: > private: > public:
                context_value = (
                    self.context.get(f"local:{param.name}") or
                    self.context.get(f"private:{param.name}") or  
                    self.context.get(f"public:{param.name}")
                )
                
                if context_value is not None:
                    final[param.name] = context_value
                elif param.default is not None:
                    final[param.name] = param.default
                elif param.required:
                    raise ParameterOrchestrationError(
                        f"Required parameter '{param.name}' not found in input or context"
                    )
        
        return final
```

### 3. Enhanced Parallel Execution (Phase 2)
```python
class SmartParallelComposedFunction(ParallelComposedFunction):
    """Parallel execution with intelligent parameter orchestration"""
    
    def __init__(self, functions: List[SandboxFunction], context: SandboxContext):
        super().__init__(functions, context)
        self.orchestrator = ParameterOrchestrator(context)
    
    def execute(self, context: SandboxContext, input_data: Any) -> List[Any]:
        """Execute parallel functions with smart parameter matching"""
        results = []
        
        with ThreadPoolExecutor(max_workers=len(self.functions)) as executor:
            futures = [
                executor.submit(self.orchestrator.orchestrate_call, func, input_data)
                for func in self.functions
            ]
            
            results = [future.result() for future in futures]
        
        return results
```

## Orchestration Strategies

### 1. Simple Positional (Phase 1)
```python
# Current implementation - simple positional passing
result = downstream_func(upstream_result)
```

### 2. Tuple Unpacking (Phase 2)  
```python
# Automatic tuple unpacking
if isinstance(upstream_result, tuple):
    result = downstream_func(*upstream_result)
else:
    result = downstream_func(upstream_result)
```

### 3. Smart Matching (Phase 2)
```python
# Intelligent parameter matching
orchestrator = ParameterOrchestrator(context)
result = orchestrator.orchestrate_call(downstream_func, upstream_result)
```

### 4. Adaptive Strategy (Phase 3)
```python
# Learn optimal strategies based on execution patterns
class AdaptiveOrchestrator(ParameterOrchestrator):
    def __init__(self, context: SandboxContext):
        super().__init__(context)
        self.execution_patterns = {}
        self.success_rates = {}
    
    def orchestrate_call(self, func: SandboxFunction, input_data: Any) -> Any:
        # Try learned strategy first, fallback to analysis
        strategy_key = (func.name, type(input_data).__name__)
        
        if strategy_key in self.execution_patterns:
            return self._execute_learned_strategy(func, input_data, strategy_key)
        else:
            return self._analyze_and_execute(func, input_data, strategy_key)
```

## Error Handling and Validation

### Parameter Validation
```python
class ParameterValidator:
    """Validates parameter compatibility and provides helpful errors"""
    
    def validate_orchestration(self, signature: FunctionSignature, params: Dict[str, Any]) -> bool:
        """Validate parameter orchestration before execution"""
        missing_required = []
        type_mismatches = []
        
        for param in signature.parameters:
            if param.required and param.name not in params:
                missing_required.append(param.name)
            elif param.name in params and param.type:
                if not isinstance(params[param.name], param.type):
                    type_mismatches.append(f"{param.name}: expected {param.type}, got {type(params[param.name])}")
        
        if missing_required:
            raise ParameterOrchestrationError(f"Missing required parameters: {missing_required}")
        if type_mismatches:
            raise ParameterOrchestrationError(f"Type mismatches: {type_mismatches}")
        
        return True
```

## Examples

### Complete Orchestration Examples

#### E-commerce Order Processing
```dana
# Complex data flow with multiple parameter sources
public:tax_rate = 0.08
private:payment_gateway = "stripe"

def fetch_order(order_id): return {"product": "laptop", "price": 999.99, "customer": "Alice"}
def calculate_tax(price, tax_rate): return price * tax_rate  
def process_payment(amount, gateway, customer): return f"Charged {amount} to {customer} via {gateway}"
def send_confirmation(customer, product): return f"Sent confirmation to {customer} for {product}"

# Multi-step orchestration
result = "order123" | fetch_order | { calculate_tax, process_payment, send_confirmation }
# Runtime automatically:
# 1. calculate_tax(price=999.99, tax_rate=0.08) - price from order, tax_rate from context
# 2. process_payment(amount=999.99, gateway="stripe", customer="Alice") - mixed sources  
# 3. send_confirmation(customer="Alice", product="laptop") - both from order data
```

#### Data Pipeline with Type Matching
```dana
def analyze_data(file_path): return (100, 0.95, ["warning", "info"], {"processed": True})
def generate_report(count: int, accuracy: float, status: dict): return f"Report: {count} items, {accuracy} accuracy, {status}"
def log_warnings(warnings: list): return f"Logged {len(warnings)} warnings"
def update_metrics(count: int, accuracy: float): return f"Updated metrics: {count}/{accuracy}"

# Type-guided parameter distribution
result = "data.csv" | analyze_data | { generate_report, log_warnings, update_metrics }
# Runtime intelligently distributes tuple (100, 0.95, ["warning", "info"], {"processed": True}):
# 1. generate_report(count=100, accuracy=0.95, status={"processed": True})
# 2. log_warnings(warnings=["warning", "info"])  
# 3. update_metrics(count=100, accuracy=0.95)
```

This parameter orchestration design provides a powerful yet simple foundation for intelligent parameter matching while maintaining backward compatibility and following the KISS principle. 