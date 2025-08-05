# Struct Field Comments

Dana supports inline comments on struct fields to provide descriptive information that enhances LLM reasoning and prompt generation.

## Overview

Struct field comments allow developers to add descriptive text to struct field definitions, which are automatically captured and used by Dana's POET system to provide enhanced context to LLMs when generating structured data.

## Syntax

Field comments are added using the standard Dana comment syntax (`#`) on the same line as the field definition:

```dana
struct Person:
    name: str  # the full name of the person
    age: int  # the age in years (must be positive)
    email: str  # the email address for contact
    metadata: dict[str, str]  # additional metadata like occupation, hobbies, etc.
```

## Features

### 1. **Automatic Comment Capture**
Comments are automatically parsed and stored with the struct definition:

```dana
struct Product:
    id: str  # unique product identifier (e.g., "PROD-001")
    name: str  # product name for display
    price: float  # price in dollars (can include cents)
    category: str  # product category like "Electronics", "Clothing", etc.
```

### 2. **Enhanced LLM Prompts**
When `reason()` is called with a struct type context, field comments are included in the enhanced prompt:

```dana
# This automatically includes field descriptions with comments
person: Person = reason("Create a person named John who is 30 years old")
```

The LLM receives an enhanced prompt containing:
```
Person struct fields:
- name: str  # the full name of the person
- age: int  # the age in years (must be positive)
- email: str  # the email address for contact
- metadata: dict[str, str]  # additional metadata like occupation, hobbies, etc.
```

### 3. **Mixed Comments Support**
Structs can have fields with and without comments:

```dana
struct MixedStruct:
    required_field: str  # this field has a comment
    optional_field: int  # this field also has a comment
    simple_field: bool   # this field has no comment
```

### 4. **Complex Type Support**
Comments work with all Dana types including complex types:

```dana
struct ComplexStruct:
    metadata: dict[str, str]  # additional metadata dictionary
    tags: list[str]  # list of tags for categorization
    config: dict  # configuration settings
    nested: dict[str, dict]  # nested dictionary structure
```

## Benefits

### 1. **Improved LLM Reasoning**
Field comments provide context that helps LLMs understand:
- What each field represents
- Expected data formats and constraints
- Business logic and domain knowledge
- Relationships between fields

### 2. **Better Data Quality**
Enhanced prompts lead to:
- More accurate field values
- Proper data types and formats
- Consistent naming conventions
- Domain-appropriate content

### 3. **Self-Documenting Code**
Comments serve as inline documentation:
- Clear field purposes
- Usage examples and constraints
- Domain-specific requirements
- Implementation guidance

## Examples

### Basic Usage
```dana
struct User:
    username: str  # unique username for login
    email: str  # primary email address
    is_active: bool  # whether the user account is active
    created_at: str  # ISO 8601 timestamp of account creation
```

### Domain-Specific Examples
```dana
struct SemiconductorDevice:
    device_id: str  # unique device identifier (e.g., "DEV-2024-001")
    process_node: str  # manufacturing process node (e.g., "7nm", "5nm")
    wafer_size: int  # wafer diameter in millimeters (typically 200 or 300)
    yield_rate: float  # manufacturing yield percentage (0.0 to 100.0)
    test_results: dict[str, bool]  # test name to pass/fail mapping
```

### E-commerce Example
```dana
struct Order:
    order_id: str  # unique order identifier
    customer_id: str  # customer account identifier
    items: list[str]  # list of product IDs in the order
    total_amount: float  # total order value in dollars
    shipping_address: dict[str, str]  # complete shipping address
    order_status: str  # current order status (pending, shipped, delivered)
```

## Integration with POET System

Field comments are automatically integrated with Dana's POET (Prompt Optimization and Enhancement Technology) system:

1. **Context Detection**: When `reason()` is called with a struct type, the system detects the expected return type
2. **Comment Extraction**: Field comments are retrieved from the struct definition
3. **Prompt Enhancement**: Comments are included in the enhanced prompt sent to the LLM
4. **Response Generation**: The LLM uses the enhanced context to generate more accurate structured data

## Best Practices

### 1. **Descriptive Comments**
Use clear, concise descriptions:
```dana
# Good
name: str  # the full name of the person

# Avoid
name: str  # name
```

### 2. **Include Constraints**
Mention important constraints and formats:
```dana
age: int  # the age in years (must be positive)
email: str  # the email address for contact (valid email format)
price: float  # price in dollars (can include cents)
```

### 3. **Provide Examples**
Include examples for complex fields:
```dana
id: str  # unique product identifier (e.g., "PROD-001")
tags: list[str]  # list of tags (e.g., ["electronics", "gaming", "laptop"])
metadata: dict[str, str]  # additional metadata (e.g., {"brand": "Dell", "warranty": "2 years"})
```

### 4. **Domain Context**
Include domain-specific information:
```dana
process_node: str  # manufacturing process node (e.g., "7nm", "5nm")
yield_rate: float  # manufacturing yield percentage (0.0 to 100.0)
test_results: dict[str, bool]  # test name to pass/fail mapping
```

## Technical Implementation

### AST Structure
Field comments are captured in the AST as part of the `StructField` node:

```python
@dataclass
class StructField:
    name: str
    type_hint: TypeHint
    comment: str | None = None  # Field description from inline comment
    location: Location | None = None
```

### Runtime Storage
Comments are stored in the `StructType` for runtime access:

```python
@dataclass
class StructType:
    name: str
    fields: dict[str, str]  # Maps field name to type name string
    field_order: list[str]  # Maintain field declaration order
    field_comments: dict[str, str]  # Maps field name to comment/description
```

### Prompt Enhancement
Comments are automatically included in enhanced prompts:

```python
def get_field_description(self, field_name: str) -> str:
    """Get a formatted description of a field including type and comment."""
    field_type = self.fields.get(field_name, "unknown")
    comment = self.field_comments.get(field_name)
    
    if comment:
        return f"{field_name}: {field_type}  # {comment}"
    else:
        return f"{field_name}: {field_type}"
```

## Migration Guide

### Existing Structs
Existing structs without comments continue to work unchanged:

```dana
# This still works perfectly
struct LegacyStruct:
    name: str
    age: int
    email: str
```

### Adding Comments
Gradually add comments to existing structs:

```dana
# Before
struct User:
    username: str
    email: str
    is_active: bool

# After (enhanced with comments)
struct User:
    username: str  # unique username for login
    email: str  # primary email address
    is_active: bool  # whether the user account is active
```

## Conclusion

Struct field comments provide a powerful way to enhance LLM reasoning by providing rich context about data structures. This feature improves data quality, reduces errors, and makes Dana code more self-documenting while maintaining backward compatibility with existing struct definitions. 