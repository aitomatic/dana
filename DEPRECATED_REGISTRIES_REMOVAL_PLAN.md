# Deprecated Registries Removal Plan

## Overview
This plan outlines the systematic removal of deprecated registry modules that have been replaced by the unified `dana.registry` system. The goal is to clean up the codebase by removing backward compatibility layers while ensuring no functionality is lost.

## Current State Analysis

### Deprecated Registry Files Identified

1. **`dana/registries/__init__.py`** - Main backward compatibility layer
2. **`dana/core/runtime/modules/registry.py`** - Deprecated module registry
3. **`dana/core/lang/interpreter/functions/function_registry.py`** - Deprecated function registry

### Migration Status
- ✅ `dana.registry` unified system is implemented and working
- ✅ Backward compatibility layers are in place
- ✅ Tests are passing with the new system
- ⏳ Deprecated files need to be removed

## Phase 1: Audit and Verification

### Step 1.1: Find All References to Deprecated Registries
```bash
# Search for imports from deprecated registries
grep -r "from dana\.registries" .
grep -r "from dana\.core\.runtime\.registries" .
grep -r "from dana\.core\.lang\.interpreter\.functions\.function_registry" .

# Search for direct usage
grep -r "dana\.registries\." .
grep -r "dana\.core\.runtime\.registries\." .
```

### Step 1.2: Verify Migration Completeness
- [ ] Check if any code still imports from deprecated registries
- [ ] Verify all functionality has been migrated to `dana.registry`
- [ ] Ensure no tests depend on deprecated registry paths
- [ ] Confirm no external dependencies use deprecated paths

### Step 1.3: Run Full Test Suite
```bash
# Run all tests to ensure current state is stable
python -m pytest tests/ -v
```

## Phase 2: Remove Deprecated Files

### Step 2.1: Remove `dana/registries/` Directory
```bash
# Remove the entire deprecated registries directory
rm -rf dana/registries/
```

**Files to remove:**
- `dana/registries/__init__.py`
- `dana/registries/__pycache__/` (if exists)

### Step 2.2: Remove Deprecated Module Registry
```bash
# Remove deprecated module registry
rm dana/core/runtime/modules/registry.py
```

### Step 2.3: Remove Deprecated Function Registry
```bash
# Remove deprecated function registry
rm dana/core/lang/interpreter/functions/function_registry.py
```

## Phase 3: Update Import References

### Step 3.1: Update Any Remaining Imports
If any files still import from deprecated paths, update them:

**Replace:**
```python
from dana.registries import *
from dana.registries.function_registry import FunctionRegistry
from dana.registries.type_registry import *
from dana.core.runtime.registries.module_registry import ModuleRegistry
from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry
```

**With:**
```python
from dana.registry import *
from dana.registry.function_registry import FunctionRegistry
from dana.registry.type_registry import *
from dana.registry.module_registry import ModuleRegistry
```

### Step 3.2: Update Documentation
- [ ] Update any documentation that references deprecated paths
- [ ] Update README files if they mention old registry imports
- [ ] Update example code to use new imports

## Phase 4: Testing and Validation

### Step 4.1: Run Comprehensive Tests
```bash
# Run all tests to ensure nothing broke
python -m pytest tests/ -v

# Run specific registry-related tests
python -m pytest tests/unit/core/test_registry.py -v
python -m pytest tests/integration/test_agent_struct_integration.py -v
```

### Step 4.2: Test Import Scenarios
Create a test script to verify all import scenarios work:

```python
# test_imports.py
def test_registry_imports():
    """Test that all registry imports work correctly."""
    
    # Test unified registry imports
    from dana.registry import get_global_registry
    from dana.registry.function_registry import FunctionRegistry
    from dana.registry.type_registry import TypeRegistry
    from dana.registry.module_registry import ModuleRegistry
    from dana.registry.struct_function_registry import StructFunctionRegistry
    
    # Test that deprecated imports fail (as expected)
    try:
        from dana.registries import FunctionRegistry
        assert False, "Deprecated import should fail"
    except ImportError:
        pass
    
    print("✅ All registry imports work correctly")
```

### Step 4.3: Test Runtime Functionality
- [ ] Test agent creation and usage
- [ ] Test function registration and calling
- [ ] Test module loading
- [ ] Test struct method registration

## Phase 5: Cleanup and Documentation

### Step 5.1: Remove Deprecation Warnings
- [ ] Remove any deprecation warning code that's no longer needed
- [ ] Clean up any temporary migration code

### Step 5.2: Update Version Information
- [ ] Update any version notes about registry migration
- [ ] Document the completion of registry unification

### Step 5.3: Final Verification
```bash
# Final test run
python -m pytest tests/ -v

# Check for any remaining references
grep -r "dana\.registries" . --exclude-dir=.git
grep -r "dana\.core\.runtime\.registries" . --exclude-dir=.git
```

## Rollback Plan

If issues are discovered during removal:

1. **Immediate Rollback:**
   ```bash
   git checkout HEAD~1  # Revert to previous commit
   ```

2. **Selective Rollback:**
   ```bash
   git checkout HEAD~1 -- dana/registries/
   git checkout HEAD~1 -- dana/core/runtime/modules/registry.py
   git checkout HEAD~1 -- dana/core/lang/interpreter/functions/function_registry.py
   ```

## Success Criteria

The removal is successful when:

- [ ] All deprecated registry files are removed
- [ ] No code imports from deprecated paths
- [ ] All tests pass
- [ ] All functionality works with `dana.registry`
- [ ] No deprecation warnings are shown
- [ ] Documentation is updated

## Notes for AI Assistant

When working on this plan:

1. **Always run tests after each step** to catch issues early
2. **Use git commits** to save progress at each phase
3. **Check for any external dependencies** that might use deprecated paths
4. **Verify that the unified registry system** handles all use cases
5. **Test both import-time and runtime** functionality
6. **Look for any hardcoded paths** in configuration files

## Expected Timeline

- **Phase 1 (Audit):** 30 minutes
- **Phase 2 (Removal):** 15 minutes  
- **Phase 3 (Updates):** 30 minutes
- **Phase 4 (Testing):** 45 minutes
- **Phase 5 (Cleanup):** 15 minutes

**Total estimated time:** 2-3 hours
