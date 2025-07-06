# Dana - Domain-Aware Neurosymbolic Architecture

Claude AI Configuration and Guidelines

## Quick Reference - Critical Rules
🚨 **MUST FOLLOW IMMEDIATELY**
- Use standard Python logging: `import logging; logger = logging.getLogger(__name__)`
- Apply appropriate logging patterns for Dana development
- Always use f-strings: `f"Value: {var}"` not `"Value: " + str(var)`
- Dana modules: `import math_utils` (no .na), Python modules: `import math.py`
- **ALL temporary development files go in `tmp/` directory**
- Run `uv run ruff check . && uv run ruff format .` before commits
- Use type hints: `def func(x: int) -> str:` (required)
- **Apply KISS/YAGNI**: Start simple, add complexity only when needed

## Essential Commands
```bash
# Core development workflow
uv run ruff check . && uv run ruff format .    # Lint and format
uv run pytest tests/ -v                        # Run tests with verbose output (includes .na files)

# Dana execution - PREFER .na files for Dana functionality testing
dana examples/dana/01_language_basics/hello_world.na                      # Direct dana command (recommended)
dana --debug examples/dana/01_language_basics/hello_world.na              # With debug output
uv run python -m dana.core.repl.dana examples/dana/01_language_basics/hello_world.na  # Alternative

# Interactive development
dana                                            # Start Dana REPL (recommended)
uv run python -m dana.core.repl.repl          # Alternative REPL entry point

# Alternative test execution
uv run python -m pytest tests/
```

## Project Context
- Dana is a framework for building domain-expert multi-agent systems
- Built on Dana (Domain-Aware NeuroSymbolic Architecture) language
- Core components: Dana Framework, Dana Language
- Primary language: Python 3.12+
- Uses uv for dependency management

## File Modification Priority
1. **NEVER modify core grammar files without extensive testing**
2. **Always check existing examples before creating new ones**
3. **ALL temporary development files go in `tmp/` directory**
4. **Prefer editing existing files over creating new ones**

## Dana Language Syntax Reference

For comprehensive Dana language documentation including syntax, scoping, data types, functions, structs, pipelines, module system, and AI integration, see:

**📖 [docs/.ai-only/dana.md](dana.md) - Complete Dana Language Reference**

Dana is a Domain-Aware NeuroSymbolic Architecture language for AI-driven automation and agent systems.

Quick Dana reminders:
- **Dana modules**: `import math_utils` (no .na), **Python modules**: `import math.py`
- **Use `log()` for examples/testing output** (preferred for color coding and debugging)
- **For Dana INFO logging to show**: Use `log_level("INFO", "dana")` (default is WARNING level)
- **Always use f-strings**: `f"Value: {var}"` not `"Value: " + str(var)`
- **Type hints required**: `def func(x: int) -> str:` (mandatory)
- **Named arguments for structs**: `Point(x=5, y=10)` not `Point(5, 10)`
- **Prefer `.na` (Dana) test files over `.py`** for Dana-specific functionality

## 3D Methodology (Design-Driven Development)

For comprehensive 3D methodology guidelines including design documents, implementation phases, quality gates, example creation, and unit testing standards, see:

**📋 [docs/.ai-only/3d.md](3d.md) - Complete 3D Methodology Reference**

Key principle: Think before you build, build with intention, ship with confidence.

Quick 3D reminders:
- **Always create design document first** using the template in 3D.md
- **Run `uv run pytest tests/ -v` at end of every phase** - 100% pass required
- **Update implementation progress checkboxes** as you complete each phase
- **Follow Example Creation Guidelines** for comprehensive examples
- **Apply Unit Testing Guidelines** for thorough test coverage

## Coding Standards & Type Hints

### Core Standards
- Follow PEP 8 style guide for Python code
- Use 4-space indentation (no tabs)
- **Type hints required**: `def func(x: int) -> str:` 
- Use docstrings for all public modules, classes, and functions
- **Always use f-strings**: `f"Value: {var}"` not `"Value: " + str(var)`

### Modern Type Hints (PEP 604)
```python
# ✅ CORRECT - Modern syntax
def process_data(items: list[str], config: dict[str, int] | None = None) -> str | None:
    return f"Processed {len(items)} items"

# ❌ AVOID - Old syntax
from typing import Dict, List, Optional, Union
def process_data(items: List[str], config: Optional[Dict[str, int]] = None) -> Union[str, None]:
    return "Processed " + str(len(items)) + " items"
```

### Linting & Formatting
- **MUST RUN**: `uv run ruff check . && uv run ruff format .` before commits
- Line length limit: 140 characters (configured in pyproject.toml)
- Auto-fix with: `uv run ruff check --fix .`

## KISS/YAGNI Design Principles

**KISS (Keep It Simple, Stupid)** & **YAGNI (You Aren't Gonna Need It)**: Balance engineering rigor with practical simplicity.

### **AI Decision-Making Guidelines**
```
🎯 **START SIMPLE, EVOLVE THOUGHTFULLY**

For design decisions, AI coders should:
1. **Default to simplest solution** that meets current requirements
2. **Document complexity trade-offs** when proposing alternatives  
3. **Present options** when multiple approaches have merit
4. **Justify complexity** only when immediate needs require it

🤖 **AI CAN DECIDE** (choose simplest):
- Data structure choice (dict vs class vs dataclass)
- Function organization (single file vs module split)
- Error handling level (basic vs comprehensive)
- Documentation depth (minimal vs extensive)

👤 **PRESENT TO HUMAN** (let them choose):
- Architecture patterns (monolith vs microservices)
- Framework choices (custom vs third-party)
- Performance optimizations (simple vs complex)
- Extensibility mechanisms (hardcoded vs configurable)

⚖️ **COMPLEXITY JUSTIFICATION TEMPLATE**:
"Proposing [complex solution] over [simple solution] because:
- Current requirement: [specific need]
- Simple approach limitation: [concrete issue]
- Complexity benefit: [measurable advantage]
- Alternative: [let human decide vs simpler approach]"
```

### **Common Over-Engineering Patterns to Avoid**
```
❌ AVOID (unless specifically needed):
- Abstract base classes for single implementations
- Configuration systems for hardcoded values
- Generic solutions for specific problems
- Premature performance optimizations
- Complex inheritance hierarchies
- Over-flexible APIs with many parameters
- Caching systems without proven performance needs
- Event systems for simple function calls

✅ PREFER (start here):
- Concrete implementations that work
- Hardcoded values that can be extracted later
- Specific solutions for specific problems
- Simple, readable code first
- Composition over inheritance
- Simple function signatures
- Direct computation until performance matters
- Direct function calls for simple interactions
```

### **Incremental Complexity Strategy**
```
📈 **EVOLUTION PATH** (add complexity only when needed):

Phase 1: Hardcoded → Phase 2: Configurable → Phase 3: Extensible

Example:
Phase 1: `return "Hello, World!"`
Phase 2: `return f"Hello, {name}!"`
Phase 3: `return formatter.format(greeting_template, name)`

🔄 **WHEN TO EVOLVE**:
- Phase 1→2: When second use case appears
- Phase 2→3: When third different pattern emerges
- Never evolve: If usage remains stable
```

## Best Practices and Patterns
- Use dataclasses or Pydantic models for data structures
- Prefer composition over inheritance
- Use async/await for I/O operations
- Follow SOLID principles
- Use dependency injection where appropriate
- Implement proper error handling with custom exceptions
- **Start with simplest solution that works**
- **Add complexity only when requirements demand it**

## Error Handling Standards
```
Every error message must follow this template:
"[What failed]: [Why it failed]. [What user can do]. [Available alternatives]"

Example:
"Dana module 'math_utils' not found: File does not exist in search paths. 
Check module name spelling or verify file exists. 
Available modules: simple_math, string_utils"

Requirements:
- Handle all invalid inputs gracefully
- Include context about what was attempted
- Provide actionable suggestions for resolution
- Test error paths as thoroughly as success paths
```

## Temporary Files & Project Structure
- **ALL temporary files go in `tmp/` directory**
- Never create test files in project root
- Use meaningful prefixes: `tmp_test_`, `tmp_debug_`
- Core framework code: `dana/`
- Tests: `tests/` (matching source structure)
- Examples: `examples/`
- Documentation: `docs/`

## Context-Aware Development Guide

### When Working on Dana Code
- **🎯 ALWAYS create `.na` test files** for Dana functionality (not `.py` files)
- **🎯 Use `dana filename.na`** as the primary execution method
- Test with existing `.na` files in `examples/dana/`
- Use Dana runtime for execution testing in Python when needed
- Validate against grammar in `dana/core/lang/parser/dana_grammar.lark`
- **Use `log()` for examples/testing output** (preferred for color coding)
- Test Dana code in REPL: `dana` or `uv run python -m dana.core.repl.repl`
- Check AST output: Enable debug logging in transformer
- Run through pytest: Copy `test_dana_files.py` to test directory

### When Working on Agent Framework
- Test with agent examples in `examples/02_core_concepts/`
- Use capability mixins from `dana/common/mixins/`
- Follow resource patterns in `dana/common/resource/`

### When Working on Common Utilities
- Keep utilities generic and reusable
- Document performance implications
- Use appropriate design patterns
- Implement proper error handling

## Common Tasks Quick Guide
- **Adding new Dana function**: See `dana/core/stdlib/`
- **Creating agent capability**: Inherit from `dana/frameworks/agent/capability/`
- **Adding LLM integration**: Use `dana/integrations/llm/`

## Common Methods and Utilities
- **Use standard Python logging**: `import logging; logger = logging.getLogger(__name__)`
- Use configuration from `dana.common.config`
- Use graph operations from `dana.common.graph`
- Use IO utilities from `dana.common.io`

## Testing & Security Essentials
- **Prefer `.na` (Dana) test files** over `.py` for Dana-specific functionality
- Write unit tests for all new code (pytest automatically discovers `test_*.na` files)
- Test coverage above 80%
- **Never commit API keys or secrets**
- Use environment variables for configuration
- Validate all inputs

## Dana Test File Guidelines
- **Create `test_*.na` files** for Dana functionality testing
- Use `log()` statements for test output and debugging (provides color coding)
- pytest automatically discovers and runs `.na` test files
- Run `.na` files directly: `dana test_example.na` or `uv run python -m dana.core.repl.dana test_example.na`

## Dana Execution Quick Guide
**Always prefer `.na` test files for Dana functionality testing**

### 📁 **Create `.na` Test Files**
```dana
# test_my_feature.na
log("🧪 Testing My Feature")

# Test basic functionality
result = my_function(5)
assert result == 10
log("✅ Basic test passed")

log("🎉 All tests passed!")
```

### 🏃 **Multiple Ways to Run `.na` Files**
```bash
# 1. Direct dana command (recommended)
dana test_my_feature.na

# 2. With debug output
dana --debug test_my_feature.na

# 3. Via Python module
uv run python -m dana.core.repl.dana test_my_feature.na

# 4. Interactive REPL for development
dana                                    # Start REPL
uv run python -m dana.core.repl.repl   # Direct REPL access

# 5. Through pytest (automatic discovery)
pytest tests/my_directory/test_dana_files.py -v  # Runs all test_*.na files
```

### ✅ **When to Use Each Method**
- **`.na` files**: For Dana-specific functionality, examples, and testing
- **`.py` files**: Only for Python-specific testing (imports, integrations)
- **pytest**: Automated testing and CI/CD pipelines
- **dana command**: Direct execution and development
- **REPL**: Interactive development and debugging

## Dana-Specific Debugging & Validation
- **Use `log()` for examples/testing output** (provides color coding and better debugging)
- **Prefer creating `.na` test files** over `.py` for Dana functionality
- Test Dana code in REPL: `uv run python -m dana.core.repl.repl`
- Check AST output: Enable debug logging in transformer
- Validate against grammar: `dana/core/lang/parser/dana_grammar.lark`
- Test with existing `.na` files in `examples/dana/`
- Execute `.na` files: `dana filename.na` or `uv run python -m dana.core.repl.dana filename.na`

## Security & Performance
- **Dana Runtime Security**: Never expose Dana runtime instances to untrusted code
- **LLM Resource Management**: Always use proper configuration management for model configuration
- Profile code for performance bottlenecks
- Cache expensive operations
- Handle memory management properly

## References
@file .gitignore
@file pyproject.toml
@file Makefile
@file README.md
