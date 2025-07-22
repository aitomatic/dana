# CI/CD and Automated Testing

This document describes the continuous integration and deployment (CI/CD) setup for the OpenDXA project, with special focus on workshop integration testing.

## Overview

Our CI/CD pipeline ensures that:
- All workshop examples remain functional as the codebase evolves
- New features are properly documented with working examples
- Breaking changes are caught early through comprehensive testing
- Contributors receive fast feedback on their changes

## GitHub Actions Workflows

### Workshop Integration Tests

**File**: `.github/workflows/workshop-integration-tests.yml`

This is our primary quality gate for workshop examples and user-facing functionality.

#### Triggers
- Pull requests to `main` or `develop` branches
- Changes to workshop examples, Dana core, or test files
- Manual triggering with optional MCP integration testing

#### Jobs

**1. Workshop Tests (Mock Mode)**
- Validates file structure and syntax
- Tests core functionality in mock mode
- Runs examples that don't require external services

**2. Workshop Syntax Validation**  
- Validates all `.na` files can be parsed
- Checks for missing expected files
- Ensures basic file structure integrity

**3. Workshop Tests (MCP Integration)** *(Conditional)*
- Only runs when MCP-related changes detected
- Installs and starts MCP weather server
- Tests full MCP integration functionality
- Automatically manages server lifecycle

**4. Report Results**
- Aggregates results from all test jobs
- Posts success/failure comments to PRs
- Provides debugging guidance for failures

#### Example PR Comment (Failure)
```markdown
## ❌ Workshop Integration Tests Failed

The Dana workshop integration tests failed for this PR. Please check:

- 🔍 **Syntax Validation**: Ensure all `.na` files have valid Dana syntax
- 🧪 **Integration Tests**: Verify workshop examples execute correctly  
- 📝 **File Structure**: Check that expected workshop files exist

### How to run tests locally:
```bash
# Run validation script (simulates CI)
python scripts/validate_workshop_ci.py

# Or run specific test categories
python tests/integration/run_workshop_tests.py --file-validation
```
```

## Local Development Workflow

### Pre-commit Validation

Before creating a PR, run the local validation script:

```bash
# Simulates the same tests that CI will run
python scripts/validate_workshop_ci.py
```

This script:
- Checks environment setup
- Runs file validation tests
- Tests core workshop functionality
- Optionally runs MCP integration tests
- Provides clear pass/fail results

### Test Categories

**File Validation Tests**
```bash
python tests/integration/run_workshop_tests.py --file-validation
```
- Validates Dana file syntax
- Checks for balanced quotes/parentheses
- Reports file structure issues

**Core Functionality Tests**
```bash
python tests/integration/run_workshop_tests.py -k "builtin_reasoning or order_intelligence"
```
- Tests examples that work in mock mode
- Validates basic Dana language features
- Ensures Python interoperability

**MCP Integration Tests**
```bash
python tests/integration/run_workshop_tests.py --with-mcp
```
- Installs MCP weather server
- Tests real external service integration
- Validates agent functionality with live services

## Test Infrastructure

### Workshop Test Runner

**File**: `tests/integration/run_workshop_tests.py`

Centralized test runner with multiple execution modes:

```bash
# Basic usage
python tests/integration/run_workshop_tests.py

# With verbose output
python tests/integration/run_workshop_tests.py -v

# Specific test categories
python tests/integration/run_workshop_tests.py --file-validation
python tests/integration/run_workshop_tests.py --parametrized

# With MCP server
python tests/integration/run_workshop_tests.py --with-mcp

# Specific examples
python tests/integration/run_workshop_tests.py -k "builtin_reasoning"
```

### Local Validation Script

**File**: `scripts/validate_workshop_ci.py`

Interactive validation script that simulates CI workflow:

```bash
python scripts/validate_workshop_ci.py
```

Features:
- Environment validation
- Step-by-step test execution
- Interactive MCP testing option
- Clear pass/fail reporting
- Debugging suggestions

## Adding New Workshop Examples

When adding new workshop examples:

1. **Create the example**: Add `.na` files to appropriate workshop subdirectory

2. **Update test expectations**: 
   ```python
   # In tests/integration/test_workshop_examples.py
   expected_files = [
       # ... existing files ...
       "new_category/new_example.na",
   ]
   ```

3. **Add parametrized test case**:
   ```python
   {
       "name": "new_example",
       "file_path": "new_category/new_example.na", 
       "should_succeed": True,  # or False if requires external deps
       "description": "Description of new example"
   }
   ```

4. **Test locally**:
   ```bash
   python scripts/validate_workshop_ci.py
   ```

5. **Update documentation**: Add example to workshop README

## Continuous Integration Best Practices

### Pull Request Requirements

- All workshop integration tests must pass
- New examples must include corresponding tests
- Breaking changes require workshop updates
- Documentation updates for user-facing changes

### Test Reliability

- **Mock Mode Default**: Tests run in mock mode by default for reliability
- **External Dependencies**: MCP tests only run when relevant
- **Graceful Degradation**: Tests handle missing external services
- **Clear Error Messages**: Failed tests provide actionable debugging info

### Performance Optimization

- **Parallel Execution**: Independent test jobs run in parallel
- **Dependency Caching**: Python packages cached across runs
- **Selective Testing**: MCP tests only run when needed
- **Fast Feedback**: Core tests complete in under 2 minutes

## Monitoring and Alerting

### GitHub Integration

- PR status checks prevent merging failing tests
- Automated comments provide debugging guidance
- Success confirmations build contributor confidence

### Maintenance

- Regular review of test reliability
- Updates for new workshop examples
- Monitoring of external service dependencies
- Performance optimization as test suite grows

## Troubleshooting CI Issues

### Common Problems

**Environment Setup Issues**
- Virtual environment not properly activated
- Missing dependencies or version conflicts  
- Python version incompatibilities

**Workshop Example Failures**  
- Syntax errors in `.na` files
- Missing or renamed workshop files
- External service dependencies unavailable

**MCP Integration Problems**
- Port conflicts (port 8000 in use)
- Network connectivity issues
- MCP server installation failures

### Debug Steps

1. **Run locally first**:
   ```bash
   python scripts/validate_workshop_ci.py
   ```

2. **Check specific failures**:
   ```bash
   python tests/integration/run_workshop_tests.py --file-validation -v
   ```

3. **Test individual examples**:
   ```bash
   dana examples/workshop/path/to/example.na
   ```

4. **Review CI logs**: Check GitHub Actions output for detailed error messages

---

This CI/CD setup ensures that OpenDXA workshop examples remain reliable, functional, and valuable to users as the project evolves. 