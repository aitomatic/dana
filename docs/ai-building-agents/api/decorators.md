# Decorators API Reference

## Overview

Dana provides key decorators for marking methods and enforcing contracts. These decorators enable observability, tool calling, and validation.

---

## @tool_use

**Location**: `dana/common/protocols/war.py`

**Purpose**: Marks a method as callable by LLM agents as a tool

**Usage**:
```python
from dana.common.protocols.war import tool_use

class MyResource(BaseResource):
    @tool_use
    @observable
    def my_method(self, param: str) -> DictParams:
        """Method can be called by agents as a tool"""
        return {"result": f"Processed {param}"}
```

**What it does**:
- Registers method for LLM tool calling
- Enables agents to discover and invoke this method
- Works with function calling API

**Required on**: All public resource and workflow methods that agents should call

---

## @observable

**Location**: `dana/common/observable.py`

**Purpose**: Enables monitoring and logging of method execution

**Usage**:
```python
from dana.common.observable import observable

class MyWorkflow(BaseWorkflow):
    @tool_use
    @observable
    def execute(self, **kwargs) -> DictParams:
        """Execution is observable for monitoring"""
        return self._do_execute(**kwargs)
```

**What it does**:
- Logs method entry/exit
- Captures execution time
- Enables debugging and monitoring
- Notifies observers

**Optional name parameter**:
```python
@observable(name="custom_operation_name")
def my_method(self):
    pass
```

**Required on**: All public resource and workflow methods

---

## @validate_input

**Location**: `dana/core/workflow/validation.py`

**Purpose**: Validates method input parameters before execution

**Usage**:
```python
from dana.core.workflow.validation import validate_input

class MyWorkflow(BaseWorkflow):
    @validate_input(
        query={"required": True, "type": str, "min_length": 1},
        max_results={"type": int, "min_value": 1, "max_value": 100, "default": 10},
        mode={"type": str, "enum": ["fast", "accurate"], "default": "fast"},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        # kwargs validated before reaching here
        query = kwargs["query"]  # Guaranteed to exist
        max_results = kwargs["max_results"]  # Has default if not provided
        return {"result": "success"}
```

**Validation Options**:
```python
{
    "required": True,              # Must be present
    "type": str,                   # Type checking (str, int, float, bool, list, dict)
    "min_length": 1,               # String/list minimum length
    "max_length": 1000,            # String/list maximum length
    "min_value": 1,                # Number minimum
    "max_value": 100,              # Number maximum
    "default": 10,                 # Default if missing
    "enum": ["a", "b"],            # Must be one of these values
}
```

**Error Handling**:
- Raises `ValueError` if validation fails
- Returns clear error message indicating which parameter failed

---

## @validate_output

**Location**: `dana/core/workflow/validation.py`

**Purpose**: Validates method return value after execution

**Usage**:
```python
from dana.core.workflow.validation import validate_output

class MyWorkflow(BaseWorkflow):
    @validate_output(
        success={"required": True, "type": bool},
        result={"required": True},
        count={"type": int, "min_value": 0},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        return {
            "success": True,
            "result": "data",
            "count": 5
        }
```

**Benefits**:
- Ensures consistent return format
- Catches implementation bugs early
- Self-documents expected output

---

## Decorator Order

**Critical**: Decorators must be applied in correct order

**Correct Order** (top to bottom):
```python
@validate_input(...)      # Outermost (applied last)
@validate_output(...)     # 
@tool_use                 # 
@observable               # Innermost (applied first)
def method(self, **kwargs):
    pass
```

**Common Patterns**:

**Resource method**:
```python
@tool_use
@observable
def method(self, **kwargs) -> DictParams:
    pass
```

**Workflow _do_execute**:
```python
@validate_input(...)
@validate_output(...)
def _do_execute(self, **kwargs) -> DictParams:
    pass
```

**Workflow execute** (already has decorators in BaseWorkflow):
```python
# Don't add decorators - already in BaseWorkflow
def execute(self, **kwargs) -> DictParams:
    return super().execute(**kwargs)
```

---

## Examples from Codebase

### Resource Method
```python
# From ConversationResource
@tool_use
@observable
def detect_intent(self, message: str, conversation_history: list | None = None, **kwargs) -> DictParams:
    result = asyncio.run(self._detect_intent(message, conversation_history, **kwargs))
    return result
```

### Workflow with Validation
```python
# From SearchWorkflow
@validate_input(
    query={"required": True, "type": str, "min_length": 1},
    max_results={"type": int, "min_value": 1, "max_value": 100, "default": 10},
)
@validate_output(
    success={"required": True, "type": bool},
    query={"required": True, "type": str},
    results={"required": True, "type": list},
)
def _do_execute(self, **kwargs) -> DictParams:
    return _searcher.search_web(query=kwargs["query"], max_results=kwargs["max_results"])
```

---

## Related Documentation

- [Base Classes](./base_classes.md)
- [Validation Reference](./validation.md)
- [Implementation Guides](../implementation/)

