# Python-to-Dana Integration: Basic Tutorials

**Learn how to seamlessly integrate Dana language capabilities into your Python applications**

This directory contains a comprehensive set of tutorials that demonstrate how to use Python-to-Dana integration to leverage Dana's AI-first features, domain-specific reasoning, and neurosymbolic capabilities directly from Python code.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- OpenDXA framework installed
- Basic familiarity with Python

### Setup

1. **Install dependencies (if not already done):**
   ```bash
   # From the opendxa root directory
   uv install
   ```

2. **Navigate to the tutorial directory:**
   ```bash
   cd opendxa/contrib/python_to_dana/examples/basic
   ```

3. **Run your first tutorial:**
   ```bash
   python 01_dana_reason_basics.py
   ```

## 📚 Tutorial Index

### **Tutorial 01: Dana Reason Basics** (`01_dana_reason_basics.py`)
**What you'll learn**: Foundation of Dana's `reason()` function for AI-powered decision making
- Basic `reason()` function usage
- Context-aware decision making
- Simple AI reasoning patterns

**Prerequisites**: None  
**Difficulty**: ⭐ Beginner  
**Duration**: 1-5 minutes

---

### **Tutorial 02: Reason vs Traditional** (`02_reason_vs_traditional.py`)
**What you'll learn**: Compare traditional Python logic with Dana's AI reasoning
- Side-by-side comparison of approaches
- Understanding when AI reasoning adds value
- Best practices for choosing the right approach

**Prerequisites**: Tutorial 01  
**Difficulty**: ⭐ Beginner  
**Duration**: 1-5 minutes

---

### **Tutorial 03: Importing Dana Modules** (`03_importing_dana_modules.py`)
**What you'll learn**: How to import and use Dana .na files directly in Python
- Dana module import system
- Function calling between Python and Dana
- Module search paths and configuration

**Prerequisites**: Tutorial 01-02  
**Difficulty**: ⭐⭐ Intermediate  
**Duration**: 5-10 minutes

---

### **Tutorial 04: Scope Access Tutorial** (`04_scope_access_tutorial.py`)
**What you'll learn**: Understanding Dana's unique scoping system from Python
- Dana's four scope types: `local:`, `public:`, `private:`, `system:`
- Accessing scoped variables from Python
- Scope-based state management
- Inter-agent communication patterns

**Prerequisites**: Tutorial 01-03  
**Difficulty**: ⭐⭐ Intermediate  
**Duration**: 5-10 minutes

---

### **Tutorial 05: Data Structures Guide** (`05_data_structures_guide.py`)
**What you'll learn**: Working with Dana structs and data types from Python
- Creating and using Dana structs
- Type safety and validation
- Data transformation between Python and Dana
- Complex data structure patterns

**Prerequisites**: Tutorial 01-04  
**Difficulty**: ⭐⭐ Intermediate  
**Duration**: 5-10 minutes

---

### **Tutorial 06: Function Pipelines** (`06_function_pipelines.py`)
**What you'll learn**: Dana's powerful function composition and pipeline features
- Pipeline operator (`|`) usage
- Function composition patterns
- Data processing workflows
- Combining Python and Dana functions in pipelines

**Prerequisites**: Tutorial 01-05  
**Difficulty**: ⭐⭐⭐ Advanced  
**Duration**: 5-10 minutes

---

### **Tutorial 07: AI Reasoning Guide** (`07_ai_reasoning_guide.py`)
**What you'll learn**: Advanced AI reasoning patterns and best practices
- Complex reasoning scenarios
- Context management for AI decisions
- Chaining reasoning calls
- Production-ready AI reasoning patterns

**Prerequisites**: Tutorial 01-06  
**Difficulty**: ⭐⭐⭐ Advanced  
**Duration**: 10-15 minutes

## 📁 Directory Structure

```
basic/
├── README.md                         # This tutorial index
├── 01_dana_reason_basics.py          # Introduction to Dana reasoning
├── 02_reason_vs_traditional.py       # Comparing approaches
├── 03_importing_dana_modules.py      # Module import system
├── 04_scope_access_tutorial.py       # Dana scoping system
├── 05_data_structures_guide.py       # Structs and data types
├── 06_function_pipelines.py          # Function composition
├── 07_ai_reasoning_guide.py          # Advanced AI patterns
└── dana/                             # Dana module files
    ├── ai_reasoning.na               # AI reasoning examples
    ├── data_structures.na            # Struct definitions
    └── pipelines.na                  # Pipeline functions
```

## 🎯 Learning Path Recommendations

### **For Python Developers New to AI**
1. Tutorial 01 → Tutorial 02 → Tutorial 07
2. Focus on understanding when AI reasoning adds value
3. Practice with simple decision-making scenarios

### **For AI/ML Engineers**
1. Tutorial 01 → Tutorial 03 → Tutorial 06 → Tutorial 07
2. Focus on pipeline composition and advanced reasoning
3. Explore neurosymbolic programming patterns


### **Complete Learning Path**
Follow tutorials 01-08 in order for comprehensive understanding

## 🔧 Configuration & Setup

### Custom Search Paths
If your Dana modules are in custom locations, you can configure search paths:

```python
from opendxa.contrib.python_to_dana.core.module_importer import install_import_hook

# Install with custom search paths
install_import_hook(
    search_paths=[
        "/path/to/your/dana/modules",
        "/another/path/to/modules"
    ],
    debug=True
)
```

## 🐛 Troubleshooting

### Common Issues

**"Dana module not found"**
- Check that your .na files are in the search paths
- Verify file names don't have syntax errors
- Ensure Dana module system is properly initialized

**"Sandbox execution failed"**
- Check Dana syntax in your .na files
- Look for missing imports or undefined variables
- Enable debug mode for detailed error messages

**"Function not callable"**
- Verify function is defined in Dana module
- Check function signatures match your call
- Ensure module is properly imported

### Getting Help

1. **Enable debug mode** in tutorials for detailed output
2. **Check the OpenDXA documentation** for Dana syntax reference
3. **Run tests** to verify your setup: `uv run pytest tests/contrib/python_to_dana/ -v`
4. **Review error messages** carefully - they often contain specific guidance

## 🚀 Next Steps

After completing these tutorials:

1. **Explore Advanced Examples**: Check `../advanced/` directory for complex patterns
2. **Read Design Documentation**: Review `docs/design/` for architectural insights
3. **Contribute**: Try implementing your own integration patterns
4. **Production Use**: Apply patterns to your real-world projects

## 📖 Additional Resources

- [Dana Language Specification](../../../../docs/design/01_dana_language_specification/overview.md)
- [Python-to-Dana Architecture Guide](../../README_module_import.md)
- [OpenDXA Framework Documentation](../../../../docs/)
- [Contributing Guide](../../../../docs/for-contributors/)

---

**Happy Learning!** 🎉

*These tutorials are designed to be hands-on and practical. Don't just read the code - run it, modify it, and experiment with your own variations!* 