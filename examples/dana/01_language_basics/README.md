# Dana Language Basics

Essential Dana language concepts and syntax. **Start here** if you're new to Dana.

## 🎯 Learning Objectives

By completing these examples, you'll understand:
- ✅ Dana syntax and variable assignment patterns
- ✅ Scope management (private, local, global)
- ✅ String operations and f-string formatting
- ✅ Logging and debugging techniques
- ✅ Basic arithmetic and data types

## 📚 Examples (Recommended Order)

### 1. **basic_assignments.na** - Your First Dana Program
```bash
uv run python -m opendxa.dana.exec.dana basic_assignments.na
```
**What you'll learn:**
- Variable assignment to different scopes
- Different data types (integers, strings, negative numbers)
- Comment handling
- Basic program structure

**Key concepts:** `private:x = 10`, scope usage, basic syntax

### 2. **arithmetic_example.na** - Mathematical Operations
```bash
uv run python -m opendxa.dana.exec.dana arithmetic_example.na
```
**What you'll learn:**
- Float literals and arithmetic operations
- Mixed types and operator precedence
- Mathematical calculations in Dana

**Key concepts:** Float math, operator precedence, numeric types

### 3. **fstrings.na** - String Formatting
```bash
uv run python -m opendxa.dana.exec.dana fstrings.na
```
**What you'll learn:**
- F-string interpolation syntax
- Variable embedding in strings
- Dynamic string creation

**Key concepts:** `f"Hello {name}"`, string interpolation, dynamic content

### 4. **multiple_scopes.na** - Scope Management
```bash
uv run python -m opendxa.dana.exec.dana multiple_scopes.na
```
**What you'll learn:**
- Different scope types and their uses
- Organizing data hierarchically
- Scope-based state management

**Key concepts:** `private:`, `local:`, `global:`, scope organization

### 5. **logging.na** - Basic Logging
```bash
uv run python -m opendxa.dana.exec.dana logging.na
```
**What you'll learn:**
- Basic logging with `log()` function
- Debugging output techniques
- When to use logging vs other output methods

**Key concepts:** `log()` function, debugging practices

### 6. **log_levels.na** - Advanced Logging
```bash
uv run python -m opendxa.dana.exec.dana log_levels.na
```
**What you'll learn:**
- Different logging levels (INFO, DEBUG, ERROR)
- Controlling logging verbosity
- Production vs development logging

**Key concepts:** `log.info()`, `log.debug()`, logging levels

### 7. **print_example.na** - Output Methods
```bash
uv run python -m opendxa.dana.exec.dana print_example.na
```
**What you'll learn:**
- Different output methods in Dana
- When to use each output approach
- Console output patterns

**Key concepts:** Output methods, console interaction

## 🚀 Quick Start

Run all basic examples in sequence:

```bash
cd examples/dana/01_language_basics/

# Essential progression
uv run python -m opendxa.dana.exec.dana basic_assignments.na
uv run python -m opendxa.dana.exec.dana arithmetic_example.na  
uv run python -m opendxa.dana.exec.dana fstrings.na
uv run python -m opendxa.dana.exec.dana multiple_scopes.na
```

## 💡 Key Dana Concepts Introduced

### **Variable Assignment and Scoping**
```dana
# Different scope patterns
private:user_name = "Alice"      # Private to current context
local:temp_value = 42           # Local scope
global:app_state = "running"    # Global application state
```

### **String Formatting**
```dana
# F-string interpolation (preferred)
name = "Dana"
message = f"Hello, {name}!"     # Result: "Hello, Dana!"
```

### **Logging Best Practices**
```dana
# Use log() for debugging, not print()
log(f"Processing user: {user_name}")
log.info("Application started successfully")
log.debug(f"Debug info: {debug_data}")
```

### **Data Types and Operations**
```dana
# Numeric operations
private:score = 85.5
private:bonus = 10
private:total = score + bonus    # 95.5

# String operations  
private:greeting = "Hello"
private:name = "World"
private:message = f"{greeting}, {name}!"
```

## 🎯 Common Patterns

### **Initialization Pattern**
```dana
# Set up initial state
private:app_name = "MyApp"
private:version = "1.0"
private:status = "initializing"

log(f"Starting {app_name} v{version}")
private:status = "running"
```

### **Data Processing Pattern**
```dana
# Process and transform data
private:input_value = 42
private:processed = input_value * 2.5
private:result = f"Processed value: {processed}"
log(result)
```

### **Scope Organization Pattern**
```dana
# Organize related data in scopes
private:user = {
    "name": "Alice",
    "age": 30,
    "active": true
}

private:session = {
    "start_time": "2024-01-01T10:00:00",
    "duration": 3600
}
```

## ⚠️ Common Mistakes to Avoid

### ❌ **Don't Do This**
```dana
# Avoid unquoted strings
private:name = hello    # ERROR: hello is not defined

# Avoid mixing scope styles inconsistently  
private:data1 = "value"
data2 = "value"        # Unclear scope

# Avoid print() for debugging
print("Debug info")    # Use log() instead
```

### ✅ **Do This Instead**
```dana
# Use quoted strings
private:name = "hello"

# Be explicit about scopes
private:data1 = "value"
private:data2 = "value"

# Use proper logging
log("Debug info")
log.info("Application event")
```

## 🔄 Practice Exercises

After completing the examples, try these modifications:

### **Exercise 1: Personal Data**
Modify `basic_assignments.na` to store and display your personal information:
```dana
private:first_name = "Your Name"
private:age = 25
private:favorite_color = "blue"
log(f"Hi, I'm {first_name}, age {age}, and I love {favorite_color}")
```

### **Exercise 2: Calculator**
Extend `arithmetic_example.na` to build a simple calculator:
```dana
private:a = 15
private:b = 7
private:sum = a + b
private:difference = a - b
private:product = a * b
private:quotient = a / b
log(f"{a} + {b} = {sum}")
log(f"{a} - {b} = {difference}")
log(f"{a} * {b} = {product}")
log(f"{a} / {b} = {quotient}")
```

### **Exercise 3: Logging Levels**
Create a program that uses different logging levels appropriately:
```dana
log.info("Application starting")
private:config_file = "app.config"
log.debug(f"Loading configuration from {config_file}")
private:user_count = 150
log.info(f"Loaded {user_count} users")
log.debug("Initialization complete")
```

## ➡️ **Next Steps**

Once you've mastered these basics:
1. **[Built-in Functions](../02_built_in_functions/)** - Learn essential data processing functions
2. **[Advanced Features](../03_advanced_features/)** - Explore AI reasoning and complex patterns
3. **[POET Examples](../04_poet_examples/)** - Add automatic optimization to your functions

---

**Ready to continue?** Head to **[02_built_in_functions](../02_built_in_functions/)** to learn about Dana's powerful built-in functions! 