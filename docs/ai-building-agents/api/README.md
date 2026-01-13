# Dana API Reference

## Core API Documentation

- **[Base Classes](./base_classes.md)** - BaseResource, BaseWorkflow, STARAgent
- **[Decorators](./decorators.md)** - @tool_use, @observable, @validate_input/output
- **[LLM Integration](./llm_integration.md)** - LLM class usage (see examples in codebase)
- **[Validation](./validation.md)** - Validation system (see decorators.md)

## Quick Reference

### Creating a Resource
```python
from dana.core.resource.base_resource import BaseResource
from dana.common.protocols.war import tool_use
from dana.common.observable import observable

class MyResource(BaseResource):
    @tool_use
    @observable
    def my_method(self, param: str) -> dict:
        return {"success": True, "result": param}
```

### Creating a Workflow
```python
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input

class MyWorkflow(BaseWorkflow):
    @validate_input(param={"required": True, "type": str})
    def _do_execute(self, **kwargs):
        return {"result": kwargs["param"]}
```

### Creating an Agent
```python
from dana.core.agent.star_agent import STARAgent

class MyAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="my-agent", **kwargs)
        self.with_workflows(...).with_resources(...)
```

## Best Learning Path

1. Read [Base Classes](./base_classes.md)
2. Read [Decorators](./decorators.md)
3. Study codebase examples
4. Use [Templates](../implementation/templates/)
