# Runtime Architecture - Enhanced Function Composition

## Overview

The enhanced function composition runtime extends Dana's existing pipe operator infrastructure with parallel execution capabilities while maintaining backward compatibility and following KISS principles.

## Current Architecture Foundation

### Existing Components
```
PipeOperationHandler → ComposedFunction → SandboxFunction.execute()
```

- **PipeOperationHandler**: Manages pipe operator execution
- **ComposedFunction**: Represents function composition (a | b)  
- **SandboxFunction**: Base execution model with context

## New Architecture Components

### 1. ParallelComposedFunction (Phase 1)
```python
class ParallelComposedFunction(SandboxFunction):
    """Handles parallel execution of function blocks: { f1, f2, f3 }"""
    
    def __init__(self, functions: List[SandboxFunction], context: SandboxContext):
        self.functions = functions
        self.context = context
        self.execution_mode = "parallel"  # vs "sequential"
    
    def execute(self, context: SandboxContext, *args, **kwargs) -> List[Any]:
        # Phase 1: Simple thread-based parallel execution
        results = []
        with ThreadPoolExecutor(max_workers=len(self.functions)) as executor:
            futures = [
                executor.submit(func.execute, context, *args, **kwargs) 
                for func in self.functions
            ]
            results = [future.result() for future in futures]
        return results
```

### 2. Enhanced PipeOperationHandler
```python
class EnhancedPipeOperationHandler(PipeOperationHandler):
    """Extended pipe handler supporting parallel blocks"""
    
    def execute_pipe(self, left: Any, right: Any, context: SandboxContext) -> Any:
        # Check if right side is parallel block
        if isinstance(right, ParallelBlock):
            return self._execute_parallel_pipe(left, right, context)
        else:
            # Use existing sequential logic
            return super().execute_pipe(left, right, context)
    
    def _execute_parallel_pipe(self, left: Any, right: ParallelBlock, context: SandboxContext) -> Any:
        # Execute left side first
        input_data = self._evaluate_expression(left, context)
        
        # Create ParallelComposedFunction from block
        parallel_func = self._create_parallel_function(right, context)
        
        # Execute parallel block
        return parallel_func.execute(context, input_data)
```

### 3. AST Extensions
```python
@dataclass
class ParallelBlock(ASTNode):
    """AST node for parallel function blocks: { f1, f2, f3 }"""
    functions: List[Expression]
    
@dataclass  
class EnhancedBinaryExpression(BinaryExpression):
    """Extended binary expression supporting parallel blocks"""
    # left: Expression (existing)
    # operator: BinaryOperator.PIPE (existing)
    # right: Expression | ParallelBlock (new)
```

## Execution Flow Architecture

### Sequential vs Parallel Execution

#### Current Sequential Flow
```
Input → Function A → Result A → Function B → Result B → Output
```

#### New Parallel Flow  
```
Input → Function A → Result A → ┌─ Function B1 ─ Result B1 ─┐
                                ├─ Function B2 ─ Result B2 ─┤ → [B1, B2, B3] → Function C → Output
                                └─ Function B3 ─ Result B3 ─┘
```

### Execution Phases

#### Phase 1: Basic Parallel Execution
1. **Parse** parallel block syntax
2. **Create** ParallelComposedFunction 
3. **Execute** functions in thread pool
4. **Collect** results in order
5. **Pass** result list to next function

#### Phase 2: Smart Parameter Orchestration
1. **Analyze** parameter signatures
2. **Match** output to input parameters
3. **Unpack** tuples/structs as needed
4. **Inject** context variables
5. **Execute** with optimized parameters

#### Phase 3: Fault-Tolerant Execution
1. **Monitor** parallel execution health
2. **Retry** failed functions with backoff
3. **Collect** partial results on failure
4. **Apply** POET enforcement policies
5. **Learn** from execution patterns

## Component Interactions

### 1. Parser Integration
```python
# In DanaParser
def parse_pipe_expression(self) -> Expression:
    left = self.parse_primary()
    
    while self.current_token.type == TokenType.PIPE:
        self.advance()  # consume '|'
        
        if self.current_token.type == TokenType.LBRACE:
            # Parse parallel block
            right = self.parse_parallel_block()
        else:
            # Parse regular expression  
            right = self.parse_primary()
            
        left = EnhancedBinaryExpression(left, BinaryOperator.PIPE, right)
    
    return left

def parse_parallel_block(self) -> ParallelBlock:
    self.expect(TokenType.LBRACE)  # consume '{'
    functions = []
    
    while self.current_token.type != TokenType.RBRACE:
        functions.append(self.parse_expression())
        if self.current_token.type == TokenType.COMMA:
            self.advance()
    
    self.expect(TokenType.RBRACE)  # consume '}'
    return ParallelBlock(functions)
```

### 2. Interpreter Integration
```python
class EnhancedDanaInterpreter(DanaInterpreter):
    def execute_expression(self, expr: Expression, context: SandboxContext) -> Any:
        if isinstance(expr, EnhancedBinaryExpression):
            return self._execute_enhanced_binary(expr, context)
        return super().execute_expression(expr, context)
    
    def _execute_enhanced_binary(self, expr: EnhancedBinaryExpression, context: SandboxContext) -> Any:
        if expr.operator == BinaryOperator.PIPE:
            if isinstance(expr.right, ParallelBlock):
                return self.pipe_handler.execute_parallel_pipe(expr.left, expr.right, context)
        return self.pipe_handler.execute_pipe(expr.left, expr.right, context)
```

## Threading and Concurrency Model

### Phase 1: ThreadPoolExecutor (Simple)
```python
def execute_parallel(self, functions: List[SandboxFunction], context: SandboxContext, input_data: Any) -> List[Any]:
    """Simple thread-based parallel execution"""
    with ThreadPoolExecutor(max_workers=min(len(functions), 8)) as executor:
        # Submit all functions for execution
        futures = [
            executor.submit(self._safe_execute, func, context, input_data)
            for func in functions
        ]
        
        # Collect results in order
        results = []
        for future in futures:
            try:
                result = future.result(timeout=30)  # 30 second timeout
                results.append(result)
            except Exception as e:
                # Phase 1: Fail fast
                raise SandboxError(f"Parallel execution failed: {e}")
        
        return results

def _safe_execute(self, func: SandboxFunction, context: SandboxContext, input_data: Any) -> Any:
    """Thread-safe function execution with context isolation"""
    # Create isolated context copy for thread safety
    thread_context = context.create_child_context()
    return func.execute(thread_context, input_data)
```

### Phase 2/3: Advanced Concurrency
- AsyncIO support for I/O bound operations
- Process pools for CPU-intensive functions  
- Adaptive execution strategy based on function characteristics

## Memory and Resource Management

### Context Isolation
```python
class ThreadSafeContext(SandboxContext):
    """Thread-safe context for parallel execution"""
    
    def __init__(self, parent: SandboxContext):
        super().__init__()
        self._parent = parent
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Any:
        with self._lock:
            # Check local first, then parent
            return super().get(key) or self._parent.get(key)
    
    def set(self, key: str, value: Any):
        with self._lock:
            super().set(key, value)
```

### Resource Limits
```python
# Configuration for parallel execution
PARALLEL_CONFIG = {
    "max_workers": 8,           # Maximum parallel threads
    "execution_timeout": 30,    # Per-function timeout (seconds)
    "memory_limit": "1GB",      # Per-thread memory limit
    "max_parallel_depth": 3     # Nested parallel block limit
}
```

## Error Handling Strategy

### Phase 1: Fail-Fast (KISS)
- Any function failure immediately stops parallel execution
- Raise first exception encountered
- Simple error propagation

### Phase 2: Partial Results
- Collect successful results even if some functions fail
- Mark failed functions in result list
- Allow downstream functions to handle partial data

### Phase 3: POET Integration
- **Perceive**: Monitor execution patterns and failure rates
- **Operate**: Execute with intelligent retry strategies
- **Enforce**: Validate results and apply quality gates
- **Train**: Learn optimal execution strategies

## Performance Considerations

### Optimization Targets
1. **Latency**: Minimize overhead for small parallel blocks
2. **Throughput**: Maximize utilization for large parallel operations
3. **Memory**: Efficient context management and result collection
4. **CPU**: Smart work distribution and load balancing

### Benchmarking Requirements
```python
# Performance test cases for each phase
test_cases = [
    {"functions": 2, "data_size": "small", "target_speedup": 1.5},
    {"functions": 4, "data_size": "medium", "target_speedup": 3.0},
    {"functions": 8, "data_size": "large", "target_speedup": 6.0},
]
```

This architecture provides a solid foundation for implementing enhanced function composition while maintaining Dana's existing strengths and following the KISS principle for incremental development. 