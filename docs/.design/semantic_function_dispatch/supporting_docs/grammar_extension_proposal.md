# Dana Grammar Extension: Generic Type Support

## 📋 **Overview**

This document proposes extending the Dana language grammar to support generic type syntax (e.g., `list[Type]`, `dict[K,V]`) which is essential for the semantic function dispatch feature, particularly struct type coercion.

## 🚨 **Current Limitation**

**Problem**: Dana grammar currently fails to parse generic type syntax:

```dana
# ❌ Current grammar FAILS:
employees: list[Person] = reason("Create team")
tasks: list[Task] = reason("Plan project") 
config: dict[str, int] = reason("Generate config")

# ✅ Current workaround:
employees: list = reason("Create team")     # Type info lost
tasks: list = reason("Plan project")       # Type info lost
config: dict = reason("Generate config")   # Type info lost
```

**Impact**: Without generic type support, the semantic function dispatch system cannot:
- Generate accurate JSON schemas for struct validation
- Provide precise context to LLM functions
- Distinguish between `list[Person]` vs `list[Task]` in prompts
- Enable strong typing for collections of custom structs

## 🎯 **Proposed Grammar Extension**

### **Current Grammar** (from `dana_grammar.lark`)
```lark
// Current type system (limited)
basic_type: union_type
union_type: single_type (PIPE single_type)*
single_type: INT_TYPE | FLOAT_TYPE | STR_TYPE | BOOL_TYPE | LIST_TYPE | DICT_TYPE | TUPLE_TYPE | SET_TYPE | NONE_TYPE | ANY_TYPE | NAME
```

### **Proposed Extension**
```lark
// Enhanced type system with generics
basic_type: union_type
union_type: generic_or_simple_type (PIPE generic_or_simple_type)*
generic_or_simple_type: generic_type | simple_type

// New generic type support
generic_type: simple_type "[" type_argument_list "]"
type_argument_list: basic_type ("," basic_type)*

// Existing simple types (unchanged)
simple_type: INT_TYPE | FLOAT_TYPE | STR_TYPE | BOOL_TYPE | LIST_TYPE | DICT_TYPE | TUPLE_TYPE | SET_TYPE | NONE_TYPE | ANY_TYPE | NAME

// Type tokens (unchanged)
INT_TYPE: "int"
FLOAT_TYPE: "float" 
STR_TYPE: "str"
BOOL_TYPE: "bool"
LIST_TYPE: "list"
DICT_TYPE: "dict"
TUPLE_TYPE: "tuple"
SET_TYPE: "set"
NONE_TYPE: "None"
ANY_TYPE: "any"
```

## 📝 **Supported Generic Syntax**

### **Basic Collections**
```dana
# List types
items: list[str] = reason("Generate list of names")
numbers: list[int] = reason("Generate list of numbers") 
flags: list[bool] = reason("Generate list of decisions")

# Dictionary types  
config: dict[str, int] = reason("Generate configuration")
mapping: dict[str, str] = reason("Generate key-value pairs")
lookup: dict[int, bool] = reason("Generate lookup table")

# Set types
unique_names: set[str] = reason("Generate unique names")
unique_ids: set[int] = reason("Generate unique IDs")

# Tuple types
coordinates: tuple[float, float] = reason("Generate coordinates")
rgb: tuple[int, int, int] = reason("Generate RGB color")
```

### **Struct Collections**
```dana
struct Person:
    name: str
    age: int

struct Task:
    title: str
    priority: int

# Collections of custom structs
team: list[Person] = reason("Create development team")
backlog: list[Task] = reason("Create project backlog")
directory: dict[str, Person] = reason("Create employee directory")
```

### **Nested Generics**
```dana
# Nested collections
matrix: list[list[int]] = reason("Generate 2D matrix")
groups: dict[str, list[Person]] = reason("Group employees by department")
hierarchy: dict[str, dict[str, list[Task]]] = reason("Create project hierarchy")
```

### **Union Types with Generics**
```dana
# Union of generic types
mixed_data: list[str] | list[int] = reason("Generate mixed list")
flexible_config: dict[str, str] | dict[str, int] = reason("Generate config")
```

## 🔧 **Implementation Details**

### **AST Node Enhancement**
```python
# Current TypeHint AST node
class TypeHint:
    def __init__(self, name: str):
        self.name = name  # "list", "dict", etc.

# Enhanced TypeHint AST node  
class TypeHint:
    def __init__(self, name: str, type_args: list[TypeHint] = None):
        self.name = name           # "list", "dict", "Person", etc.
        self.type_args = type_args or []  # [TypeHint("str"), TypeHint("int")]
    
    def is_generic(self) -> bool:
        return len(self.type_args) > 0
    
    def to_string(self) -> str:
        if self.is_generic():
            args = ", ".join(arg.to_string() for arg in self.type_args)
            return f"{self.name}[{args}]"
        return self.name
```

### **Parser Transformer Updates**
```python
# In AssignmentTransformer
def generic_type(self, items):
    """Transform generic_type rule into enhanced TypeHint."""
    base_type = items[0]  # simple_type result  
    type_args = items[1]  # type_argument_list result
    
    return TypeHint(
        name=base_type.name,
        type_args=type_args
    )

def type_argument_list(self, items):
    """Transform type_argument_list into list of TypeHint objects."""
    return [item for item in items]  # Each item is already a TypeHint
```

### **Schema Generation Support**
```python
def generate_json_schema(type_hint: TypeHint) -> dict:
    """Generate JSON schema from enhanced TypeHint."""
    if not type_hint.is_generic():
        return {"type": get_json_type(type_hint.name)}
    
    if type_hint.name == "list":
        item_schema = generate_json_schema(type_hint.type_args[0])
        return {
            "type": "array",
            "items": item_schema
        }
    
    elif type_hint.name == "dict":
        key_type = type_hint.type_args[0]
        value_type = type_hint.type_args[1]
        return {
            "type": "object",
            "additionalProperties": generate_json_schema(value_type)
        }
    
    elif type_hint.name in struct_registry:
        # Custom struct type
        return generate_struct_schema(type_hint.name)
```

## 🧪 **Test Cases**

### **Grammar Parsing Tests**
```python
def test_generic_type_parsing():
    """Test that enhanced grammar correctly parses generic types."""
    test_cases = [
        "list[str]",
        "dict[str, int]", 
        "list[Person]",
        "dict[str, list[Task]]",
        "tuple[float, float, float]",
        "list[str] | list[int]"
    ]
    
    for case in test_cases:
        result = parse_type_hint(case)
        assert result is not None
        assert result.is_generic() or "|" in case
```

### **Schema Generation Tests**
```python
def test_schema_generation():
    """Test JSON schema generation from generic types."""
    # list[str] → {"type": "array", "items": {"type": "string"}}
    list_str = TypeHint("list", [TypeHint("str")])
    schema = generate_json_schema(list_str)
    assert schema == {"type": "array", "items": {"type": "string"}}
    
    # dict[str, int] → {"type": "object", "additionalProperties": {"type": "integer"}}
    dict_str_int = TypeHint("dict", [TypeHint("str"), TypeHint("int")])
    schema = generate_json_schema(dict_str_int)
    assert schema["type"] == "object"
    assert schema["additionalProperties"]["type"] == "integer"
```

## ⚡ **Performance Considerations**

### **Parsing Overhead**
- **Generic type parsing**: ~1-2ms additional per complex type
- **AST node creation**: Minimal overhead with enhanced TypeHint
- **Memory usage**: Slight increase for type_args storage

### **Optimization Strategies**
- **Type caching**: Cache parsed TypeHint objects for reuse
- **Lazy evaluation**: Only parse generics when needed for context
- **Schema caching**: Cache generated JSON schemas

## 🔄 **Migration Strategy**

### **Backwards Compatibility**
```dana
# Existing code continues to work
items: list = reason("Generate items")      # ✅ Still valid
config: dict = reason("Generate config")   # ✅ Still valid

# New syntax is additive
items: list[str] = reason("Generate items")      # ✅ Enhanced
config: dict[str, int] = reason("Generate config")  # ✅ Enhanced
```

### **Gradual Adoption**
1. **Phase 1**: Enable grammar extension (no breaking changes)
2. **Phase 2**: Encourage generic syntax in new code
3. **Phase 3**: Add linter warnings for non-generic collections
4. **Phase 4**: Optional strict mode requiring generic types

## ✅ **Implementation Checklist**

### **Grammar Extension**
- [ ] Update `dana_grammar.lark` with generic type rules
- [ ] Test grammar parsing with complex nested generics
- [ ] Ensure backwards compatibility with existing syntax

### **AST Enhancement**  
- [ ] Enhance `TypeHint` class with `type_args` support
- [ ] Update parser transformers for generic types
- [ ] Add utility methods for type introspection

### **Schema Generation**
- [ ] Implement JSON schema generation for generic types
- [ ] Support nested generics and custom structs
- [ ] Add validation for schema correctness

### **Testing**
- [ ] Comprehensive parsing tests for all generic combinations
- [ ] Schema generation validation tests
- [ ] Performance benchmarks for parsing overhead
- [ ] Integration tests with semantic function dispatch

## 🎯 **Success Criteria**

1. **Grammar Compatibility**: All existing Dana code continues to parse correctly
2. **Generic Support**: Complex nested generics parse without errors
3. **Schema Quality**: Generated JSON schemas accurately represent types
4. **Performance**: <5ms parsing overhead for complex generic types
5. **Integration**: Seamless integration with semantic function dispatch

---

**This grammar extension is the critical foundation that enables the full power of semantic function dispatch with struct type coercion.** 🚀 