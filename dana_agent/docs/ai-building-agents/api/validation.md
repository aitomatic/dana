# Validation API Reference

## Overview

Dana provides input/output validation through the `@validate_input` and `@validate_output` decorators.

**Location**: `dana/core/workflow/validation.py`

## Validation Spec

```python
{
    "required": bool,              # Must be present
    "type": type,                  # str, int, float, bool, list, dict
    "min_length": int,             # For str/list
    "max_length": int,             # For str/list
    "min_value": number,           # For int/float
    "max_value": number,           # For int/float
    "default": any,                # Default value
    "enum": list,                  # Must be one of these
}
```

## Examples

See [Decorators Reference](./decorators.md) for complete examples.

**Best examples in codebase**:
- `dana/lib/workflows/web_research.py` - Multiple validated workflows
- `contrib/expert_interview/workflows/expert_interview.py` - Complex validation

