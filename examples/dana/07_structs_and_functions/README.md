# Dana Structs and Functions - Alternative to Python Classes

This directory demonstrates how Dana uses **structs + functions** as a powerful alternative to Python's class-based object-oriented programming. Dana's approach provides clear separation of data and behavior, better composability, and explicit type safety.

## 🎯 Learning Objectives

After completing these examples, you will understand:

- How Dana structs replace Python classes for data modeling
- How external functions replace class methods
- Polymorphic function patterns for type-specific behavior  
- Composition patterns for complex data relationships
- How structs integrate with Dana's pipeline system
- Advantages of struct/function approach over inheritance

## 📚 Examples Overview

### [`01_basic_struct_functions.na`](01_basic_struct_functions.na) ⭐ **Start Here**
**Estimated Time:** 15 minutes

**What You'll Learn:**
- Basic struct definition and instantiation
- Constructor-like functions for structs
- "Method-like" functions that operate on structs
- Direct field access vs encapsulation
- Key differences from Python classes

**Key Concepts:**
```dana
# Struct definition (data only)
struct Person:
    name: str
    age: int
    skills: list

# External functions (behavior)
def create_person(name: str, age: int) -> Person:
    return Person(name=name, age=age, skills=[])

def add_skill(person: Person, skill: str) -> Person:
    person.skills.append(skill)
    return person
```

### [`02_polymorphic_functions.na`](02_polymorphic_functions.na) ⭐⭐
**Estimated Time:** 25 minutes

**What You'll Learn:**
- Function overloading based on parameter types
- Alternative to inheritance hierarchies
- Polymorphic behavior without class inheritance
- Composition patterns for generic behavior

**Key Concepts:**
```dana
# Multiple struct types
struct Rectangle: width: float, height: float
struct Circle: radius: float

# Polymorphic functions (same name, different types)
def area(rect: Rectangle) -> float: return rect.width * rect.height
def area(circle: Circle) -> float: return 3.14159 * circle.radius * circle.radius
```

### [`03_nested_structs_composition.na`](03_nested_structs_composition.na) ⭐⭐⭐
**Estimated Time:** 30 minutes

**What You'll Learn:**
- Complex data modeling with nested structs
- Business logic implementation without classes
- Deep data access patterns
- Managing relationships between entities

**Key Concepts:**
```dana
# Nested composition
struct Contact:
    email: str
    address: Address

struct Employee:
    name: str
    contact: Contact
    skills: list

# Complex business logic
def get_company_summary(company: Company) -> dict:
    # Access nested data: company.employees[0].contact.address.city
```

### [`04_structs_in_pipelines.na`](04_structs_in_pipelines.na) ⭐⭐⭐
**Estimated Time:** 25 minutes

**What You'll Learn:**
- Data transformation workflows using structs
- Pipeline composition with type safety
- Functional programming patterns
- Building reusable data processing components

**Key Concepts:**
```dana
# Pipeline transformation: RawData → Validated → Processed → Formatted
processing_pipeline = validate_raw_data | enrich_validated_data | format_for_output
result = raw_data | processing_pipeline
```

## 🚀 Quick Start

1. **Start with basic concepts:**
   ```bash
   uv run python -m opendxa.dana.exec.dana examples/dana/07_structs_and_functions/01_basic_struct_functions.na
   ```

2. **Progress through examples in order:**
   - Each builds on concepts from previous examples
   - Pay attention to the comparison comments with Python equivalents

3. **Experiment with modifications:**
   - Add new fields to existing structs
   - Create new functions that operate on the structs
   - Try combining concepts from different examples

## 💡 Key Design Principles

### **Dana Approach: Structs + Functions**
```dana
# ✅ DANA WAY
struct Person: name: str, age: int
def greet(person: Person) -> str: return f"Hello, {person.name}"

person = Person(name="Alice", age=30)
message = greet(person)
```

### **Python Approach: Classes + Methods**
```python
# Traditional Python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        return f"Hello, {self.name}"

person = Person("Alice", 30)
message = person.greet()
```

## ✅ Advantages of Dana's Approach

| Aspect | Dana Structs + Functions | Python Classes |
|--------|-------------------------|----------------|
| **Data/Behavior** | Clear separation | Mixed together |
| **Composability** | High - mix any functions | Limited by inheritance |
| **Type Safety** | Explicit function signatures | Runtime method resolution |
| **Testability** | Each function independent | Methods tied to class state |
| **Complexity** | No inheritance chains | Can become complex hierarchies |
| **Flexibility** | Add functions without modifying structs | Must modify class for new methods |

## 🔧 Common Patterns

### **Constructor Pattern**
```dana
def create_user(name: str, email: str) -> User:
    return User(
        name=name,
        email=email,
        active=true,
        created_at=get_current_time()
    )
```

### **Validation Pattern**
```dana
def validate_user(user: User) -> bool:
    return user.email.contains("@") and len(user.name) > 0
```

### **Transformation Pattern**
```dana
def user_to_display_format(user: User) -> DisplayUser:
    return DisplayUser(
        display_name=f"{user.name} ({user.email})",
        status="Active" if user.active else "Inactive"
    )
```

### **Polymorphic Pattern**
```dana
def process_shape(rect: Rectangle) -> float: # Rectangle-specific logic
def process_shape(circle: Circle) -> float:  # Circle-specific logic
```

## 🧪 Practice Exercises

1. **Basic Exercise:** Create a `Book` struct and functions for:
   - Creating books with validation
   - Adding/removing from a library
   - Searching by title or author

2. **Intermediate Exercise:** Model a blog system with:
   - `Post`, `Author`, `Comment` structs
   - Functions for publishing, commenting, user management
   - Polymorphic functions for different content types

3. **Advanced Exercise:** Build a data processing pipeline:
   - Raw data validation → cleaning → enrichment → output
   - Multiple output formats (JSON, CSV, formatted display)
   - Error handling and logging throughout pipeline

## 🎯 Next Steps

After mastering structs and functions:

1. **Explore AI Integration:** See how structs work with `reason()` functions
2. **Study Pipeline Patterns:** Advanced data transformation workflows  
3. **Learn Module Organization:** Organizing related structs and functions
4. **Practice POET Integration:** Self-improving functions with struct parameters

## 📖 Related Documentation

- **[Dana Language Reference](../../../docs/.ai-only/dana.md)** - Complete syntax guide
- **[Pipeline Examples](../03_advanced_features/)** - Advanced pipeline patterns
- **[POET Examples](../04_poet_examples/)** - Self-improving functions with structs

## 🚨 Common Pitfalls

1. **Forgetting Named Arguments:**
   ```dana
   ❌ person = Person("Alice", 30)  # Wrong - positional args
   ✅ person = Person(name="Alice", age=30)  # Correct - named args
   ```

2. **Missing Type Hints:**
   ```dana
   ❌ def process(data): return data  # Wrong - no types
   ✅ def process(data: User) -> str: return data.name  # Correct
   ```

3. **Trying to Add Methods to Structs:**
   ```dana
   ❌ struct Person:
           name: str
           def greet(self): pass  # Wrong - structs are data only
   
   ✅ struct Person: name: str
      def greet(person: Person) -> str: return f"Hello {person.name}"
   ```

This directory showcases Dana's elegant alternative to object-oriented programming, emphasizing clarity, composability, and type safety through the powerful combination of structs and functions. 