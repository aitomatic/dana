# Dana Language Examples

A curated collection of high-quality examples demonstrating the Dana language, organized by complexity and use case. **Quality over quantity** - each example teaches essential concepts.

## 📚 **Streamlined Learning Path**

Follow this progression to master Dana efficiently:

| Level | Directory | Focus | Time | Examples |
|-------|-----------|-------|------|----------|
| **Beginner** | `01_language_basics/` | Core syntax and concepts | 30-45 min | 7 examples |
| **Intermediate** | `02_built_in_functions/` | Data processing essentials | 20-30 min | 2 comprehensive examples |
| **Advanced** | `03_advanced_features/` | AI reasoning and complex patterns | 45-60 min | 8 examples |
| **Specialist** | `04_poet_examples/` | Self-improving functions | 20-30 min | 4 focused examples |
| **Integration** | `05_mcp_integration/` | External tool integration | 15-20 min | 4 examples |
| **Object-Oriented** | `07_structs_and_functions/` | Structs + functions vs classes | 60-90 min | 4 comprehensive examples |

## 🗂️ **Curated Directory Organization**

### 📖 **01_language_basics/** - Essential Dana Concepts
Core Dana language features every developer needs to know.

**7 Examples:**
- `basic_assignments.na` - Variable assignments and scoping
- `arithmetic_example.na` - Mathematical operations  
- `fstrings.na` - String formatting and interpolation
- `multiple_scopes.na` - Scope management
- `logging.na` - Basic logging
- `log_levels.na` - Advanced logging levels
- `print_example.na` - Output methods

**Start here:** Perfect foundation for Dana development

### 🔧 **02_built_in_functions/** - Data Processing Power
Master Dana's essential built-in functions for real-world applications.

**2 Comprehensive Examples:**
- `builtin_functions_basic.na` ⭐ **Essential functions** - `len()`, `sum()`, `max()`, `min()`
- `pythonic_builtins_demo.na` ⭐ **Complete reference** - All built-in functions with examples

**Focus:** Essential functions you'll use every day

### 🚀 **03_advanced_features/** - AI and Complex Patterns
Dana's unique AI reasoning capabilities and sophisticated application patterns.

**8 Examples:**
- `reason_demo.na` - AI reasoning introduction
- `reasoning_example.na` - Practical AI applications
- `hybrid_math_agent.na` ⭐ **Flagship** - Complete AI agent with validation
- `temperature_monitor.na` - Real-world automation
- `function_composition_demo*.na` - Advanced composition patterns

**Highlight:** `hybrid_math_agent.na` showcases a complete AI-powered application

### 🎯 **04_poet_examples/** - Self-Improving Functions
POET (Parameter Optimization Engine + Training) examples for functions that get better over time.

**4 Focused Examples:**
- `poet_basic_demo.na` - Simple POET usage
- `poet_decorator_demo.na` - Configuration patterns
- `poet_learning_demo.na` - Advanced learning features  
- `poet_pipeline_demo.na` - POET in data pipelines

**Value:** Learn to build functions that optimize themselves automatically

### 🔌 **05_mcp_integration/** - External Tool Integration
Model Context Protocol (MCP) examples for connecting Dana to external systems.

**4 Examples:**
- `setup.md` - Configuration guide
- `start_*.py` - Server setup scripts
- `na/test_use_stmt.na` - Using MCP resources
- `na/test_with_stmt.na` - Resource management

**Purpose:** Connect Dana to real-world tools and APIs

### 🐛 **06_debugging_tools/** - Error Handling
Essential debugging and error handling examples.

**2 Examples:**
- `syntax_errors.na` - Common syntax errors and solutions
- `error_locations.na` - Error location and debugging techniques

**Focus:** Debug Dana code effectively

### 🏗️ **07_structs_and_functions/** - Alternative to Python Classes
Comprehensive examples of Dana's struct + function approach as an elegant alternative to Python's class-based OOP.

**4 Comprehensive Examples:**
- `01_basic_struct_functions.na` ⭐ **Start here** - Basic struct and function patterns
- `02_polymorphic_functions.na` - Function overloading and inheritance alternatives
- `03_nested_structs_composition.na` - Complex data modeling with composition
- `04_structs_in_pipelines.na` - Data transformation workflows with type safety

**Key Value:** Learn how Dana achieves object-oriented benefits through clear separation of data (structs) and behavior (functions), enabling better composability, testability, and type safety than traditional classes.

### 📋 **reference/** - Supporting Materials
Documentation, utilities, and reference materials.

**Contents:**
- `python_utilities/` - Python helper scripts for running examples
- Documentation and setup guides

## 🚀 **Quick Start Guide**

### **New to Dana?** (Start Here - 15 minutes)
```bash
# Essential foundation
uv run python -m dana.dana.exec.dana examples/dana/01_language_basics/basic_assignments.na
uv run python -m dana.dana.exec.dana examples/dana/01_language_basics/arithmetic_example.na

# Essential functions
uv run python -m dana.dana.exec.dana examples/dana/02_built_in_functions/builtin_functions_basic.na
```

### **Ready for AI Features?** (20 minutes)
```bash
# AI reasoning introduction
uv run python -m dana.dana.exec.dana examples/dana/03_advanced_features/reason_demo.na

# Complete AI agent example
uv run python -m dana.dana.exec.dana examples/dana/03_advanced_features/hybrid_math_agent.na
```

### **Want Self-Improving Functions?** (15 minutes)
```bash
# POET basics
uv run python -m dana.dana.exec.dana examples/dana/04_poet_examples/poet_basic_demo.na

# Advanced POET features
uv run python -m dana.dana.exec.dana examples/dana/04_poet_examples/poet_learning_demo.na
```

## 🎯 **Quality-Focused Approach**

### **What We Removed:**
- ❌ **Test artifacts** - Files like `test_01_minimal.na` that were just 3-line test cases
- ❌ **Python utilities** - Moved to `reference/python_utilities/` where they belong
- ❌ **Validation files** - Internal test files like `poet_empty_domain_test.na`
- ❌ **Debug fragments** - Tiny debugging files that don't teach concepts
- ❌ **Duplicates** - Eliminated duplicate files across old and new structure

### **What We Kept:**
- ✅ **Learning examples** - Files that teach important Dana concepts
- ✅ **Real-world patterns** - Practical applications you can build on
- ✅ **Progressive difficulty** - Clear learning progression
- ✅ **Complete applications** - Like `hybrid_math_agent.na` that show full patterns

### **Result: 31 High-Quality Examples**
- **Before:** 50+ scattered files with duplicates and test artifacts
- **After:** 31 carefully curated examples that teach essential concepts
- **Focus:** Every example serves a clear learning purpose

## 🎓 **Example Categories by Purpose**

### **Learning Dana Language**
1. `01_language_basics/basic_assignments.na` - Your first Dana program
2. `02_built_in_functions/builtin_functions_basic.na` - Essential functions
3. `01_language_basics/fstrings.na` - String formatting

### **Building AI Applications**  
1. `03_advanced_features/reason_demo.na` - AI reasoning introduction
2. `03_advanced_features/hybrid_math_agent.na` - Complete AI agent
3. `04_poet_examples/poet_learning_demo.na` - Self-improving AI

### **Production Applications**
1. `03_advanced_features/temperature_monitor.na` - Real-world monitoring
2. `04_poet_examples/poet_pipeline_demo.na` - Optimized data pipelines
3. `05_mcp_integration/` - External system integration

### **Debugging and Development**
1. `06_debugging_tools/syntax_errors.na` - Common error patterns
2. `06_debugging_tools/error_locations.na` - Debugging techniques

## 🔧 **Running Examples**

### **Individual Examples**
```bash
# Basic Dana syntax
uv run python -m dana.dana.exec.dana examples/dana/01_language_basics/basic_assignments.na

# AI reasoning  
uv run python -m dana.dana.exec.dana examples/dana/03_advanced_features/reason_demo.na

# Self-improving functions
uv run python -m dana.dana.exec.dana examples/dana/04_poet_examples/poet_basic_demo.na
```

### **Run All Examples in a Category**
```bash
# Run all basic examples
for file in examples/dana/01_language_basics/*.na; do
    echo "=== Running $file ==="
    uv run python -m dana.dana.exec.dana "$file"
done
```

### **Using Python Utilities**
```bash
# Use helper scripts (moved to proper location)
python examples/dana/reference/python_utilities/run_examples.py
```

## 💡 **Key Learning Outcomes**

### **After 01_language_basics/** (30 minutes)
- ✅ Understand Dana syntax and scoping
- ✅ Use f-strings and logging effectively
- ✅ Handle basic data types and operations

### **After 02_built_in_functions/** (20 minutes)  
- ✅ Master essential collection functions
- ✅ Process data efficiently with built-ins
- ✅ Apply type conversions and mathematical operations

### **After 03_advanced_features/** (45 minutes)
- ✅ Integrate AI reasoning into applications
- ✅ Build complete AI agents with validation
- ✅ Implement real-world automation patterns

### **After 04_poet_examples/** (20 minutes)
- ✅ Create self-optimizing functions
- ✅ Configure domain-specific intelligence
- ✅ Monitor learning progress and effectiveness

## 🎯 **Best Practices Demonstrated**

### **Code Quality**
- Use `log()` instead of `print()` for debugging
- Apply f-strings for string formatting: `f"Hello {name}"`
- Implement proper error handling and validation
- Structure code with clear functions and scopes

### **AI Integration**
- Provide clear, specific prompts to AI reasoning
- Validate AI responses when possible  
- Combine AI reasoning with deterministic validation
- Handle AI failures gracefully

### **Production Readiness**
- Use POET for automatic parameter optimization
- Implement comprehensive monitoring and alerting
- Design for scalability and maintainability
- Apply proper logging and debugging techniques

## 🔗 **Related Resources**

### **Core Documentation**
- **[Dana Language Reference](../../../docs/.ai-only/dana.md)** - Complete language specification
- **[POET Documentation](../../../docs/dana/poet/)** - Parameter optimization guide
- **[3D Methodology](../../../docs/.ai-only/3d.md)** - Development best practices

### **Advanced Topics**
- **[Real-World Applications](../../04_real_world_applications/)** - Production examples
- **[Agent Framework](../../02_core_concepts/)** - Multi-agent systems
- **[Dana Architecture](../../for-engineers/)** - Framework overview

---

**🎉 Ready to start?** Begin with **`01_language_basics/basic_assignments.na`** and follow the progression. Each example builds essential Dana skills efficiently.