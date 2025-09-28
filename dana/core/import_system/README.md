# Dana Importing System

## Motivation

Dana's importing system is currently scattered across multiple modules (`dana/core/runtime/modules/`, `dana/core/lang/interpreter/executor/statement/`, `dana/registry/`) with inconsistent logic, circular import detection issues, and broken lazy loading mechanisms. This fragmentation makes it difficult to:

- Maintain consistent import behavior
- Debug import-related issues
- Extend the system with new features
- Ensure Python compatibility

This module provides a **unified importing system** with clear standards and fundamental patterns that solve the core importing challenges.

## Core Principles

1. **Python Compatibility** - Import behavior should match Python's semantics
2. **Lazy Loading** - Submodules should be loaded on-demand to avoid circular dependencies
3. **Circular Import Tolerance** - Allow legitimate circular imports that Python permits
4. **Unified Logic** - All import operations go through a single, consistent system
5. **Clear Error Messages** - Distinguish between actual errors and false positives

## Design Goals

- **Unified Architecture**: Single, consistent importing system
- **Python Compatibility**: Match Python's import semantics
- **Robust Lazy Loading**: Handle complex package structures efficiently
- **Intelligent Circular Import Detection**: Allow legitimate patterns, prevent problematic ones
- **Cross-Language Support**: Seamless Dana-Python module interoperability
- **Performance**: Efficient module discovery, loading, and caching
- **Maintainability**: Clear, documented, and testable code

## Implementation Strategy

### Phase 1: Core Infrastructure
- Unified import handler
- Module registry with proper lifecycle management
- Lazy loading mechanism

### Phase 2: Pattern Support
- All fundamental import patterns
- Circular import tolerance
- Cross-language compatibility

### Phase 3: Advanced Features
- Module reloading
- Dynamic imports
- Import hooks and plugins

## File Structure

```
dana/core/importing/
├── README.md              # This file (motivation and approach)
├── SPEC.md                # Detailed specifications (what should work)
├── __init__.py            # Public API
├── core/
│   ├── __init__.py
│   ├── resolver.py        # Module resolution logic
│   ├── loader.py          # Module loading and execution
│   ├── registry.py        # Module registry and caching
│   └── lazy_loader.py     # Lazy loading mechanism
├── patterns/
│   ├── __init__.py
│   ├── absolute.py        # Absolute import handling
│   ├── relative.py        # Relative import handling
│   ├── from_import.py     # From-import handling
│   └── star_import.py     # Star import handling
├── compatibility/
│   ├── __init__.py
│   ├── python.py          # Python module compatibility
│   └── dana.py            # Dana module compatibility
└── utils/
    ├── __init__.py
    ├── circular_detection.py  # Circular import detection
    └── error_handling.py       # Import error handling
```

## Success Criteria

The importing system is successful when:

1. **All smoke tests pass** - `tests/importing/test-imports.na` executes without errors
2. **Python compatibility** - Dana imports behave like Python imports
3. **Performance** - No significant performance regression
4. **Maintainability** - Clear, documented, and testable code
5. **Extensibility** - Easy to add new import patterns and features

## Migration Strategy

1. **Incremental replacement** - Replace existing import logic module by module
2. **Backward compatibility** - Maintain existing APIs during transition
3. **Comprehensive testing** - Test all import patterns before deployment
4. **Performance monitoring** - Ensure no performance regressions

This unified approach will solve the current importing issues while providing a solid foundation for future enhancements.
