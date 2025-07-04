# Dana Built-in Functions

Master Dana's powerful built-in functions for data processing, analysis, and manipulation. These functions are essential for real-world Dana applications.

## 🎯 Learning Objectives

By completing these examples, you'll master:
- ✅ Essential collection functions (`len()`, `sum()`, `max()`, `min()`)
- ✅ Type conversion functions (`int()`, `float()`, `bool()`)
- ✅ Data processing functions (`sorted()`, `enumerate()`, `all()`, `any()`)
- ✅ Mathematical operations (`abs()`, `round()`)
- ✅ Real-world data analysis patterns

## 📚 Examples (Recommended Order)

### 1. **builtin_functions_basic.na** ⭐ **START HERE**
```bash
uv run python -m dana.dana.exec.dana builtin_functions_basic.na
```
**What you'll learn:**
- Essential collection functions you'll use daily
- Grade analysis example with practical applications
- Core functions: `len()`, `sum()`, `max()`, `min()`, `int()`, `round()`
- Basic data processing patterns

**Perfect for:** New users who need the most important functions first

### 2. **pythonic_builtins_demo.na** ⭐ **COMPREHENSIVE REFERENCE**
```bash
uv run python -m dana.dana.exec.dana pythonic_builtins_demo.na
```
**What you'll learn:**
- Complete coverage of all Dana built-in functions
- Advanced collection processing with `sorted()`, `enumerate()`
- Boolean logic with `all()` and `any()`
- Complex data analysis examples
- Professional data processing patterns

**Perfect for:** Complete reference and advanced patterns

## 🚀 Quick Start

```bash
cd examples/dana/02_built_in_functions/

# Start with essentials (5-10 minutes)
uv run python -m dana.dana.exec.dana builtin_functions_basic.na

# Comprehensive exploration (15-20 minutes)
uv run python -m dana.dana.exec.dana pythonic_builtins_demo.na
```

## 💡 Key Functions by Category

### **Collection Analysis**
```dana
# Essential functions for working with lists/collections
scores = [85, 92, 78, 96, 88]

total_count = len(scores)        # 5
total_sum = sum(scores)          # 439
highest = max(scores)            # 96
lowest = min(scores)             # 78
average = sum(scores) / len(scores)  # 87.8
```

### **Type Conversions**
```dana
# Convert between different data types
grade_text = "87.5"
grade_number = float(grade_text)     # 87.5
grade_rounded = int(grade_number)    # 87
grade_int = round(grade_number)      # 88 (rounded to nearest)

# Boolean conversions
has_grade = bool(grade_number)       # true (non-zero is true)
```

### **Advanced Collection Processing**
```dana
# Sorting and enumeration
scores = [85, 92, 78, 96, 88]
sorted_scores = sorted(scores)       # [78, 85, 88, 92, 96]
sorted_desc = sorted(scores, reverse=true)  # [96, 92, 88, 85, 78]

# Enumerate for index + value
for index, score in enumerate(scores):
    log(f"Student {index + 1}: {score}")
```

### **Boolean Logic Functions**
```dana
# Test collections with all() and any()
passing_grades = [85, 92, 78, 96, 88]
all_passing = all(score >= 70 for score in passing_grades)  # true
any_excellent = any(score >= 95 for score in passing_grades)  # true

failing_grades = [65, 45, 78, 92, 55]  
all_failing = all(score < 70 for score in failing_grades)   # false
any_failing = any(score < 70 for score in failing_grades)   # true
```

### **Mathematical Functions**
```dana
# Mathematical operations
value = -42.7
absolute = abs(value)            # 42.7
rounded = round(value)           # -43
rounded_up = round(value, 1)     # -42.7 (1 decimal place)
```

## 🎯 Common Patterns

### **Data Analysis Pattern**
```dana
# Analyze a dataset
data = [23, 45, 67, 89, 12, 34, 56, 78]

# Basic statistics
private:count = len(data)
private:total = sum(data) 
private:average = total / count
private:minimum = min(data)
private:maximum = max(data)
private:range_value = maximum - minimum

log(f"Dataset Analysis:")
log(f"  Count: {count}")
log(f"  Average: {round(average, 2)}")
log(f"  Range: {minimum} to {maximum} (span: {range_value})")
```

### **Grade Processing Pattern**
```dana
# Process student grades
grades = [87.5, 92.3, 78.9, 95.1, 83.7]

# Convert to integers and analyze
private:rounded_grades = [round(grade) for grade in grades]
private:grade_count = len(rounded_grades)
private:total_points = sum(rounded_grades)
private:class_average = total_points / grade_count
private:highest_grade = max(rounded_grades)
private:lowest_grade = min(rounded_grades)

# Check performance
private:all_passing = all(grade >= 70 for grade in rounded_grades)
private:any_excellent = any(grade >= 95 for grade in rounded_grades)

log(f"Class Performance:")
log(f"  Average: {round(class_average, 1)}")
log(f"  Range: {lowest_grade} - {highest_grade}")
log(f"  All passing (≥70): {all_passing}")
log(f"  Any excellent (≥95): {any_excellent}")
```

### **Data Validation Pattern**
```dana
# Validate data quality
user_inputs = ["85", "92.5", "", "abc", "78"]

# Convert and validate
private:valid_numbers = []
for input_text in user_inputs:
    if input_text and input_text.replace(".", "").isdigit():
        private:number = float(input_text)
        private:valid_numbers.append(number)

if len(valid_numbers) > 0:
    private:average = sum(valid_numbers) / len(valid_numbers)
    log(f"Valid data: {valid_numbers}")
    log(f"Average: {round(average, 2)}")
else:
    log("No valid numeric data found")
```

### **Sorting and Ranking Pattern**
```dana
# Create rankings
students = ["Alice", "Bob", "Charlie", "Diana"]
scores = [88, 95, 82, 91]

# Combine and sort by score
private:student_scores = list(zip(students, scores))
private:ranked = sorted(student_scores, key=lambda x: x[1], reverse=true)

log("Class Rankings:")
for rank, (student, score) in enumerate(ranked, 1):
    log(f"  {rank}. {student}: {score}")
```

## 🔄 Practice Exercises

### **Exercise 1: Sales Analysis**
Create a sales analysis program using built-in functions:
```dana
# Monthly sales data
sales = [12500, 15300, 11800, 18200, 16900, 14700]

# Your task: Calculate and display:
# - Total sales for the period
# - Average monthly sales
# - Best and worst months
# - Check if all months exceeded $10,000
# - Check if any month exceeded $18,000
```

### **Exercise 2: Temperature Converter**
Build a temperature analysis tool:
```dana
# Temperature readings in Celsius
celsius_temps = [23.5, 28.3, 19.7, 31.2, 25.8]

# Your task:
# - Convert all to Fahrenheit: F = C * 9/5 + 32
# - Find hottest and coldest in both scales
# - Calculate average temperature
# - Round all results appropriately
```

### **Exercise 3: Inventory Management**
Create an inventory checker:
```dana
# Product quantities
inventory = [45, 0, 23, 7, 0, 156, 89, 12]

# Your task:
# - Count total items
# - Find items that need restocking (quantity < 10)
# - Check if any items are out of stock
# - Calculate average inventory level
# - Sort quantities to see distribution
```

## ⚠️ Common Mistakes

### ❌ **Don't Do This**
```dana
# Don't use Python-style list comprehensions incorrectly
numbers = [1, 2, 3]
doubled = [x * 2 for x in numbers]  # May not work in all Dana versions

# Don't forget to handle empty collections
empty_list = []
average = sum(empty_list) / len(empty_list)  # Division by zero!

# Don't ignore type conversion errors
invalid_number = int("abc")  # Will cause error
```

### ✅ **Do This Instead**
```dana
# Use explicit loops for transformations
numbers = [1, 2, 3]
private:doubled = []
for x in numbers:
    private:doubled.append(x * 2)

# Always check for empty collections
data = []
if len(data) > 0:
    private:average = sum(data) / len(data)
else:
    private:average = 0
    log("No data to average")

# Handle conversion errors gracefully
text_number = "abc"
try:
    private:number = int(text_number)
except:
    log(f"Could not convert '{text_number}' to integer")
    private:number = 0
```

## 📊 Function Reference Quick Guide

| Function | Purpose | Example |
|----------|---------|---------|
| `len(collection)` | Count items | `len([1, 2, 3])` → `3` |
| `sum(numbers)` | Add all numbers | `sum([1, 2, 3])` → `6` |
| `max(numbers)` | Find largest | `max([1, 3, 2])` → `3` |
| `min(numbers)` | Find smallest | `min([1, 3, 2])` → `1` |
| `sorted(collection)` | Sort collection | `sorted([3, 1, 2])` → `[1, 2, 3]` |
| `int(value)` | Convert to integer | `int("42")` → `42` |
| `float(value)` | Convert to float | `float("3.14")` → `3.14` |
| `round(number)` | Round to nearest | `round(3.7)` → `4` |
| `abs(number)` | Absolute value | `abs(-5)` → `5` |
| `all(booleans)` | All true? | `all([true, true])` → `true` |
| `any(booleans)` | Any true? | `any([false, true])` → `true` |
| `enumerate(collection)` | Index + value | `enumerate(["a", "b"])` → `[(0, "a"), (1, "b")]` |

## ➡️ **Next Steps**

Once you've mastered built-in functions:
1. **[Advanced Features](../03_advanced_features/)** - Learn AI reasoning and complex patterns
2. **[POET Examples](../04_poet_examples/)** - Add automatic optimization to your functions
3. **[MCP Integration](../05_mcp_integration/)** - Connect to external tools and services

---

**Ready for AI features?** Continue to **[03_advanced_features](../03_advanced_features/)** to explore Dana's powerful AI reasoning capabilities! 