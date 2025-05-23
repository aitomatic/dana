# Dana Language PR

## Description
<!-- What Dana language feature/fix are you implementing? -->

## Type of Change
- [ ] 🐛 Parser bug fix
- [ ] ✨ New language feature
- [ ] 🔧 Interpreter improvement
- [ ] ♻️ AST refactoring
- [ ] 💥 Breaking syntax change

## Dana Components
- [ ] **Parser** - Lark grammar, syntax rules
- [ ] **AST** - Node types, validation, transformations  
- [ ] **Interpreter** - Execution logic, function registry
- [ ] **Sandbox** - Runtime environment, context management
- [ ] **Functions** - Built-in functions, core capabilities

## Language Changes
<!-- Describe the specific Dana syntax/behavior changes -->

### Syntax Example
```python
# Before (if applicable)


# After
```

## Testing
- [ ] Added Dana language tests
- [ ] Parser tests pass: `pytest tests/dana/sandbox/parser/`
- [ ] Interpreter tests pass: `pytest tests/dana/sandbox/interpreter/`
- [ ] Example Dana programs still work
- [ ] Edge cases tested (syntax errors, invalid inputs)

### Test Commands
```bash
# Run Dana-specific tests
pytest tests/dana/
bin/dana examples/
```

## Backward Compatibility
- [ ] ✅ Fully backward compatible
- [ ] ⚠️ Minor breaking changes (migration notes below)
- [ ] 💥 Major breaking changes (requires version bump)

<!-- If breaking changes, explain migration path -->

## Documentation
- [ ] Updated language documentation
- [ ] Added/updated examples
- [ ] Function docstrings updated
- [ ] Grammar rules documented

**Closes #** 