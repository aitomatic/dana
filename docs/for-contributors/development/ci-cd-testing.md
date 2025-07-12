# CI/CD Testing Strategy

## Overview

OpenDXA uses a parallelized testing strategy in GitHub Actions to optimize CI/CD performance. Tests are organized into logical subsystem groups that run independently, significantly reducing total CI time.

## Workflow Files

### `pytest-parallel.yml` (Recommended for Pull Requests)
- **Trigger**: Pull requests and pushes to main branches
- **Strategy**: Parallel execution across 20 jobs
- **Runtime**: ~3-5 minutes (vs ~15-20 minutes sequential)
- **Purpose**: Fast feedback for code changes

### `pytest.yml` (Sequential Testing)
- **Trigger**: Weekly schedule and manual trigger
- **Strategy**: Sequential execution
- **Runtime**: ~15-20 minutes
- **Purpose**: Comprehensive testing after merge

## Test Groups

### 1. Dana Language Core (6 jobs)
**Components**: Parser, AST, interpreter, sandbox, structs, functions, imports, execution
**Test Paths**: 
- `tests/dana/sandbox/parser/` - Language parsing and AST generation
- `tests/dana/sandbox/interpreter/test_struct_*` - Critical struct implementation tests
- `tests/dana/sandbox/interpreter/functions/` - Built-in functions and function handling
- `tests/dana/sandbox/interpreter/test_*import*` - Module system and import handling
- `tests/dana/sandbox/interpreter/` - Core execution and runtime features
- `tests/dana/sandbox/` - Sandbox utilities and context management

**Rationale**: Core language functionality that affects all other components.

### 2. Dana Integration & Components (3 jobs)
**Components**: REPL, transcoder, module system, .na files, UX, integration scenarios
**Test Paths**:
- `tests/dana/repl/`, `tests/dana/translator/`, `tests/dana/module/`, `tests/dana/na/`, `tests/dana/ux/` - User-facing features
- `tests/dana/integration/`, `tests/dana/scenarios/` - Integration and scenario tests
- `tests/dana/expected_failures/` - Language limitation documentation tests

**Rationale**: User-facing features and integration points.

### 3. Functional Tests (3 jobs)
**Components**: Dana language tests (.na files), cross-feature integration, standard library
**Test Paths**:
- `tests/functional/language/` - Core language features (syntax, semantics, control flow)
- `tests/functional/integration/` - Cross-feature integration scenarios
- `tests/functional/stdlib/` - Standard library features (POET, built-in functions)

**Rationale**: Direct testing of Dana language features and behavior.

### 4. Integration & Regression Tests (2 jobs)
**Components**: End-to-end system integration, known issues and expected failures
**Test Paths**:
- `tests/integration/end_to_end/` - Full system integration tests
- `tests/regression/` - Known issues, expected failures, and regression prevention

**Rationale**: System-wide functionality and regression prevention.

### 5. Common Utilities (2 jobs)
**Components**: Graph, I/O, mixins, resources, logging, configuration
**Test Paths**:
- `tests/common/resource/` - LLM resources, AISuite integration (heavy tests)
- `tests/common/` - Graph, I/O, mixins, config, utils, state (light tests)

**Rationale**: Shared infrastructure used across the framework.

### 6. Framework Components (3 jobs)
**Components**: Agent framework, POET framework, execution engine
**Test Paths**:
- `tests/agent/` - Agent capabilities and resources
- `tests/dana/poet/` - Domain-driven function enhancement
- `tests/execution/` - Pipeline and reasoning systems

**Rationale**: Multi-agent system functionality and execution logic.

### 7. Miscellaneous (1 job)
**Components**: Catch-all for unmatched tests
**Test Paths**: Any tests not covered by the above groups
**Rationale**: Ensures new test directories are automatically included.

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.live` - Tests requiring real LLM calls (excluded in CI)
- `@pytest.mark.deep` - Comprehensive/slow tests (excluded in fast CI)
- `@pytest.mark.unit` - Fast unit tests (included in CI)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.poet` - POET framework tests

## Local Development

### Running All Tests
```bash
# Fast tests only (matches CI)
uv run pytest -m "not live and not deep" tests/ -v

# All tests including comprehensive
uv run pytest -m "not live" tests/ -v

# Specific subsystem
uv run pytest tests/dana/sandbox/ -v
```

### Running Parallel Tests Locally

#### Using the Parallel Test Script (Recommended)
```bash
# Run tests using the same groupings as CI
python scripts/test-parallel.py

# Make sure the script is executable
chmod +x scripts/test-parallel.py
./scripts/test-parallel.py
```

#### Using pytest-xdist
```bash
# Install pytest-xdist for parallel execution
uv add --dev pytest-xdist

# Run tests in parallel
uv run pytest -n auto tests/ -m "not live and not deep" -v
```

## Adding New Tests

### Test Organization Guidelines

1. **Place tests in logical subsystem directories**:
   - Dana language features → `tests/dana/`
   - Functional tests → `tests/functional/`
   - Integration tests → `tests/integration/`
   - Regression tests → `tests/regression/`
   - Common utilities → `tests/common/`
   - Agent functionality → `tests/agent/`
   - Execution logic → `tests/execution/`

2. **Use appropriate markers**:
   ```python
   import pytest
   
   @pytest.mark.unit
   def test_fast_function():
       pass
   
   @pytest.mark.deep
   def test_comprehensive_feature():
       pass
   
   @pytest.mark.live
   def test_with_real_llm():
       pass
   ```

3. **Follow naming conventions**:
   - Test files: `test_*.py` or `test_*.na`
   - Test functions: `test_*`
   - Test classes: `Test*`

### New Subsystem Tests

If you create a new top-level test directory (e.g., `tests/new_subsystem/`):

1. **Add it to `pytest-parallel.yml`** as a new job
2. **Update the catch-all job** to ignore the new directory
3. **Update this documentation**

Example:
```yaml
# New job
test-new-subsystem:
  # ... standard job configuration ...
  run: uv run pytest tests/new_subsystem/ -m "not live and not deep" --tb=short -v

# Update catch-all job
test-miscellaneous:
  run: |
    uv run pytest tests/ -m "not live and not deep" --tb=short -v \
      --ignore=tests/dana/ \
      --ignore=tests/common/ \
      --ignore=tests/agent/ \
      --ignore=tests/execution/ \
      --ignore=tests/functional/ \
      --ignore=tests/integration/ \
      --ignore=tests/regression/ \
      --ignore=tests/new_subsystem/
```

## Performance Monitoring

### Expected Runtimes (GitHub Actions)

| Job Category | Expected Runtime | Test Count | Description |
|--------------|------------------|------------|-------------|
| Dana Language Core | 4-6 minutes | ~150 tests | Parser, structs, functions, imports, execution |
| Dana Integration | 3-5 minutes | ~80 tests | REPL, translator, modules, integration scenarios |
| Functional Tests | 2-4 minutes | ~60 tests | Language features, integration, standard library |
| Integration & Regression | 2-3 minutes | ~40 tests | End-to-end, regression tests |
| Common Utilities | 2-4 minutes | ~50 tests | Resources, core utilities |
| Framework Components | 1-3 minutes | ~30 tests | Agent, POET, execution engine |
| Miscellaneous | 1-2 minutes | ~10 tests | Catch-all for unmatched tests |
| **Total Parallel** | **6-8 minutes** | **~420 tests** | All tests running in parallel |
| **Sequential** | **15-20 minutes** | **~420 tests** | All tests running sequentially |

### Optimization Tips

1. **Keep test groups balanced** - Aim for similar runtimes
2. **Use appropriate markers** - Exclude slow tests from fast CI
3. **Monitor job runtimes** - Rebalance groups if needed
4. **Add new comprehensive tests to deep marker** - Keep CI fast

## Troubleshooting

### Job Failures

If a specific job fails:

1. **Check the job logs** in GitHub Actions
2. **Run the failing job locally**:
   ```bash
   # Example for dana-core failures
   uv run pytest tests/dana/sandbox/ tests/dana/ipv/ -m "not live and not deep" -v
   ```
3. **Fix the specific tests** in that subsystem
4. **Re-run the workflow**

### All Jobs Failing

If all jobs fail with similar errors:

1. **Check for dependency issues** - `uv sync --extra dev`
2. **Check for environment issues** - Verify Python version and dependencies
3. **Check for configuration issues** - Verify test configuration and markers

### Performance Issues

If CI is taking too long:

1. **Review job runtimes** - Identify slow jobs
2. **Rebalance test groups** - Move tests between jobs
3. **Add more markers** - Exclude slow tests from fast CI
4. **Optimize test code** - Reduce test setup/teardown time

## Test Coverage

Test coverage is tracked and reported for:
- Line coverage
- Branch coverage
- Function coverage

Run coverage report:
```bash
python -m pytest --cov=dana tests/
```

## Future Improvements

1. **Dynamic test grouping** - Automatically balance test groups based on runtime
2. **Test dependency analysis** - Optimize parallel execution based on test dependencies
3. **Performance regression detection** - Monitor test runtime trends
4. **Test flakiness detection** - Identify and fix flaky tests 