# Dana Type System Enhancement: AgentInstance Type Detection

## Problem Solved

You requested that `type(a)` should return `AgentInstance[Abc]` instead of `StructInstance[Abc]` for agent instances. This enhancement provides more specific and accurate type information for Dana's type system.

## Implementation

### Before
```dana
agent_blueprint Abc:
    name: str = "An Agent"

a = Abc()
type(a)  # StructInstance[Abc]  # ❌ Generic struct type
```

### After
```dana
agent_blueprint Abc:
    name: str = "An Agent"

a = Abc()
type(a)  # AgentInstance[Abc]  # ✅ Specific agent type
```

## Technical Details

### Enhanced Type Detection

Updated `dana/libs/corelib/py_builtins/type_wrapper.py` to detect `AgentInstance` objects by checking for agent-specific methods:

```python
def _extract_safe_info(self):
    """Extract safe type information without exposing internals."""
    # For instances, try to get the underlying type name
    if hasattr(self._obj, "_type") and hasattr(self._obj._type, "name"):
        self._underlying_type_name = self._obj._type.name
    else:
        self._underlying_type_name = None

    # Determine if this is a resource, agent, or struct instance
    if hasattr(self._obj, "start"):  # ResourceInstance has start() method
        self._instance_type = "ResourceInstance"
    elif hasattr(self._obj, "plan") and hasattr(self._obj, "solve") and hasattr(self._obj, "chat"):  # AgentInstance has agent methods
        self._instance_type = "AgentInstance"
    elif hasattr(self._obj, "_type") and hasattr(self._obj._type, "fields"):
        self._instance_type = "StructInstance"
    else:
        self._instance_type = None
```

### Detection Logic

The system now detects `AgentInstance` objects by checking for the presence of agent-specific methods:
- `plan()` - Agent planning method
- `solve()` - Agent problem-solving method  
- `chat()` - Agent chat method

This approach is:
- **Secure**: Only checks for method existence, no introspection
- **Accurate**: Specifically identifies agent instances
- **Maintainable**: Uses stable public API methods

## Complete Type System Behavior

### Constructor Types
```dana
agent_blueprint Abc:
    name: str = "An Agent"

resource R:
    name: str = "A Resource"

type(Abc)  # Constructor[agent_constructor]
type(R)    # Constructor[resource_constructor]
```

### Instance Types
```dana
a = Abc()      # AgentInstance[Abc]
r = R()        # ResourceInstance[R]
agent AA(Abc)  # AgentInstance[AA]
```

## Benefits

### 1. **More Accurate Type Information**
- `AgentInstance[TypeName]` clearly indicates agent instances
- `ResourceInstance[TypeName]` clearly indicates resource instances
- `StructInstance[TypeName]` for regular struct instances

### 2. **Better Developer Experience**
- Clear distinction between different instance types
- More informative debugging information
- Better IDE support and type hints

### 3. **Consistent Type System**
- All instance types follow the same pattern: `TypeName[UnderlyingType]`
- Maintains security boundaries while providing rich information
- No breaking changes to existing code

## Testing

The enhancement is fully tested with:
- Unit tests in `tests/test_na/test_na_basic_syntax.py`
- Demo file `tests/test_na/test_type_system_demo.na`
- Updated documentation in `docs/primers/`

## Summary

This enhancement makes Dana's type system more precise and informative by correctly identifying `AgentInstance` objects and returning `AgentInstance[TypeName]` instead of the generic `StructInstance[TypeName]`. The change is backward-compatible and maintains all security boundaries while providing better type information for developers.
