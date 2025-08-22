# Dana Comprehensions Primer

## TL;DR (1 minute read)

Comprehensions in Dana provide a concise way to create lists, sets, and dictionaries by transforming and filtering data. They replace verbose loops with elegant, readable expressions.

```dana
# Instead of this verbose loop:
numbers = [1, 2, 3, 4, 5]
squares = []
for x in numbers:
    if x % 2 == 0:
        squares.append(x * x)

# Use this concise comprehension:
squares = [x * x for x in numbers if x % 2 == 0]
```

## What Are Comprehensions?

Comprehensions are a Python-inspired feature that lets you create collections (lists, sets, dictionaries) from existing data using a compact, expression-based syntax. They combine iteration, filtering, and transformation in a single line.

## List Comprehensions

### Basic Syntax
```dana
[expression for item in iterable]
```

### Examples
```dana
# Double each number
numbers = [1, 2, 3, 4, 5]
doubled = [x * 2 for x in numbers]
# Result: [2, 4, 6, 8, 10]

# Extract names from user objects
users = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
names = [user["name"] for user in users]
# Result: ["Alice", "Bob"]
```

### With Filtering
```dana
# Only even numbers
even = [x for x in numbers if x % 2 == 0]
# Result: [2, 4]

# Adults only
adults = [user["name"] for user in users if user["age"] >= 30]
# Result: ["Alice"]
```

## Set Comprehensions

### Basic Syntax
```dana
{expression for item in iterable}
```

### Examples
```dana
# Unique squares
squares = {x * x for x in numbers}
# Result: {1, 4, 9, 16, 25}

# Unique word lengths
words = ["hello", "world", "hello", "dana"]
lengths = {len(word) for word in words}
# Result: {5, 4}
```

## Dictionary Comprehensions

### Basic Syntax
```dana
{(key_expression: value_expression) for item in iterable}
```

**Note:** Dana uses parentheses around key-value pairs to distinguish dictionary comprehensions from set comprehensions, unlike Python's `{k: v for ...}` syntax.

### Examples
```dana
# Number to string mapping
number_map = {(x: str(x)) for x in numbers}
# Result: {1: "1", 2: "2", 3: "3", 4: "4", 5: "5"}

# Name to age lookup
age_lookup = {(user["name"]: user["age"]) for user in users}
# Result: {"Alice": 30, "Bob": 25}
```

## Common Patterns

### Safe Dictionary Access
```dana
data = [{"value": 1}, {}, {"value": 3}]
values = [item.get("value", 0) for item in data]
# Result: [1, 0, 3]
```

### Nested Data Flattening
```dana
matrix = [[1, 2], [3, 4], [5, 6]]
flattened = [x for row in matrix for x in row]
# Result: [1, 2, 3, 4, 5, 6]
```

### Conditional Transformation
```dana
numbers = [1, 2, 3, 4, 5]
result = [x * 2 if x % 2 == 0 else x * 3 for x in numbers]
# Result: [3, 4, 9, 8, 15]
```

## When to Use Comprehensions

### ✅ Good Use Cases
- **Simple transformations**: `[x * 2 for x in numbers]`
- **Filtering data**: `[x for x in data if x > 0]`
- **Extracting values**: `[item["key"] for item in items]`
- **Creating lookups**: `{k: v for k, v in data.items()}`

### ❌ Avoid When
- **Complex logic**: Use regular loops for multi-step operations
- **Side effects**: Comprehensions should be pure transformations
- **Performance-critical**: For very large datasets, consider alternatives
- **Debugging**: Loops are easier to debug step-by-step

## Best Practices

### 1. Keep It Readable
```dana
# Good - clear and readable
names = [user["name"] for user in users if user["age"] >= 18]

# Avoid - too complex
result = [f"{u['n']}:{u['a']}" for u in users if u['a'] >= 18 and u['n'].startswith('A')]
```

### 2. Use Descriptive Variable Names
```dana
# Good
squares = [number * number for number in numbers]

# Avoid
squares = [x * x for x in numbers]
```

### 3. Break Complex Comprehensions
```dana
# For complex logic, use multiple steps
filtered_users = [user for user in users if user["age"] >= 18]
names = [user["name"] for user in filtered_users]
```

## Common Mistakes

### 1. Forgetting the Expression
```dana
# Wrong - missing expression
result = [for x in numbers]

# Correct
result = [x for x in numbers]
```

### 2. Incorrect Dict Comprehension Syntax
```dana
# Wrong - missing parentheses (Python style)
result = {x: x * 2 for x in numbers}

# Wrong - missing colon
result = {x, x * 2 for x in numbers}

# Correct - Dana requires parentheses around key-value pairs
result = {(x: x * 2) for x in numbers}
```

### 3. Modifying Variables in Comprehension
```dana
# Wrong - modifying loop variable
result = [x + 1 for x in numbers if (x := x + 1) > 3]

# Correct - use separate variable
result = [x + 1 for x in numbers if x + 1 > 3]
```

## Performance Tips

- **Comprehensions are generally faster** than equivalent loops
- **Memory usage scales** with input size
- **For large datasets**, consider if you need all results at once
- **Profile your code** if performance is critical

## Python vs Dana Differences

Dana's comprehension syntax is largely compatible with Python, but has one key difference for dictionary comprehensions:

### Dictionary Comprehensions
```dana
# Python syntax
python_dict = {k: v for k, v in items}

# Dana syntax - requires parentheses around key-value pairs
dana_dict = {(k: v) for k, v in items}
```

**Why the difference?**
- **Disambiguation**: Parentheses clearly distinguish dict comprehensions from set comprehensions
- **Consistency**: Makes the key-value relationship explicit and visually distinct
- **Parsing clarity**: Eliminates ambiguity in Dana's grammar

### List and Set Comprehensions
```dana
# Identical in both Python and Dana
list_comp = [x * 2 for x in items]
set_comp = {x * 2 for x in items}
```

## Migration Guide

### From Python to Dana
```dana
# Python
ages = {name: age for name, age in users}

# Dana - add parentheses around key-value pairs
ages = {(name: age) for name, age in users}
```

### From Loops to Comprehensions

**Before:**
```dana
numbers = [1, 2, 3, 4, 5]
squares = []
for x in numbers:
    if x % 2 == 0:
        squares.append(x * x)
```

**After:**
```dana
numbers = [1, 2, 3, 4, 5]
squares = [x * x for x in numbers if x % 2 == 0]
```

### From Map/Filter to Comprehensions

**Before:**
```dana
numbers = [1, 2, 3, 4, 5]
filtered = filter(lambda x: x % 2 == 0, numbers)
squares = map(lambda x: x * x, filtered)
```

**After:**
```dana
numbers = [1, 2, 3, 4, 5]
squares = [x * x for x in numbers if x % 2 == 0]
```

### From Python Dict Comprehensions
```dana
# Python code
user_ages = {user.name: user.age for user in users if user.active}

# Dana equivalent - add parentheses around key-value pairs
user_ages = {(user.name: user.age) for user in users if user.active}
```

## Next Steps

- **Practice**: Try converting your existing loops to comprehensions
- **Explore**: Experiment with nested comprehensions and complex expressions
- **Read**: Check the full specification in `dana/specs/core/comprehensions.md`
- **Build**: Use comprehensions in your Dana projects for cleaner, more readable code 