# Regression Tests

This directory contains tests for known issues, expected failures, and regression prevention.

## Structure

- **`known_issues/`** - Tests for known bugs and limitations
  - Current bugs that are being tracked
  - Workarounds and temporary fixes
  - Bug reproduction cases

- **`expected_failures/`** - Tests that are expected to fail
  - **`syntax_limitations/`** - Language syntax limitations
  - **`language_limitations/`** - Language feature limitations
  - **`operator_limitations/`** - Operator and expression limitations
  - **`function_limitations/`** - Function and method limitations
  - **`data_structure_limitations/`** - Data structure limitations

## Purpose

### Regression Prevention
- Ensure that fixed bugs don't reappear
- Track known issues and their status
- Provide test cases for bug fixes

### Known Limitations
- Document current language limitations
- Provide test cases for expected failures
- Track planned improvements

### Bug Tracking
- Reproduce reported bugs
- Verify bug fixes
- Track bug status and resolution

## Running Regression Tests

```bash
# All regression tests
python -m pytest tests/regression/

# Expected failures only
python -m pytest tests/regression/expected_failures/

# Known issues only
python -m pytest tests/regression/known_issues/

# Specific limitation category
python -m pytest tests/regression/expected_failures/syntax_limitations/
```

## Test Guidelines

### Expected Failures
1. **Clear Documentation**: Explain why the test is expected to fail
2. **Specific Error**: Test for specific error types or messages
3. **Future Planning**: Include comments about planned fixes
4. **Workarounds**: Document any available workarounds

### Known Issues
1. **Bug Description**: Clear description of the issue
2. **Reproduction Steps**: Steps to reproduce the bug
3. **Expected Behavior**: What the correct behavior should be
4. **Status Tracking**: Current status and planned fixes

## Example Test Structure

### Expected Failure Test
```python
import pytest

def test_syntax_limitation():
    """
    Test that a specific syntax limitation is enforced.
    This test is expected to fail until the limitation is removed.
    """
    with pytest.raises(SyntaxError):
        # This syntax is not yet supported
        exec("x = 1 | 2")  # Bitwise OR not supported in Dana
```

### Known Issue Test
```python
def test_known_bug_reproduction():
    """
    Test reproduction of a known bug.
    This test should pass once the bug is fixed.
    """
    # Current bug: function composition with certain types fails
    result = some_function_composition()
    assert result == expected_value  # Currently fails
```

## Status Tracking

### Test Status Markers
- `@pytest.mark.xfail` - Expected to fail
- `@pytest.mark.skip` - Temporarily skipped
- `@pytest.mark.bug` - Known bug
- `@pytest.mark.limitation` - Language limitation

### Issue Status
- **Open**: Bug is confirmed and being tracked
- **In Progress**: Bug is being worked on
- **Fixed**: Bug has been fixed, test should pass
- **Won't Fix**: Issue is a known limitation that won't be addressed

## Continuous Integration

Regression tests are run:
- On all pull requests
- On main branch commits
- Before releases
- As part of the full test suite

## Maintenance

### Adding New Tests
1. Create test file in appropriate subdirectory
2. Use clear, descriptive names
3. Include comprehensive documentation
4. Mark with appropriate pytest markers

### Updating Tests
1. Update status when bugs are fixed
2. Remove tests for resolved issues
3. Update documentation for changes
4. Verify test behavior after fixes

### Cleanup
1. Remove tests for permanently resolved issues
2. Update documentation for status changes
3. Archive tests for historical reference
4. Maintain test organization and clarity 