# Dana Libraries Primer

## TL;DR (30 seconds read)

```dana
# 🎯 Zero imports needed - everything just works!

# Math functions - ready immediately
result = sum_range(1, 100)    # 5050
print(f"Sum 1-100: {result}")
print(f"7 is odd: {is_odd(7)}")          # true
print(f"Factorial 5: {factorial(5)}")    # 120

# Text functions - ready immediately  
print(capitalize_words("hello dana world"))   # "Hello Dana World"
print(title_case("artificial intelligence"))  # "Artificial Intelligence"

# AI functions - ready immediately
answer = reason("What's the capital of France?")
response = llm("Explain quantum computing briefly")

# All core functions available globally - no imports, no setup!
```

**🚀 Performance**: Core functions preloaded at startup (0ms runtime overhead)  
**🎯 Zero friction**: 20+ essential functions available immediately  
**🧠 AI-ready**: Reasoning, LLM, and agent functions built-in

---

## What Are Dana Libraries?

Dana Libraries is a **3-tier rationalized loading system** that eliminates import overhead for essential functions while maintaining modularity for advanced features.

**The Problem Solved**: Traditional languages force you to import basic functions (`import math`, `from collections import...`). Dana makes essentials globally available while keeping advanced features modular.

## The 3-Tier Architecture

```
📦 dana/libs/
├── 🚀 initlib/    # Startup & Environment (automatic)
├── ⚡ corelib/    # Core Functions (preloaded)  
└── 📚 stdlib/     # Extended Library (on-demand)
```

### Tier 1: Initialization Library (`initlib/`)
**When**: Runs automatically on `import dana`  
**Purpose**: Bootstrap Dana environment

```python
import dana  # This automatically:
# ✅ Loads .env files
# ✅ Initializes configuration
# ✅ Sets up module system  
# ✅ Preloads core functions
```

### Tier 2: Core Library (`corelib/`)
**When**: Preloaded during startup  
**Purpose**: Essential functions that every program needs

```dana
# These work immediately - no imports!
sum_range(1, 10)              # Math
capitalize_words("hello")     # Text  
reason("What is AI?")         # AI/LLM
print("Hello world")          # Output
log("Debug info")             # Logging
str(42)                       # Type conversion
```

### Tier 3: Standard Library (`stdlib/`)
**When**: Imported explicitly  
**Purpose**: Advanced utilities and specialized functionality

```dana
# Explicit imports for advanced features
import agent

# Now access advanced agent utilities
agents = create_agent_pool("CustomerService", 3)
cs_agent = agent_from_template("customer_service")
```

## Core Library Categories

### 📊 Math Functions
Essential mathematical operations without `import math`:

```dana
# Range operations
total = sum_range(1, 100)        # Sum 1 to 100 (inclusive)

# Number testing  
is_odd(7)                        # true
is_even(8)                       # true

# Mathematical functions
factorial(5)                     # 120 (5!)
```

### 📝 Text Functions
String processing without imports:

```dana
# Word capitalization
capitalize_words("hello world")   # "Hello World"
title_case("the great gatsby")    # "The Great Gatsby"

# More text functions available...
```

### 🤖 AI/LLM Functions
AI capabilities built into the language:

```dana
# Direct AI reasoning
answer = reason("Explain photosynthesis")

# LLM interactions
response = llm("Write a haiku about coding", "gpt-4")

# Context-aware reasoning
analysis = context_aware_reason("Analyze this data", context_data)

# Model configuration
set_model("claude-3-sonnet")
```

### 🛠️ Utility Functions
Common operations without boilerplate:

```dana
# Type conversion
str(123)                         # "123"
cast("int", "456")              # 456

# Output and logging
print("Hello", "world")          # Console output
log("Debug message", "DEBUG")    # Structured logging
log_level("INFO")               # Set log level

# No-op for testing/placeholders
noop()                          # Does nothing
```

### ⚙️ Framework Functions
Advanced framework features:

```dana
# POET enhancements
poet("reason", ["Analyze data"], domain="financial")
feedback(result, {"accuracy": 0.95})

# Resource management
rag_resource = use("rag", sources=["docs/"])
mcp_resource = use("mcp", server="claude-computer")
```

## Performance Model

### Startup Sequence
```
1. import dana
   ↓
2. initlib automatic startup
   ↓ 
3. Environment & config loading
   ↓
4. Core functions preloaded
   ↓
5. Ready for execution (≈50ms total)
```

### Runtime Performance
```
Core Functions:     0ms overhead (preloaded)
Stdlib Functions:   ~1-5ms (first use only)
Regular imports:    ~10-50ms (per import)
```

## Developer Mental Model

### Think in Tiers

**🟢 Always Available (Tier 2)**
- Math, text, basic AI, logging, utilities
- Zero imports, zero overhead
- Use freely in any Dana program

**🟡 Explicit Import (Tier 3)**  
- Advanced agent utilities, specialized tools
- `import module_name` when needed
- Modular and composable

**🔵 Automatic (Tier 1)**
- Environment, configuration, system setup  
- Happens transparently
- You don't think about it

### Writing Dana Code

**✅ Good Approach**:
```dana
# Start coding immediately
result = sum_range(1, 100)
analysis = reason("What does this result mean?")
print(f"Analysis: {analysis}")

# Import only when you need advanced features
import agent
agents = create_agent_pool("DataProcessor", 5)
```

**❌ Old Thinking**:
```python
# Don't think like this anymore!
import math
import textwrap
from ai_library import reasoning

result = sum(range(1, 101))  # Manual implementation
```

## Extending the System

### Adding Core Functions (Tier 2)
Create files in `dana/libs/corelib/py/`:

```python
# dana/libs/corelib/py/py_myfunction.py

def py_my_function(context, value):
    """My custom core function."""
    return f"Processed: {value}"

# Export for registration
__all__ = ["py_my_function"]
```

Function automatically available as `my_function()` in all Dana programs.

### Adding Stdlib Modules (Tier 3)
Create modules in `dana/libs/stdlib/`:

```python
# dana/libs/stdlib/mymodule/__init__.py

def advanced_utility():
    """Advanced functionality requiring explicit import."""
    return "Advanced result"
```

Use with explicit import:
```dana
import mymodule
result = advanced_utility()
```

## Best Practices

### When to Use Each Tier

**Use Core Library (Tier 2) for**:
- Functions used in >50% of programs
- Zero-dependency utilities
- Essential language operations
- Performance-critical functions

**Use Standard Library (Tier 3) for**:
- Specialized domain functionality  
- Functions with heavy dependencies
- Optional/advanced features
- Domain-specific utilities

### Performance Tips

```dana
# ✅ Prefer core functions (0ms overhead)
result = sum_range(1, 1000)

# ✅ Cache imports for repeated use
import heavy_module
for item in items:
    heavy_module.process(item)  # Module already loaded

# ❌ Avoid repeated imports in loops
for item in items:
    import heavy_module         # Wasteful
    heavy_module.process(item)
```

### Code Organization

```dana
# ✅ Core functions at the top (no imports needed)
total = sum_range(1, 100)
analysis = reason("Analyze this data")

# ✅ Imports grouped together
import agent
import advanced_math
import data_processing

# ✅ Use imported functions
agents = create_agent_pool("Processor", 3)
```

## Troubleshooting

### Function Not Found
```
Error: Function 'my_function' not found
```

**Check**:
1. Is it a core function? (should work immediately)
2. Do you need to import a stdlib module?
3. Is the function name correct?

### Slow Startup
```
Dana startup taking >500ms
```

**Solutions**:
1. Set `DANA_TEST_MODE=1` for testing (skips heavy init)
2. Check for custom .env files with complex processing
3. Profile with debug logging enabled

### Import Confusion
```
Which functions need imports?
```

**Rule of thumb**:
- **Math, text, AI, logging, utilities**: No imports
- **Advanced agents, specialized tools**: Import required
- **When unsure**: Try without import first!

## Advanced Topics

### Custom Initialization
```python
# Custom startup behavior
os.environ["DANA_TEST_MODE"] = "1"  # Skip heavy init
import dana
```

### Function Priority
Registration order:
1. Core Library Functions (highest priority)
2. Pythonic Built-in Functions (lowest priority)

Core functions override Python built-ins when names conflict.

### Registry Inspection
```dana
# Debug: See all available functions
import dana.core.lang.interpreter.functions.function_registry as registry
print(registry.list_functions())
```

---

## Summary

Dana Libraries transforms the development experience by:

**🎯 Eliminating Friction**: 20+ essential functions work immediately  
**⚡ Optimizing Performance**: Core functions preloaded for 0ms overhead  
**🏗️ Providing Structure**: Clear separation between core vs advanced features  
**🚀 Enabling Productivity**: Start coding immediately, import only when needed  

The system balances **convenience** (core functions always available) with **modularity** (stdlib requires explicit imports), giving you the best of both worlds.

**Next Steps**:
- Check out the [Core Functions Reference](corelib_functions.md) for complete function list
- See [Agent Primer](agent.md) for advanced agent functionality  
- Read [Import System](import.md) for module system details