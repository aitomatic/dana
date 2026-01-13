# Universal Dana (.na) Test Integration

This document explains how to integrate Dana (`.na`) test files into pytest across any test directory.

## 🚀 **Quick Start**

To run Dana test files in **any** directory with pytest:

1. **Create your Dana test files** with the `test_*.na` naming pattern
2. **Copy the universal test runner** to your directory:
   ```bash
   cp tests/dana/test_dana_files.py your_test_directory/
   ```
3. **Run with pytest**:
   ```bash
   pytest your_test_directory/test_dana_files.py -v
   ```

That's it! All `test_*.na` files in that directory will automatically be discovered and run.

## 📁 **File Structure Example**

```
tests/dana/poet/
├── test_poet_simple.na          # ✅ Will be discovered and run
├── test_poet_basic.na           # ✅ Will be discovered and run  
├── test_poet_advanced.na        # ✅ Will be discovered and run
├── test_dana_files.py           # 🔧 Universal test runner
└── other_python_tests.py       # ⚙️ Regular Python tests

tests/dana/na/
├── test_simple.na               # ✅ Will be discovered and run
├── test_functions.na            # ✅ Will be discovered and run
├── test_dana_files.py           # 🔧 Universal test runner
└── my_module_test.na            # ❌ Won't be discovered (wrong naming)
```

## 🔧 **How It Works**

### **Universal Test Runner** (`test_dana_files.py`)

```python
import pytest
from tests.conftest import run_dana_test_file

@pytest.mark.dana
def test_dana_files(dana_test_file):
    """Universal test that runs any Dana (.na) test file."""
    run_dana_test_file(dana_test_file)
```

### **Auto-Discovery** (in `tests/conftest.py`)

The universal system automatically:
1. **Discovers** all `test_*.na` files in the same directory
2. **Parametrizes** the test to run once per `.na` file
3. **Reports** each `.na` file as a separate pytest test case
4. **Isolates** each test with its own DanaSandbox

### **Benefits**

- ✅ **Authentic Testing**: Tests run pure Dana code, not Python simulations
- ✅ **Zero Boilerplate**: Copy one file, get full pytest integration
- ✅ **Auto-Discovery**: Add `.na` files, automatically get pytest tests
- ✅ **Parallel Execution**: pytest can run Dana tests in parallel
- ✅ **IDE Integration**: Works with pytest plugins and IDEs
- ✅ **Clear Reporting**: Each `.na` file shows as separate test result

## 📝 **Dana Test File Guidelines**

### **Naming Convention**
- ✅ `test_*.na` - Will be discovered
- ❌ `example.na` - Won't be discovered  
- ❌ `*_test.na` - Won't be discovered

### **Test Structure**
Dana test files should be self-contained and use `assert` statements:

```dana
# test_my_feature.na
log("🧪 Testing My Feature")

# Test 1: Basic functionality
result = my_function(5)
assert result == 10
log("✅ Basic test passed")

# Test 2: Error handling  
try:
    my_function(-1)
    assert false, "Should have thrown error"
except:
    log("✅ Error handling works")

log("🎉 All tests passed!")
```

## 🏃 **Running Tests**

### **Single Directory**
```bash
# Run all .na tests in poet directory
pytest tests/dana/poet/test_dana_files.py -v

# Run all .na tests in na directory  
pytest tests/dana/na/test_dana_files.py -v
```

### **All Dana Tests**
```bash
# Run all Dana tests across all directories
pytest tests/dana/ -k "test_dana_files" -v

# Run all tests (Python + Dana)
pytest tests/dana/ -v
```

### **Specific Test File**
```bash
# Run specific .na file through pytest
pytest tests/dana/poet/test_dana_files.py::test_dana_files[test_poet_simple] -v
```

## 🔍 **Example Output**

```
tests/dana/poet/test_dana_files.py::test_dana_files[test_poet_simple] PASSED
tests/dana/poet/test_dana_files.py::test_dana_files[test_poet_basic] PASSED  
tests/dana/poet/test_dana_files.py::test_dana_files[test_poet_advanced] FAILED

tests/dana/na/test_dana_files.py::test_dana_files[test_simple] PASSED
tests/dana/na/test_dana_files.py::test_dana_files[test_functions] PASSED
tests/dana/na/test_dana_files.py::test_dana_files[test_control_flow] PASSED
```

## 🚨 **Troubleshooting**

### **Test Not Discovered**
- Check file naming: Must be `test_*.na`
- Ensure `test_dana_files.py` is in the same directory
- Verify the `.na` file has valid Dana syntax

### **Import Errors**
- Ensure you're running from the project root
- Check that `tests/conftest.py` has the universal test functions

### **Syntax Errors**
- Dana test files must use valid Dana syntax
- Use `log()` instead of `print()` for output
- Check Dana language documentation for correct syntax

## 📚 **More Information**

- **Dana Language Reference**: See `docs/.ai-only/dana.md`
- **POET Testing**: See Dana files in `tests/dana/poet/`
- **Core Dana Tests**: See Dana files in `tests/dana/na/` 