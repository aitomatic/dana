# Agent Interface Patterns

## Overview

This document catalogs proven patterns for designing intuitive, autonomous agent interfaces. These patterns ensure agents are both powerful (through STAR loop autonomy) and accessible (through natural interfaces).

## Core Principles

### 1. Autonomy Through STAR Loop
- **Principle**: Agents should use STAR loop for reasoning and tool selection
- **Why**: Enables adaptation, learning, and intelligent decision-making
- **Implementation**: Use `query()` or `converse()` entry points

### 2. Intuitive Interfaces
- **Principle**: Agent interfaces should be natural and easy to use
- **Why**: Reduces cognitive load and increases adoption
- **Implementation**: Magic functions, natural language, clear method names

### 3. Clear Entry Point Selection
- **Principle**: Different entry points for different use cases
- **Why**: Prevents confusion and ensures appropriate autonomy level
- **Implementation**: Document when to use each entry point

## Interface Patterns

### Pattern 1: Autonomous Entry Points

**Intent**: Provide interfaces that leverage full agent autonomy through STAR loop

**Problem**: Need natural ways to interact with agents while maintaining reasoning capability

**Structure**:
```python
# ✅ Good - Full autonomy through STAR loop
result = agent.query(caller_message="research companies")
agent.converse(initial_message="research companies")
agent.research_companies()  # Magic function

# ❌ Bad - No autonomy, hardcoded workflow
result = agent.research_companies()  # Direct method call
```

**Characteristics**:
- Uses STAR loop for reasoning and tool selection
- Agent can adapt strategy based on results
- LLM chooses which workflows/resources to use
- Natural language interface

**When to Use**:
- User-facing interfaces
- Interactive applications
- When you want agent autonomy
- Complex, adaptive tasks

**Examples**:
```python
# Programmatic with response
result = agent.query(caller_message="research coffee companies in Đắk Lắk")

# Interactive conversation
agent.converse(initial_message="research coffee companies in Đắk Lắk")

# Magic function (calls converse)
agent.research_coffee_companies()
```

**Anti-patterns**:
- Hardcoded workflow execution
- Bypassing STAR loop
- No LLM reasoning
- Inflexible interfaces

---

### Pattern 2: Magic Function Interface

**Intent**: Convert method calls to natural language for intuitive agent interaction

**Problem**: Complex `query(caller_message="...")` syntax is not user-friendly

**Structure**:
```python
def __getattr__(self, name: str):
    """
    Magic function: Convert unknown method calls to natural language and call converse.

    Examples:
        agent.hi_how_are_you() -> converse("hi how are you")
        agent.research_coffee_companies() -> converse("research coffee companies")
        agent.find_exporters_in_dak_lak() -> converse("find exporters in dak lak")
    """
    def magic_method(*args, **kwargs):
        # Convert method name to natural language
        natural_language = name.replace("_", " ").strip()

        # Add any positional arguments as additional context
        if args:
            args_str = " ".join(str(arg) for arg in args)
            natural_language += f" {args_str}"

        # Add any keyword arguments as additional context
        if kwargs:
            kwargs_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
            natural_language += f" {kwargs_str}"

        # Call converse with the natural language message
        return self.converse(initial_message=natural_language)

    return magic_method
```

**Characteristics**:
- Intuitive method names: `agent.research_coffee_companies()`
- Natural language conversion: `research_coffee_companies` → `"research coffee companies"`
- Argument support: `agent.find_exporters_in("Đắk Lắk")` → `"find exporters in Đắk Lắk"`
- Interactive conversation: Calls `converse()` for user interaction

**When to Use**:
- User-facing agent interfaces
- Interactive applications
- When you want natural method names
- Educational or demo purposes

**Examples**:
```python
# All of these work and start interactive conversations:
agent.hi_how_are_you()                    # -> converse("hi how are you")
agent.research_coffee_companies()         # -> converse("research coffee companies")
agent.find_exporters_in_dak_lak()         # -> converse("find exporters in dak lak")
agent.search_companies_in_province("Gia Lai") # -> converse("search companies in province Gia Lai")
```

**Anti-patterns**:
- Not implementing `__getattr__`
- Complex method signatures
- Non-intuitive naming
- Bypassing conversation interface

---

### Pattern 3: Entry Point Selection

**Intent**: Choose the right entry point for the right use case

**Problem**: Different use cases require different levels of autonomy and interaction

**Structure**:
```python
# For programmatic use with response
result = agent.query(caller_message="research companies")
# Returns: {"response": "...", "tool_calls": [...], "reasoning": "..."}

# For interactive conversation
agent.converse(initial_message="research companies")
# Starts: Interactive conversation loop

# For natural method calls (magic function)
agent.research_companies()
# Converts to: converse("research companies")

# For direct workflow execution (use sparingly)
workflow = MyWorkflow()
result = workflow.execute(params)
# Bypasses: STAR loop, no autonomy
```

**When to Use Each**:

| Use Case | Entry Point | Why |
|----------|-------------|-----|
| **User Interface** | `converse()` | Interactive, natural |
| **API Integration** | `query()` | Programmatic, structured response |
| **Natural Method Calls** | Magic function | Intuitive, discoverable |
| **Direct Execution** | Workflow.execute() | Deterministic, no LLM reasoning |

**Anti-patterns**:
- Using wrong entry point for use case
- Bypassing autonomy when you need it
- Using autonomy when you need determinism
- Not documenting entry point choices

---

### Pattern 4: Composition vs. Programmatic Access

**Intent**: Clear separation between LLM tool selection and programmatic execution

**Problem**: Confusion about when to use `with_workflows()` vs. direct instantiation

**Structure**:
```python
# For LLM tool selection (composition)
self.with_workflows(
    MyWorkflow(workflow_id="my-workflow"),
    AnotherWorkflow(workflow_id="another-workflow")
)
# LLM can choose to call "my-workflow" or "another-workflow" tools

# For programmatic use (direct instantiation)
workflow = MyWorkflow()
result = workflow.execute(params)
# Direct execution in code, no LLM involvement
```

**When to Use Each**:

| Scenario | Approach | Example |
|----------|----------|---------|
| **LLM selects workflow** | `with_workflows()` | Agent chooses which tool to use |
| **Programmatic execution** | Direct instantiation | Code calls specific workflow |
| **Agent composition** | `with_workflows()` | Agent has access to tools |
| **Workflow orchestration** | Direct instantiation | Workflow calls other workflows |

**Anti-patterns**:
- Assuming `with_workflows()` gives programmatic access
- Using direct instantiation for LLM tool selection
- Not understanding the difference
- Mixing patterns inappropriately

---

## Implementation Guidelines

### 1. Always Implement Magic Function
```python
def __getattr__(self, name: str):
    def magic_method(*args, **kwargs):
        natural_language = name.replace("_", " ").strip()
        # Add args/kwargs to message
        return self.converse(initial_message=natural_language)
    return magic_method
```

### 2. Document Entry Points
```python
class MyAgent(STARAgent):
    """
    MyAgent provides multiple entry points:

    - query(caller_message="...") - Programmatic with response
    - converse(initial_message="...") - Interactive conversation
    - natural_method_name() - Magic function (calls converse)
    """
```

### 3. Choose Appropriate Autonomy Level
```python
# High autonomy - use STAR loop
agent.query("research companies")

# Low autonomy - direct execution
workflow = ResearchWorkflow()
result = workflow.execute(provinces=["Đắk Lắk"])
```

### 4. Test All Entry Points
```python
def test_agent_interfaces():
    agent = MyAgent()

    # Test programmatic
    result = agent.query(caller_message="test")
    assert "response" in result

    # Test magic function
    # (This will start conversation - test in interactive mode)
    # agent.test_method()
```

## Common Pitfalls

### 1. Wrong Entry Point (No Autonomy)
**Problem**: Using hardcoded methods that bypass STAR loop
**Solution**: Use `query()` or `converse()` for autonomous behavior

### 2. Missing Magic Function
**Problem**: Complex, non-intuitive interfaces
**Solution**: Implement `__getattr__` for natural method calls

### 3. Composition Confusion
**Problem**: Assuming `with_workflows()` gives programmatic access
**Solution**: Use composition for LLM tools, direct instantiation for code

### 4. Inconsistent Interface
**Problem**: Different entry points for similar use cases
**Solution**: Document and standardize entry point usage

## Related Documents

- [Agent Design Patterns](./agent_design_patterns.md) - Agent architecture patterns
- [Agent Team Design Guide](./agent_team_design_guide.md) - Complete design methodology
- [Implementation Guide](../implementation/README.md) - Step-by-step implementation
