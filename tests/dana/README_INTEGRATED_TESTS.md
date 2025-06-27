# Dana Integrated Tests - Real-World Usage Testing

## Overview

This directory contains a comprehensive battery of integrated tests for the Dana language that go beyond simple unit tests to validate real-world usage patterns. These tests exercise complex interactions between language features and reveal integration issues that unit tests might miss.

## 🎯 Goals

- **Real-World Validation**: Test Dana code in realistic business scenarios
- **Integration Testing**: Verify complex interactions between language features  
- **Regression Prevention**: Ensure previously fixed issues stay fixed
- **Performance Monitoring**: Track performance of complex operations
- **Developer Confidence**: Provide comprehensive examples of Dana capabilities

## 📁 Directory Structure

```
tests/dana/
├── integration/                     # Integrated real-world tests
│   ├── language_features/          # Complex language feature interactions
│   │   ├── test_nested_conditionals_with_structs.na ✅
│   │   └── test_dana_files.py       # Universal test runner
│   ├── data_structures/            # Nested structs, complex data modeling
│   │   ├── test_company_employee_management.na ✅
│   │   └── test_dana_files.py       # Universal test runner
│   ├── control_flow/               # Complex conditional logic, loops
│   ├── functions_and_composition/  # Function composition, polymorphism
│   ├── poet_integration/           # POET domain intelligence tests
│   ├── agent_workflows/            # Multi-step agent scenarios
│   └── performance/                # Performance and scalability tests
├── scenarios/                      # Complete real-world scenarios
│   ├── financial_services/        # Complete financial workflows
│   │   ├── test_loan_application_workflow.na ✅ (partial)
│   │   └── test_dana_files.py       # Universal test runner
│   ├── building_management/        # HVAC and building automation
│   ├── manufacturing/              # Process control and monitoring
│   └── multi_agent/               # Agent-to-agent communication
├── regression/                     # Regression test suite
│   ├── known_issues/              # Tests for previously fixed bugs
│   │   ├── test_pipe_operator_context_fix.na ✅
│   │   └── test_dana_files.py       # Universal test runner
│   └── edge_cases/                # Edge cases and corner conditions
└── legacy/                         # Existing tests (reorganized)
    ├── na/                        # Original basic tests
    ├── poet/                      # Original POET tests
    └── sandbox/                   # Original sandbox tests
```

## ✅ Implemented Tests

### Language Features Integration
- **`test_nested_conditionals_with_structs.na`**: Complex access control system with multi-level conditionals, struct field access, and business logic validation. Tests user permission systems with nested if/else statements and struct operations.

### Data Structures Integration  
- **`test_company_employee_management.na`**: Comprehensive HR system simulation with nested structs, organizational hierarchy, payroll calculations, project team analysis, and employee transfers.

### Financial Services Scenarios
- **`test_loan_application_workflow.na`**: Complete loan processing workflow with POET integration, risk assessment, compliance checking, and decision making (partial implementation).

### Regression Tests
- **`test_pipe_operator_context_fix.na`**: Comprehensive regression test for pipe operator context issues [[memory:6048090787961906368]], including basic pipes, higher-order functions, struct operations, error handling, and context preservation.

## 🚀 Running Tests

### Individual Test Files
```bash
# Run specific Dana test file directly
uv run python -m opendxa.dana.exec.dana tests/dana/integration/language_features/test_nested_conditionals_with_structs.na

# Run through pytest (recommended)
uv run pytest tests/dana/integration/language_features/test_dana_files.py -v
```

### Category-Based Testing
```bash
# Run all language feature integration tests
uv run pytest tests/dana/integration/language_features/ -v

# Run all data structure tests
uv run pytest tests/dana/integration/data_structures/ -v

# Run all financial services scenarios
uv run pytest tests/dana/scenarios/financial_services/ -v

# Run all regression tests
uv run pytest tests/dana/regression/ -v
```

### Full Test Suite
```bash
# Run all integrated tests
uv run pytest tests/dana/integration/ tests/dana/scenarios/ tests/dana/regression/ -v

# Run with coverage
uv run pytest tests/dana/integration/ tests/dana/scenarios/ tests/dana/regression/ --cov=opendxa.dana -v
```

## 🔧 Test Development Guidelines

### Test File Naming
- **Integration Tests**: `test_<feature_description>.na`
- **Scenario Tests**: `test_<business_workflow>.na`
- **Regression Tests**: `test_<issue_description>_fix.na`

### Test Structure Template
```dana
# Test: <Test Name>
# ==================
# PURPOSE: <What this test validates>
# SCOPE: <Language features and complexity covered>
# REAL-WORLD: <Business context or use case>

log("🧪 Testing <Feature Name>")

# Define test data structures
struct TestData:
    field1: str
    field2: int

# Define test functions
def test_function(input: TestData) -> bool:
    # Complex business logic
    return true

# Test scenarios
log("\n--- Testing <Scenario Name> ---")

# Test case 1
result1 = test_function(TestData(field1="test", field2=42))
assert result1 == true
log("✅ Test case 1 passed")

log("🎉 <Test Name> completed successfully!")
```

### Universal Test Runners
Each directory contains a `test_dana_files.py` that automatically discovers and runs all `test_*.na` files:

```python
import pytest
from tests.conftest import run_dana_test_file

@pytest.mark.dana
def test_dana_files(dana_test_file):
    """Universal test that runs any Dana (.na) test file."""
    run_dana_test_file(dana_test_file)
```

## 📊 Test Coverage

### Current Implementation Status

| Category | Tests Implemented | Coverage |
|----------|------------------|----------|
| Language Features | 1/5 | 20% |
| Data Structures | 1/5 | 20% |
| Control Flow | 0/5 | 0% |
| Functions & Composition | 0/5 | 0% |
| POET Integration | 0/5 | 0% |
| Agent Workflows | 0/5 | 0% |
| Performance | 0/5 | 0% |
| Financial Services | 1/5 | 20% |
| Building Management | 0/5 | 0% |
| Manufacturing | 0/5 | 0% |
| Multi-Agent | 0/5 | 0% |
| Known Issues | 1/4 | 25% |
| Edge Cases | 0/10 | 0% |

### Target Coverage Goals
- **Language Feature Coverage**: 90% of Dana language features tested in integration scenarios
- **Real-World Scenario Coverage**: 5 complete end-to-end scenarios per domain
- **Regression Coverage**: 100% of known issues have regression tests

## 🔄 Implementation Roadmap

### Phase 1: Foundation ✅ COMPLETED
- [x] Create new directory structure
- [x] Move existing tests to `legacy/` folder  
- [x] Create universal test runners for each category
- [x] Implement 3 core integration tests
- [x] Verify pytest integration works

### Phase 2: Language Features (Next)
- [ ] Implement control flow integration tests
- [ ] Implement function composition tests
- [ ] Implement mixed data type operation tests
- [ ] Implement scope and variable shadowing tests
- [ ] Implement f-string with nested expressions tests

### Phase 3: Advanced Features
- [ ] Implement POET integration tests
- [ ] Implement agent workflow tests
- [ ] Add performance baseline tests
- [ ] Implement higher-order function tests

### Phase 4: Scenarios
- [ ] Complete financial services scenarios
- [ ] Implement building management scenarios
- [ ] Implement manufacturing scenarios
- [ ] Implement multi-agent scenarios

### Phase 5: Regression Suite
- [ ] Implement parser caching regression tests [[memory:5958236072487089018]]
- [ ] Implement sandbox cleanup regression tests [[memory:8625090651729048317]]
- [ ] Implement edge case tests
- [ ] Create automated regression test runner

## 🐛 Known Issues and Limitations

### Current Limitations
1. **Dict Method Access**: Dana dicts don't support `.append()` method - use separate list variables
2. **POET Integration**: Some POET decorators may not work in test environment
3. **Complex Assertions**: Some assertion patterns need simplification for Dana parser

### Workarounds
```dana
# ❌ Don't do this (dict append)
analysis = {"recommendations": []}
analysis["recommendations"].append("item")

# ✅ Do this instead
recommendations = []
recommendations.append("item")
analysis = {"recommendations": recommendations}
```

## 🔍 Test Quality Metrics

### Success Criteria
- **Test Reliability**: 99% pass rate on clean builds
- **Performance Stability**: <10% variance in test execution time
- **Bug Detection**: Catch integration issues before they reach production

### Monitoring
- Track test execution time trends
- Monitor memory usage during complex tests
- Alert on performance regressions
- Maintain baseline performance metrics

## 🤝 Contributing

### Adding New Tests
1. Choose appropriate category (integration/scenarios/regression)
2. Follow naming conventions and test structure template
3. Include comprehensive assertions and error cases
4. Add documentation comments explaining business context
5. Test both success and failure scenarios

### Updating Existing Tests
1. Maintain backward compatibility
2. Update documentation if behavior changes
3. Verify all assertions still pass
4. Consider adding additional edge cases

## 📚 References

- **[Dana Language Reference](../../docs/.ai-only/dana.md)**: Complete Dana syntax and features
- **[POET Documentation](../../docs/dana/poet/)**: POET domain intelligence framework
- **[Original Test Plan](../tmp/dana_integrated_tests_plan.md)**: Detailed implementation plan
- **[Legacy Tests](legacy/)**: Original unit tests and examples

---

**Status**: Phase 1 Complete ✅ | **Next**: Phase 2 Language Features | **Branch**: `dana/integrated-tests` 