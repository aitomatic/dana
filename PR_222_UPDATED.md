# Add support for `not in` operator in Dana

## Summary

This PR implements the `not in` membership operator for the Dana language, completing Python-style membership testing support. The `in` operator was already supported, but users had to use the awkward `not (x in y)` workaround for negated membership tests.

## What's New

✅ **Native `not in` operator support**
```dana
# Before (still works):
if not (user in authorized_users):
    deny_access()

# Now (Pythonic):
if user not in authorized_users:
    deny_access()
```

## Changes Made

### 1. **AST Definition** (`dana/core/lang/ast/__init__.py`)
- Added `NOT_IN = "not in"` to `BinaryOperator` enum

### 2. **Grammar Fix** (`dana/core/lang/parser/dana_grammar.lark`)
- Changed `NOT_IN_OP: "not" "in"` to `NOT_IN_OP.3: /\bnot\s+in\b/`
- Priority 3 ensures "not in" is recognized as one token before "not" (priority 2) can split it

### 3. **Parser Updates** (3 files)
- `operator_transformer.py`: Returns `BinaryOperator.NOT_IN` instead of string
- `expression_helpers.py`: Added "not in" to operator mapping
- `expression_transformer.py`: Added "not in" to binary operator map

### 4. **Executor** (`binary_operation_handler.py`)
```python
elif node.operator == BinaryOperator.NOT_IN:
    return left not in right
```

### 5. **Type Checker** (`type_checker.py`)
- Added `BinaryOperator.NOT_IN` to comparison operators returning `bool`

## Testing

✅ **All tests pass**: 1654 tests passing (no regressions)

✅ **Comprehensive validation**:
- Lists, strings, dicts, tuples, sets
- Empty collections
- Complex expressions
- Equivalence with `not (x in y)`

## Examples

```dana
# Collection membership
if item not in shopping_cart:
    add_to_cart(item)

# String validation  
if "@" not in email or "." not in email:
    raise ValueError("Invalid email format")

# Access control
allowed_roles = ["admin", "moderator", "user"]
if user.role not in allowed_roles:
    raise PermissionError(f"Invalid role: {user.role}")

# Data validation
required_fields = ["name", "email", "phone"]
missing = [field for field in required_fields if field not in data]
if missing:
    raise ValueError(f"Missing fields: {missing}")
```

## Why This Matters

1. **Pythonic**: Dana aims to be Python-inspired, and `not in` is idiomatic Python
2. **Readable**: `x not in y` reads naturally in English
3. **Consistent**: Pairs with `in` like `is not` pairs with `is`
4. **Expected**: Python developers expect this to work

## No Breaking Changes

The previous workaround `not (x in y)` continues to work exactly as before.

## Files Changed

- `dana/core/lang/ast/__init__.py` - Added enum value
- `dana/core/lang/parser/dana_grammar.lark` - Fixed grammar tokenization
- `dana/core/lang/parser/transformer/expression/operator_transformer.py` - Return enum not string
- `dana/core/lang/parser/transformer/expression/expression_helpers.py` - Added to operator map
- `dana/core/lang/parser/transformer/expression_transformer.py` - Added to operator map
- `dana/core/lang/interpreter/executor/expression/binary_operation_handler.py` - Execute logic
- `dana/core/lang/parser/utils/type_checker.py` - Type checking support
- `tests/regression/operator_limitations/test_expected_operator_failures.na` - Updated docs