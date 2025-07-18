# Testing Strategy - Enhanced Function Composition

## Overview

This testing strategy ensures thorough validation of enhanced function composition features across all phases while maintaining backward compatibility. Each phase requires 100% pass rate before proceeding to the next phase.

## Testing Philosophy

### Core Principles
1. **Test-Driven Development**: Tests written before or alongside implementation
2. **Phase Gate Testing**: No phase advancement without complete test validation
3. **Backward Compatibility**: All existing tests must continue passing
4. **Performance Validation**: Benchmarking and regression detection
5. **Real-World Scenarios**: Tests based on actual usage patterns

### Coverage Requirements
- **Phase 1**: 95%+ coverage for new components
- **Phase 2**: 95%+ coverage for enhanced components
- **Phase 3**: 98%+ coverage for production features
- **Overall**: 95%+ coverage for entire function composition system

## Phase 1: Design & Foundation Testing

### 1.1 AST and Parser Testing

#### AST Extensions Test Suite
```python
# File: tests/dana/function_composition/test_ast_extensions.py

class TestParallelBlockAST:
    """Test ParallelBlock AST node functionality"""
    
    def test_parallel_block_creation(self):
        """Test creating ParallelBlock with various function lists"""
        # Valid cases: 2, 3, 5, 10 functions
        functions = [Identifier("f1"), Identifier("f2")]
        block = ParallelBlock(functions)
        assert len(block.functions) == 2
        assert block.functions[0].name == "f1"
    
    def test_parallel_block_validation(self):
        """Test ParallelBlock validation rules"""
        # Empty list should raise error
        with pytest.raises(ValueError):
            ParallelBlock([])
        
        # Single function should warn
        with pytest.warns(UserWarning):
            ParallelBlock([Identifier("single")])
    
    def test_parallel_block_visitor_pattern(self):
        """Test AST visitor integration"""
        # Test visitor pattern works with ParallelBlock
        functions = [Identifier("f1"), Identifier("f2")]
        block = ParallelBlock(functions)
        
        visitor = ASTVisitor()
        result = visitor.visit(block)
        assert result is not None

class TestEnhancedBinaryExpression:
    """Test BinaryExpression with ParallelBlock support"""
    
    def test_binary_with_parallel_block(self):
        """Test BinaryExpression right operand as ParallelBlock"""
        left = Identifier("a")
        right = ParallelBlock([Identifier("b"), Identifier("c")])
        expr = BinaryExpression(left, BinaryOperator.PIPE, right)
        
        assert expr.left == left
        assert expr.operator == BinaryOperator.PIPE
        assert isinstance(expr.right, ParallelBlock)
    
    def test_nested_parallel_expressions(self):
        """Test complex nesting: a | { b, c } | d"""
        # Build: a | { b, c } | d
        parallel_block = ParallelBlock([Identifier("b"), Identifier("c")])
        left_expr = BinaryExpression(Identifier("a"), BinaryOperator.PIPE, parallel_block)
        full_expr = BinaryExpression(left_expr, BinaryOperator.PIPE, Identifier("d"))
        
        assert isinstance(full_expr.left, BinaryExpression)
        assert isinstance(full_expr.left.right, ParallelBlock)
```

#### Parser Testing
```python
# File: tests/dana/function_composition/test_parser_parallel.py

class TestParallelBlockParsing:
    """Test parser handling of parallel block syntax"""
    
    def test_basic_parallel_parsing(self):
        """Test parsing basic parallel blocks"""
        test_cases = [
            "{ f1, f2 }",
            "{ func_a, func_b, func_c }",
            "{a,b,c,d,e}",  # No spaces
            "{ f1 , f2 , f3 }",  # Extra spaces
        ]
        
        parser = DanaParser()
        for case in test_cases:
            result = parser.parse_parallel_block_from_string(case)
            assert isinstance(result, ParallelBlock)
            assert len(result.functions) >= 2
    
    def test_pipe_with_parallel_parsing(self):
        """Test parsing pipe expressions with parallel blocks"""
        test_cases = [
            "a | { b, c }",
            "func1 | { func2, func3 } | func4",
            "data | process | { validate, log, format } | send",
        ]
        
        parser = DanaParser()
        for case in test_cases:
            result = parser.parse_expression_from_string(case)
            assert isinstance(result, BinaryExpression)
            # Verify structure contains ParallelBlock
    
    def test_parallel_parsing_errors(self):
        """Test error handling for invalid parallel syntax"""
        error_cases = [
            "{ }",  # Empty block
            "{ f1 }",  # Single function (warning)
            "{ f1, }",  # Trailing comma
            "{ f1 f2 }",  # Missing comma
            "{ f1, f2",  # Missing closing brace
            "f1, f2 }",  # Missing opening brace
        ]
        
        parser = DanaParser()
        for case in error_cases:
            with pytest.raises((SyntaxError, ParseError)):
                parser.parse_expression_from_string(case)
```

### 1.2 Lexer Testing
```python
# File: tests/dana/function_composition/test_lexer_braces.py

class TestLexerBraceSupport:
    """Test lexer handling of brace tokens"""
    
    def test_brace_tokenization(self):
        """Test basic brace tokenization"""
        lexer = DanaLexer()
        tokens = lexer.tokenize("{ func1, func2 }")
        
        expected_types = [
            TokenType.LBRACE,
            TokenType.IDENTIFIER,
            TokenType.COMMA,
            TokenType.IDENTIFIER,
            TokenType.RBRACE
        ]
        
        assert [t.type for t in tokens] == expected_types
    
    def test_brace_whitespace_handling(self):
        """Test whitespace handling around braces"""
        test_cases = [
            "{a,b}",
            "{ a, b }",
            "{\ta,\tb\t}",
            "{\na,\nb\n}",
        ]
        
        lexer = DanaLexer()
        for case in test_cases:
            tokens = lexer.tokenize(case)
            # Should produce same logical token sequence
            identifiers = [t for t in tokens if t.type == TokenType.IDENTIFIER]
            assert len(identifiers) == 2
```

### 1.3 Integration Testing (Phase 1)
```python
# File: tests/dana/function_composition/test_phase1_integration.py

class TestPhase1Integration:
    """Integration tests for Phase 1 foundations"""
    
    def test_end_to_end_syntax_validation(self):
        """Test complete parsing pipeline for parallel syntax"""
        code = """
        def double(x): return x * 2
        def triple(x): return x * 3
        
        result = 5 | { double, triple }
        """
        
        interpreter = DanaInterpreter()
        context = SandboxContext()
        
        # Should parse without errors
        program = interpreter.parse(code)
        assert program is not None
        
        # Should execute (sequential for Phase 1)
        result = interpreter.execute_program(program, context)
        assert result.success
    
    def test_backward_compatibility(self):
        """Ensure existing pipe operator functionality unchanged"""
        existing_tests = [
            "5 | double | triple",
            "data | process | format",
            "func1 | func2 | func3 | func4",
        ]
        
        interpreter = DanaInterpreter()
        context = SandboxContext()
        
        # Register test functions
        interpreter.function_registry.register("double", lambda ctx, x: x * 2)
        interpreter.function_registry.register("triple", lambda ctx, x: x * 3)
        
        for test_case in existing_tests:
            result = interpreter.evaluate_expression_string(test_case, context)
            # Should work exactly as before
            assert result is not None
```

## Phase 2: Parallel Execution & Parameter Testing

### 2.1 Parallel Execution Testing
```python
# File: tests/dana/function_composition/test_parallel_execution.py

class TestParallelExecution:
    """Test true parallel execution capabilities"""
    
    def test_concurrent_execution(self):
        """Test functions execute concurrently"""
        import time
        
        def slow_double(ctx, x):
            time.sleep(0.1)  # Simulate slow operation
            return x * 2
        
        def slow_triple(ctx, x):
            time.sleep(0.1)
            return x * 3
        
        # Measure execution time
        start = time.time()
        result = self.execute_parallel_code("5 | { slow_double, slow_triple }")
        duration = time.time() - start
        
        # Should be ~0.1s (parallel) not ~0.2s (sequential)
        assert duration < 0.15
        assert result == [10, 15]
    
    def test_thread_safety(self):
        """Test thread safety of parallel execution"""
        def counter_func(ctx, x):
            # Access shared context safely
            count = ctx.get("counter", 0)
            ctx.set("counter", count + 1)
            return x + count
        
        # Multiple parallel executions
        results = []
        for i in range(10):
            result = self.execute_parallel_code(f"{i} | {{ counter_func, counter_func }}")
            results.append(result)
        
        # Verify no race conditions or data corruption
        assert all(isinstance(r, list) and len(r) == 2 for r in results)
    
    def test_resource_cleanup(self):
        """Test proper resource cleanup after parallel execution"""
        # Test with various resource types
        resource_tests = [
            "file_operation",
            "network_call", 
            "database_query",
        ]
        
        for test_type in resource_tests:
            with self.monitor_resources():
                result = self.execute_parallel_code(f"data | {{ {test_type}_func1, {test_type}_func2 }}")
                
            # Verify no resource leaks
            assert self.check_no_resource_leaks()
```

### 2.2 Parameter Orchestration Testing
```python
# File: tests/dana/function_composition/test_parameter_orchestration.py

class TestParameterOrchestration:
    """Test intelligent parameter matching and injection"""
    
    def test_tuple_unpacking(self):
        """Test automatic tuple unpacking"""
        def get_coords(): return (10, 20)
        def calc_distance(x, y): return (x**2 + y**2)**0.5
        
        result = self.execute_orchestrated_code("get_coords | calc_distance")
        expected = (10**2 + 20**2)**0.5
        assert abs(result - expected) < 0.001
    
    def test_named_parameter_matching(self):
        """Test parameter matching by name"""
        def get_user_data(): return {"name": "Alice", "age": 30, "city": "NYC"}
        def format_user(name, age): return f"{name} is {age} years old"
        
        result = self.execute_orchestrated_code("get_user_data | format_user")
        assert result == "Alice is 30 years old"
    
    def test_context_injection(self):
        """Test parameter injection from context"""
        context_setup = """
        private:api_key = "secret123"
        public:base_url = "https://api.example.com"
        """
        
        def make_request(endpoint, api_key, base_url):
            return f"GET {base_url}/{endpoint} with {api_key}"
        
        result = self.execute_orchestrated_code(
            context_setup + "get_endpoint | make_request"
        )
        assert "secret123" in result
        assert "https://api.example.com" in result
    
    def test_complex_parameter_scenarios(self):
        """Test complex parameter orchestration scenarios"""
        scenarios = [
            # Mixed tuple and named parameters
            {
                "code": "get_mixed_data | process_mixed",
                "expected_params": ["tuple_unpacked", "named_matched", "context_injected"]
            },
            # Type-guided parameter assignment
            {
                "code": "get_typed_data | process_typed",
                "expected_behavior": "type_based_matching"
            },
            # Nested structure handling
            {
                "code": "get_nested_struct | process_nested",
                "expected_behavior": "property_extraction"
            }
        ]
        
        for scenario in scenarios:
            result = self.execute_orchestrated_code(scenario["code"])
            self.validate_orchestration_scenario(result, scenario)
```

### 2.3 Performance Testing
```python
# File: tests/dana/function_composition/test_performance.py

class TestPerformanceBenchmarks:
    """Performance benchmarks and regression testing"""
    
    def test_parallel_speedup(self):
        """Test parallel execution provides expected speedup"""
        test_cases = [
            {"functions": 2, "expected_speedup": 1.5},
            {"functions": 4, "expected_speedup": 3.0},
            {"functions": 8, "expected_speedup": 6.0},
        ]
        
        for case in test_cases:
            sequential_time = self.measure_sequential_execution(case["functions"])
            parallel_time = self.measure_parallel_execution(case["functions"])
            
            actual_speedup = sequential_time / parallel_time
            assert actual_speedup >= case["expected_speedup"]
    
    def test_memory_usage(self):
        """Test memory usage remains reasonable during parallel execution"""
        baseline_memory = self.measure_memory_usage_baseline()
        
        # Execute large parallel workload
        large_parallel_memory = self.measure_memory_usage_during_execution(
            "data | { f1, f2, f3, f4, f5, f6, f7, f8 }"
        )
        
        # Memory increase should be proportional, not exponential
        memory_ratio = large_parallel_memory / baseline_memory
        assert memory_ratio < 10  # Should not exceed 10x baseline
    
    def test_latency_overhead(self):
        """Test latency overhead for small parallel operations"""
        simple_sequential = self.measure_latency("5 | double")
        simple_parallel = self.measure_latency("5 | { double, triple }")
        
        # Parallel overhead should be minimal for simple operations
        overhead_ratio = simple_parallel / simple_sequential
        assert overhead_ratio < 2.0  # Less than 2x overhead
```

## Phase 3: Advanced Features Testing

### 3.1 Fault Tolerance Testing
```python
# File: tests/dana/function_composition/test_fault_tolerance.py

class TestFaultTolerance:
    """Test fault-tolerant execution and retry logic"""
    
    def test_retry_mechanism(self):
        """Test retry logic for failed functions"""
        class FlakyFunction:
            def __init__(self):
                self.call_count = 0
            
            def __call__(self, ctx, x):
                self.call_count += 1
                if self.call_count < 3:  # Fail first 2 times
                    raise Exception("Temporary failure")
                return x * 2
        
        flaky_func = FlakyFunction()
        result = self.execute_with_retry("5 | flaky_func", max_retries=5)
        
        assert result == 10  # Should eventually succeed
        assert flaky_func.call_count == 3
    
    def test_partial_result_collection(self):
        """Test collecting partial results when some functions fail"""
        def working_func(ctx, x): return x * 2
        def failing_func(ctx, x): raise Exception("Always fails")
        
        result = self.execute_with_partial_collection(
            "5 | { working_func, failing_func }",
            collect_partial=True
        )
        
        # Should get result from working function, error marker for failing
        assert result["working_func"] == 10
        assert "error" in result["failing_func"]
    
    def test_circuit_breaker(self):
        """Test circuit breaker pattern for repeatedly failing functions"""
        failure_count = 0
        
        def intermittent_func(ctx, x):
            nonlocal failure_count
            failure_count += 1
            if failure_count % 3 == 0:  # Fails 2/3 of the time
                return x * 2
            raise Exception("Intermittent failure")
        
        # Circuit should open after repeated failures
        with self.circuit_breaker_config(failure_threshold=5):
            results = []
            for i in range(10):
                try:
                    result = self.execute_with_circuit_breaker(f"{i} | intermittent_func")
                    results.append(result)
                except CircuitBreakerOpenException:
                    break
            
        # Circuit breaker should have activated
        assert len(results) < 10
```

### 3.2 Advanced Type System Testing
```python
# File: tests/dana/function_composition/test_advanced_types.py

class TestAdvancedTypeMatching:
    """Test advanced type system integration"""
    
    def test_struct_property_mapping(self):
        """Test automatic struct property extraction"""
        struct_code = """
        struct UserProfile:
            name: str
            age: int
            email: str
            preferences: dict
        
        def format_user(name: str, age: int): return f"{name} ({age})"
        
        user = UserProfile("Alice", 30, "alice@example.com", {})
        result = user | format_user
        """
        
        result = self.execute_type_guided_code(struct_code)
        assert result == "Alice (30)"
    
    def test_generic_type_handling(self):
        """Test handling of generic types"""
        generic_code = """
        from typing import List, Dict
        
        def process_list(items: List[int]): return sum(items)
        def process_dict(data: Dict[str, int]): return max(data.values())
        
        mixed_data = ([1, 2, 3], {"a": 10, "b": 20})
        result = mixed_data | { process_list, process_dict }
        """
        
        result = self.execute_type_guided_code(generic_code)
        assert result == [6, 20]  # sum([1,2,3]), max([10,20])
    
    def test_type_conversion(self):
        """Test automatic type conversion when safe"""
        conversion_code = """
        def process_string(text: str): return text.upper()
        def process_number(num: float): return num * 2
        
        # Should auto-convert int to float, int to str
        mixed_input = (42, 3.14)
        result = mixed_input | { process_string, process_number }
        """
        
        result = self.execute_type_guided_code(conversion_code)
        assert result[0] == "42"  # int converted to str
        assert result[1] == 6.28  # float processed normally
```

## Test Infrastructure and Utilities

### Test Execution Helpers
```python
# File: tests/dana/function_composition/test_utils.py

class FunctionCompositionTestHelper:
    """Helper utilities for function composition testing"""
    
    def execute_parallel_code(self, code: str) -> Any:
        """Execute Dana code with parallel function composition"""
        interpreter = DanaInterpreter()
        context = SandboxContext()
        
        # Set up test environment
        self.setup_test_functions(interpreter)
        
        result = interpreter.evaluate_expression_string(code, context)
        return result
    
    def setup_test_functions(self, interpreter: DanaInterpreter):
        """Set up common test functions"""
        test_functions = {
            "double": lambda ctx, x: x * 2,
            "triple": lambda ctx, x: x * 3,
            "add_ten": lambda ctx, x: x + 10,
            "stringify": lambda ctx, x: str(x),
            "sum_all": lambda ctx, lst: sum(lst),
        }
        
        for name, func in test_functions.items():
            interpreter.function_registry.register(name, func)
    
    @contextmanager
    def monitor_resources(self):
        """Monitor system resources during test execution"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss
        initial_threads = process.num_threads()
        
        yield
        
        # Verify resource cleanup
        final_memory = process.memory_info().rss
        final_threads = process.num_threads()
        
        # Memory should not grow excessively
        memory_growth = (final_memory - initial_memory) / initial_memory
        assert memory_growth < 0.1  # Less than 10% memory growth
        
        # Thread count should return to baseline
        assert final_threads <= initial_threads + 2  # Allow some threading overhead
```

### Performance Measurement Framework
```python
# File: tests/dana/function_composition/performance_framework.py

class PerformanceMeasurementFramework:
    """Framework for measuring and tracking performance"""
    
    def __init__(self):
        self.baseline_measurements = {}
        self.current_measurements = {}
    
    def measure_execution_time(self, code: str, iterations: int = 100) -> float:
        """Measure average execution time over multiple iterations"""
        import time
        
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            self.execute_code(code)
            end = time.perf_counter()
            times.append(end - start)
        
        return sum(times) / len(times)
    
    def benchmark_parallel_vs_sequential(self, function_count: int) -> dict:
        """Compare parallel vs sequential execution performance"""
        # Generate test code
        functions = [f"test_func_{i}" for i in range(function_count)]
        sequential_code = " | ".join(functions)
        parallel_code = f"test_input | {{ {', '.join(functions)} }}"
        
        # Measure both approaches
        sequential_time = self.measure_execution_time(sequential_code)
        parallel_time = self.measure_execution_time(parallel_code)
        
        return {
            "sequential_time": sequential_time,
            "parallel_time": parallel_time,
            "speedup": sequential_time / parallel_time,
            "efficiency": (sequential_time / parallel_time) / function_count
        }
    
    def detect_performance_regression(self, test_name: str, current_time: float) -> bool:
        """Detect if current performance is significantly worse than baseline"""
        if test_name not in self.baseline_measurements:
            self.baseline_measurements[test_name] = current_time
            return False
        
        baseline = self.baseline_measurements[test_name]
        regression_threshold = 1.2  # 20% slower is considered regression
        
        return current_time > baseline * regression_threshold
```

## Continuous Integration and Automation

### CI Pipeline Requirements
```yaml
# .github/workflows/function_composition_tests.yml
name: Function Composition Tests

on: [push, pull_request]

jobs:
  test-phase1:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run Phase 1 Tests
        run: pytest tests/dana/function_composition/test_phase1_* -v --cov
      
      - name: Check Coverage
        run: coverage report --fail-under=95

  test-phase2:
    needs: test-phase1
    runs-on: ubuntu-latest
    steps:
      - name: Run Phase 2 Tests
        run: pytest tests/dana/function_composition/test_parallel_* -v
      
      - name: Performance Benchmarks
        run: pytest tests/dana/function_composition/test_performance.py

  test-integration:
    needs: [test-phase1, test-phase2]
    runs-on: ubuntu-latest
    steps:
      - name: Full Integration Tests
        run: pytest tests/dana/function_composition/ -v --slow
```

### Test Execution Strategy

#### Daily Testing
- All unit tests for implemented phases
- Basic performance benchmarks
- Backward compatibility validation

#### Weekly Testing
- Comprehensive integration tests
- Advanced performance analysis
- Memory leak detection
- Stress testing with large parallel workloads

#### Release Testing
- Full test suite execution
- Performance regression analysis
- Production scenario validation
- Documentation example verification

## Summary

This comprehensive testing strategy ensures:

1. **Quality Assurance**: Thorough validation at each development phase
2. **Performance Validation**: Continuous performance monitoring and regression detection
3. **Backward Compatibility**: Existing functionality remains unchanged
4. **Real-World Readiness**: Tests based on actual usage scenarios
5. **Automation**: CI/CD integration for continuous validation

The strategy follows the KISS principle by building testing complexity incrementally, matching the implementation phases, while ensuring production-ready quality and reliability. 