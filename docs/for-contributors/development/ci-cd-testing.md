# CI/CD Testing Strategy

## Overview

OpenDXA uses a parallelized testing strategy in GitHub Actions to optimize CI/CD performance. Tests are organized into logical subsystem groups that run independently, significantly reducing total CI time.

## Workflow Files

### `pytest-parallel.yml` (Recommended for Pull Requests)
- **Trigger**: Pull requests
- **Strategy**: Parallel execution across 6 jobs
- **Runtime**: ~3-5 minutes (vs ~15-20 minutes sequential)
- **Purpose**: Fast feedback for code changes

### `pytest.yml` (Sequential Testing)
- **Trigger**: Push to main branch
- **Strategy**: Sequential execution
- **Runtime**: ~15-20 minutes
- **Purpose**: Comprehensive testing after merge

## Test Groups

### 1. Dana Language Core (`test-dana-core`)
**Components**: Parser, AST, interpreter, sandbox, IPV
**Test Paths**: 
- `tests/dana/sandbox/`
- `tests/dana/ipv/`
- Critical struct tests (run comprehensively)

**Rationale**: Core language functionality that affects all other components.

### 2. Dana Integration (`test-dana-integration`)
**Components**: REPL, transcoder, module system, .na files, UX
**Test Paths**:
- `tests/dana/repl/`
- `tests/dana/integration/`
- `tests/dana/module/`
- `tests/dana/na/`
- `tests/dana/ux/`

**Rationale**: User-facing features and integration points.

### 3. Common Utilities (`test-common-utilities`)
**Components**: Graph, I/O, mixins, resources, logging
**Test Paths**:
- `tests/common/`

**Rationale**: Shared infrastructure used across the framework.

### 4. Agent Framework (`test-agent-framework`)
**Components**: Capabilities and resources for agents
**Test Paths**:
- `tests/agent/`

**Rationale**: Multi-agent system functionality.

### 5. Execution Engine (`test-execution-engine`)
**Components**: Pipeline and reasoning systems
**Test Paths**:
- `tests/execution/`

**Rationale**: Core execution and orchestration logic.

### 6. Miscellaneous (`test-miscellaneous`)
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
   - Test files: `test_*.py`
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
      --ignore=tests/new_subsystem/
```

## Performance Monitoring

### Expected Runtimes (GitHub Actions)

| Job | Expected Runtime | Test Count |
|-----|------------------|------------|
| test-dana-core | 4-6 minutes | ~35 tests |
| test-dana-integration | 3-5 minutes | ~25 tests |
| test-common-utilities | 2-4 minutes | ~15 tests |
| test-agent-framework | 1-3 minutes | ~8 tests |
| test-execution-engine | 1-2 minutes | ~5 tests |
| test-miscellaneous | 1-2 minutes | ~3 tests |
| **Total Parallel** | **6-8 minutes** | **~91 tests** |
| **Sequential** | **15-20 minutes** | **~91 tests** |

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
2. **Check for environment variable issues** - `OPENDXA_MOCK_LLM`, etc.
3. **Run the full test suite locally** - `uv run pytest tests/ -v`

### Adding More Parallelization

To further optimize CI times:

1. **Split large test groups** - If dana-core takes too long, split into parser/interpreter/sandbox jobs
2. **Use matrix strategies** - Run different Python versions in parallel
3. **Cache dependencies** - Add caching for uv dependencies
4. **Use faster runners** - Consider GitHub's larger runners for critical paths

## Best Practices

1. **Write fast tests** - Unit tests should complete in milliseconds
2. **Use mocks appropriately** - Mock external services and LLM calls
3. **Group related tests** - Keep tests in logical subsystem directories
4. **Mark slow tests** - Use `@pytest.mark.deep` for comprehensive tests
5. **Test locally first** - Run relevant test groups before pushing
6. **Monitor CI times** - Keep total runtime under 10 minutes for good developer experience 