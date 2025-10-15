# Implementation Guides

## Quick Start

1. **Copy a template** from `templates/`
2. **Follow the guide** for your component type
3. **Refer to API docs** as needed
4. **Test your component**

## Templates

Start here - copy and modify:
- **[Resource Template](./templates/resource_template.py)** - For external capabilities
- **[Workflow Template](./templates/workflow_template.py)** - For orchestration logic
- **[Agent Template](./templates/agent_template.py)** - For agent composition

## Step-by-Step Guides

### Creating a Resource
1. Copy `templates/resource_template.py`
2. Replace `[PLACEHOLDER]` text
3. Implement your methods with `@tool_use` and `@observable`
4. Return consistent `DictParams` format
5. Add error handling
6. Write tests

**Key Points**:
- Make it domain-agnostic (reusable)
- Keep methods stateless
- Use clear PUBLIC_DESCRIPTION
- See [Resource Design Patterns](../design/resource_design_patterns.md)

**API Reference**: [Base Classes](../api/base_classes.md#baseresource) | [Decorators](../api/decorators.md)

---

### Creating a Workflow
1. Copy `templates/workflow_template.py`
2. Replace `[PLACEHOLDER]` text
3. Implement `_do_execute()` with validation
4. Use resources for external calls
5. Keep logic deterministic
6. Write tests

**Key Points**:
- Encode business logic
- Use `@validate_input` and `@validate_output`
- Compose with `|` operator
- See [Workflow Design Patterns](../design/workflow_design_patterns.md)

**API Reference**: [Base Classes](../api/base_classes.md#baseworkflow) | [Decorators](../api/decorators.md)

---

### Creating an Agent
1. **Design first** using [Agent Team Design Guide](../design/agent_team_design_guide.md)
2. Create required resources and workflows
3. Copy `templates/agent_template.py`
4. Replace `[PLACEHOLDER]` text
5. Compose with `.with_workflows()` and `.with_resources()`
6. Create identity in docstring or `.xml` file
7. Write tests

**Key Points**:
- Keep agent code minimal (configuration)
- Clear PUBLIC_DESCRIPTION + IDENTITY
- Compose existing capabilities
- See [Agent Design Patterns](../design/agent_design_patterns.md)

**API Reference**: [Base Classes](../api/base_classes.md#staragent)

---

## Testing

Basic test pattern:
```python
def test_my_component():
    component = MyComponent()
    result = component.method(param="test")
    assert result["success"] == True
    assert "result" in result
```

See `dana_agent/tests/` for comprehensive examples.

---

## Codebase Examples

**Resources**:
- `dana/lib/resources/conversation.py` - LLM-powered
- `dana/lib/resources/web_research/search.py` - External API

**Workflows**:
- `dana/lib/workflows/web_research.py` - Sequential & parallel
- `contrib/expert_interview/workflows/` - Phased orchestration

**Agents**:
- `dana/lib/agents/web_research.py` - Single specialist
- `dana/apps/dana/dana_agent.py` - Coordinator

---

## Entry Point Best Practices

### For Autonomous Behavior
```python
# ✅ Good - Full autonomy through STAR loop
result = agent.query(caller_message="research companies")
agent.converse(initial_message="research companies")
agent.research_companies()  # Magic function

# ❌ Bad - No autonomy, hardcoded workflow
result = agent.research_companies()  # Direct method call
```

### Magic Function Implementation
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

### Composition vs. Programmatic Access
```python
# For LLM tool selection (composition)
self.with_workflows(MyWorkflow(workflow_id="my-workflow"))
# LLM can choose to call "my-workflow" tool

# For programmatic use (direct instantiation)
workflow = MyWorkflow()
result = workflow.execute(params)
# Direct execution in code
```

## Common Issues

**Issue**: Method not callable by agent
**Solution**: Add `@tool_use` and `@observable` decorators

**Issue**: Validation error
**Solution**: Check `@validate_input` spec matches your parameters

**Issue**: Import errors
**Solution**: Ensure you're importing from correct module paths

**Issue**: Wrong entry point (no autonomy)
**Solution**: Use `query()` or `converse()` instead of direct method calls

**Issue**: Composition vs. programmatic confusion
**Solution**: Use `with_workflows()` for LLM tools, direct instantiation for code

**Issue**: Missing intuitive interface
**Solution**: Implement magic function with `__getattr__`

**Issue**: Async event loop conflicts
**Solution**: Use `await` in async context or mock data for demos

---

## Quick Reference

| Component | Base Class | Key Decorators | Must Implement |
|-----------|-----------|----------------|----------------|
| Resource | BaseResource | @tool_use, @observable | public methods |
| Workflow | BaseWorkflow | @validate_input, @validate_output | _do_execute() |
| Agent | STARAgent | none (uses composition) | __init__() |

---

See [Main Docs](../README.md) for full documentation structure.
