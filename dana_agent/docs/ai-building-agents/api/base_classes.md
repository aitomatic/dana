# Base Classes API Reference

## Overview

Dana provides three foundational base classes for building agent systems. This document provides the API reference for these classes based on the actual implementation.

---

## BaseResource

**File**: `dana/core/resource/base_resource.py`

**Purpose**: Base class for all resources that provide external capabilities to agents and workflows.

### Class Definition

```python
class BaseResource(BaseWAR, ResourceProtocol):
    """
    Base class for resources providing external capabilities.

    Resources should:
    - Be domain-agnostic (reusable across domains)
    - Be stateless (no state between calls)
    - Provide focused capabilities via methods
    - Use @tool_use and @observable decorators
    - Return consistent DictParams format
    """
```

### Constructor

```python
def __init__(
    self,
    resource_type: str | None = None,
    resource_id: str | None = None,
    auto_register: bool = True,
    registry=None,
    **kwargs
):
    """
    Initialize a resource.

    Args:
        resource_type: Type identifier (defaults to class name)
        resource_id: Unique resource ID (defaults to None)
        auto_register: Auto-register with global registry (default True)
        registry: Specific registry (defaults to global registry)
        **kwargs: Additional arguments for parent classes
    """
```

### Key Properties

```python
@property
def resource_id(self) -> str:
    """Get the resource unique ID"""

@resource_id.setter
def resource_id(self, value: str):
    """Set the resource ID"""

@property
def resource_type(self) -> str:
    """Get the resource type (usually class name)"""
```

### Registry Methods

```python
def unregister_resource(self) -> bool:
    """
    Unregister this resource from the registry.

    Returns:
        True if successfully unregistered
    """
```

### Implementation Pattern

```python
from dana.core.resource.base_resource import BaseResource
from dana.common.protocols.war import tool_use
from dana.common.observable import observable
from dana.common.protocols import DictParams

class MyResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Description of what this resource does.
    This appears in agent system prompts.
    </PUBLIC_DESCRIPTION>
    """

    def __init__(self, **kwargs):
        super().__init__(resource_id="my-resource", **kwargs)
        # Initialize any internal clients/state

    @tool_use
    @observable
    def my_method(self, param: str, **kwargs) -> DictParams:
        """
        Method documentation.

        Args:
            param: Parameter description

        Returns:
            Dictionary with results
        """
        try:
            result = self._do_work(param)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

---

## BaseWorkflow

**File**: `dana/core/workflow/base_workflow.py`

**Purpose**: Base class for all workflows that orchestrate deterministic multi-step processes.

### Class Definition

```python
class BaseWorkflow(BaseWA, WorkflowProtocol):
    """
    Base class for workflows providing deterministic orchestration.

    Workflows should:
    - Encode deterministic logic and business rules
    - Be composable (via | operator)
    - Validate inputs and outputs
    - Use resources for external capabilities
    - Be domain-specific (focused on particular use case)
    """
```

### Constructor

```python
def __init__(
    self,
    args_transform: str | None = None,
    pre_callable: Callable[[DictParams], None] | None = None,
    post_callable: Callable[[DictParams], None] | None = None,
    workflow_type: str | None = None,
    workflow_id: str | None = None,
    auto_register: bool = True,
    registry=None,
    composite_left: BaseWorkflow | None = None,
    composite_right: BaseWorkflow | None = None,
    **kwargs,
):
    """
    Initialize a workflow.

    Args:
        args_transform: Declarative input/output mapping string
            Format: "input_mappings -> output_name"
            Example: "url=result.url, query=query -> search_result"
        pre_callable: Function to transform inputs before execution
        post_callable: Function to transform outputs after execution
        workflow_type: Type identifier (defaults to class name)
        workflow_id: Unique workflow ID
        auto_register: Auto-register with global registry
        registry: Specific registry
        composite_left: Left workflow for composition (internal)
        composite_right: Right workflow for composition (internal)
    """
```

### Key Methods

```python
@tool_use
@observable
def execute(self, **kwargs) -> DictParams:
    """
    Execute the workflow with pre/post-processing.

    Args:
        **kwargs: Input parameters

    Returns:
        Dictionary with results (includes "result" key)
    """

def _do_execute(self, **kwargs) -> DictParams:
    """
    Override this method to implement workflow logic.

    Args:
        **kwargs: Input parameters

    Returns:
        Dictionary with execution results
    """
```

### Composition

```python
def __or__(self, other: BaseWorkflow | Callable) -> BaseWorkflow:
    """
    Compose workflows using | operator.

    Args:
        other: Another workflow or callable

    Returns:
        Composite workflow that executes both in sequence

    Example:
        workflow = Workflow1() | Workflow2() | Workflow3()
    """
```

### Key Properties

```python
@property
def workflow_id(self) -> str:
    """Get the workflow unique ID"""

@workflow_id.setter
def workflow_id(self, value: str):
    """Set the workflow ID"""

@property
def public_description(self) -> str:
    """Get the public description from docstring"""
```

### Implementation Pattern

```python
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.common.protocols import DictParams

class MyWorkflow(BaseWorkflow):
    """
    Brief description of what this workflow does.

    USE FOR: When to use this workflow
    STEPS: Step1 → Step2 → Step3
    """

    def __init__(self, **kwargs):
        super().__init__(workflow_id="my-workflow", **kwargs)
        # Initialize any resources needed
        self.resource = MyResource()

    @validate_input(
        param1={"required": True, "type": str},
        param2={"type": int, "default": 10},
    )
    @validate_output(
        success={"required": True, "type": bool},
        result={"required": True},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """Implementation of workflow logic"""
        param1 = kwargs["param1"]
        param2 = kwargs["param2"]

        # Execute workflow steps
        step1_result = self.resource.method1(param1)
        step2_result = self.resource.method2(step1_result, param2)

        return {
            "success": True,
            "result": step2_result
        }
```

---

## STARAgent

**File**: `dana/core/agent/star_agent.py`

**Purpose**: Base class for all agents following the See-Think-Act-Reflect pattern.

### Class Definition

```python
class STARAgent:
    """
    STAR Agent: See-Think-Act-Reflect agent.

    Agents should:
    - Have clear PUBLIC_DESCRIPTION (for other agents/users)
    - Have clear PRIVATE_IDENTITY (for self-guidance)
    - Compose workflows, resources, and sub-agents
    - Be focused and specialized
    - Use minimal code (mostly configuration)
    """
```

### Constructor

```python
def __init__(
    self,
    agent_type: str,
    agent_id: str | None = None,
    llm_provider: str = "anthropic",
    model: str | None = None,
    **kwargs
):
    """
    Initialize a STAR agent.

    Args:
        agent_type: Type identifier for this agent
        agent_id: Unique agent ID (defaults to agent_type)
        llm_provider: LLM provider ("anthropic", "openai", etc.)
        model: Specific model to use
        **kwargs: Additional arguments
    """
```

### Composition Methods

```python
def with_agents(self, *agents) -> 'STARAgent':
    """
    Add sub-agents that this agent can delegate to.

    Args:
        *agents: Variable number of agent instances

    Returns:
        self (for method chaining)

    Example:
        agent.with_agents(
            SubAgent1(),
            SubAgent2()
        )
    """

def with_workflows(self, *workflows) -> 'STARAgent':
    """
    Add workflows that this agent can execute.

    Args:
        *workflows: Variable number of workflow instances

    Returns:
        self (for method chaining)
    """

def with_resources(self, *resources) -> 'STARAgent':
    """
    Add resources that this agent can use.

    Args:
        *resources: Variable number of resource instances

    Returns:
        self (for method chaining)
    """

def with_notifiable(self, *notifiables) -> 'STARAgent':
    """
    Add objects to notify of agent events.

    Args:
        *notifiables: Objects implementing notification interface

    Returns:
        self (for method chaining)
    """
```

### Query Methods

```python
def query(self, message: str | None = None, **kwargs) -> DictParams:
    """
    Send a query to the agent.

    Args:
        message: The user/caller message
        **kwargs: Additional context

    Returns:
        Dictionary with response and metadata
    """
```

### Properties

```python
@property
def agent_type(self) -> str:
    """Get the agent type"""

@property
def object_id(self) -> str:
    """Get the agent unique ID"""

@property
def available_resources(self) -> list:
    """Get list of available resources"""

@property
def available_agents(self) -> list:
    """Get list of available sub-agents"""

def get_state(self) -> dict:
    """Get current agent state including resources and workflows"""
```

### Implementation Pattern

```python
from dana.core.agent.star_agent import STARAgent

class MyAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    Description of what this agent does.
    Visible to other agents and users.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    You are [agent role].
    Your principles: ...
    Your approach: ...
    </PRIVATE_IDENTITY>
    """

    def __init__(self, agent_id: str | None = None, **kwargs):
        super().__init__(
            agent_type="my-agent-type",
            agent_id=agent_id or "my-agent",
            **kwargs
        )

        # Compose capabilities
        self.with_workflows(
            MyWorkflow1(workflow_id="workflow-1"),
            MyWorkflow2(workflow_id="workflow-2"),
        ).with_resources(
            MyResource1(resource_id="resource-1"),
            MyResource2(resource_id="resource-2"),
        )
```

**Alternative**: Identity can be in separate `.prt` file:
```python
# my_agent.prt file
<PUBLIC_DESCRIPTION>
...
</PUBLIC_DESCRIPTION>

<PRIVATE_IDENTITY>
...
</PRIVATE_IDENTITY>

<THINKING_RULES>
...
</THINKING_RULES>

<CONFIGURATION_INFO>
...
</CONFIGURATION_INFO>
```

---

## Common Patterns

### Fluent Builder Pattern

All agents use method chaining for composition:

```python
agent = (
    MyAgent()
    .with_agents(SubAgent())
    .with_workflows(Workflow1(), Workflow2())
    .with_resources(Resource1(), Resource2())
    .with_notifiable(logger)
)
```

### Consistent Return Format

All methods return `DictParams` (dictionary) with consistent structure:

```python
{
    "success": bool,           # Always present
    "result": any,             # Main result data
    "error": str,              # Present if success=False
    "metadata": dict,          # Optional additional info
}
```

### Error Handling

All classes should handle errors gracefully:

```python
try:
    result = perform_operation()
    return {"success": True, "result": result}
except Exception as e:
    return {"success": False, "error": str(e)}
```

---

## Related Documentation

- [Decorators Reference](./decorators.md)
- [Validation Reference](./validation.md)
- [LLM Integration](./llm_integration.md)
- [Implementation Guides](../implementation/)

---

**Location in codebase**:
- `dana/core/resource/base_resource.py`
- `dana/core/workflow/base_workflow.py`
- `dana/core/agent/star_agent.py`
