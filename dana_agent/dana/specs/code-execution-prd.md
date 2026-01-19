# Code Execution Resource - Product Requirements Document

## Overview

The Code Execution Resource provides agents with the ability to execute Python code in a secure sandboxed environment. This enables agents to perform computational tasks, data analysis, transformations, and other programmatic operations while maintaining safety and resource limits.

| Aspect | Description |
|--------|-------------|
| Nature | Secure code execution capability |
| Execution Model | Sandboxed Python interpreter |
| Security | Restricted builtins, whitelisted modules, optional process isolation |
| Use Cases | Data processing, calculations, transformations, analysis |

## Problem Statement

Dana agents currently lack a general-purpose mechanism to execute Python code. While `RLMResource` uses code execution internally for document querying, there is no standalone resource that agents can use to:

- Perform calculations and data transformations
- Execute custom algorithms
- Process data programmatically
- Run computational workflows
- Test code snippets

Agents need a secure, controlled way to execute code that:
- Prevents dangerous operations (file system access, network calls, system commands)
- Enforces resource limits (time, memory, output size)
- Provides clear error handling and feedback
- Supports both one-off execution and stateful sessions

## Why This Matters

1. **Capability Gap**: Agents cannot perform computational tasks that require code execution beyond what's built into resources.

2. **Flexibility**: Enables agents to handle tasks that require custom logic or algorithms not available through existing resources.

3. **Data Processing**: Allows agents to transform, analyze, and process data programmatically.

4. **Testing & Validation**: Agents can test code snippets, validate logic, and verify calculations.

5. **Educational**: Agents can demonstrate code execution and explain results interactively.

6. **Composability**: Works alongside other resources (e.g., RLMResource for querying, CodeExecutionResource for processing).

## User Stories

### Story 1: Data Analysis
> As a user, I want my agent to analyze a dataset by writing and executing Python code, so I can get insights without manually writing scripts.

### Story 2: Calculations
> As a user, I want my agent to perform complex calculations or transformations on data I provide, executing the code in a safe environment.

### Story 3: Code Testing
> As a developer, I want my agent to test code snippets I provide, executing them safely and reporting results.

### Story 4: Stateful Execution
> As a user, I want my agent to maintain state across multiple code executions, so I can build up results incrementally.

### Story 5: Secure Execution
> As a security-conscious user, I want code execution to be sandboxed so malicious code cannot access my file system or network.

## Proposed Solution

### Architecture

```
User: "Calculate the standard deviation of [1, 2, 3, 4, 5]"
     │
     ▼
STARAgent._think()
     │
     ▼
LLM sees CodeExecutionResource.execute() tool
     │
     ▼
LLM calls: CodeExecutionResource.execute(
    code="import statistics; print(statistics.stdev([1, 2, 3, 4, 5]))"
)
     │
     ▼
CodeExecutionResource
  ├── Validates code (syntax check)
  ├── Applies security restrictions
  ├── Executes in PythonSandbox
  │   ├── Restricted builtins (no eval, exec, open, etc.)
  │   ├── Whitelisted modules (math, statistics, json, etc.)
  │   ├── Timeout enforcement
  │   └── Output capture
  └── Returns result
     │
     ▼
STARAgent receives: "1.5811388300841898"
     │
     ▼
Continue STAR loop
```

### Core Components

1. **CodeExecutionResource** (`dana/common/resource/code_execution_resource.py`)
   - Resource interface exposing `execute()` and `reset()` methods
   - Configuration for security level, timeouts, resource limits
   - Integration with PythonSandbox or process-based sandbox

2. **PythonSandbox** (existing, `dana/core/agent/components/python_sandbox.py`)
   - Soft sandbox: restricted builtins, whitelisted modules
   - In-process execution with namespace isolation
   - Output capture and truncation

3. **ProcessSandbox** (optional, future enhancement)
   - Hard sandbox: process isolation
   - Resource limits (CPU, memory, time)
   - Network restrictions
   - Filesystem restrictions

## Requirements

### Functional Requirements

#### FR-1: Code Execution
- **FR-1.1**: Execute Python code strings provided by the agent
- **FR-1.2**: Support both single-line and multi-line code blocks
- **FR-1.3**: Return stdout output from code execution
- **FR-1.4**: Capture and return error messages on execution failure
- **FR-1.5**: Support stateful execution (variables persist across calls)

#### FR-2: Security Restrictions
- **FR-2.1**: Block dangerous builtins: `eval`, `exec`, `open`, `__import__`, `compile`, `input`, `breakpoint`
- **FR-2.2**: Whitelist safe modules: `math`, `statistics`, `json`, `re`, `collections`, `itertools`, `functools`, `datetime`, `random`, `string`
- **FR-2.3**: Prevent file system writes
- **FR-2.4**: Prevent network access (in soft sandbox)
- **FR-2.5**: Prevent subprocess execution
- **FR-2.6**: Block system command execution

#### FR-3: Resource Limits
- **FR-3.1**: Enforce execution timeout (default: 5 seconds, configurable)
- **FR-3.2**: Limit output size (default: 10KB, configurable)
- **FR-3.3**: Limit memory usage (future: with process isolation)
- **FR-3.4**: Limit CPU time (future: with process isolation)

#### FR-4: State Management
- **FR-4.1**: Maintain namespace across multiple `execute()` calls
- **FR-4.2**: Provide `reset()` method to clear namespace
- **FR-4.3**: Support session-based isolation (optional)

#### FR-5: Error Handling
- **FR-5.1**: Catch and report syntax errors
- **FR-5.2**: Catch and report runtime errors
- **FR-5.3**: Handle timeout exceptions gracefully
- **FR-5.4**: Provide clear error messages to the agent

### Non-Functional Requirements

#### NFR-1: Security
- **NFR-1.1**: No sandbox escapes in adversarial testing
- **NFR-1.2**: Code cannot access host file system (except through explicit resource methods)
- **NFR-1.3**: Code cannot make network requests (in soft sandbox)
- **NFR-1.4**: Code cannot execute system commands

#### NFR-2: Performance
- **NFR-2.1**: Code execution should complete in < 5 seconds for typical tasks
- **NFR-2.2**: Overhead from sandbox should be < 10ms per execution
- **NFR-2.3**: Support concurrent executions (future: with process isolation)

#### NFR-3: Usability
- **NFR-3.1**: Clear, actionable error messages
- **NFR-3.2**: Output should be human-readable
- **NFR-3.3**: Resource should be easy to configure and use

#### NFR-4: Reliability
- **NFR-4.1**: Handle malformed code gracefully
- **NFR-4.2**: Recover from execution errors without crashing
- **NFR-4.3**: Maintain sandbox state across errors

## API Design

### CodeExecutionResource

```python
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource

class CodeExecutionResource(BaseResource):
    """Secure Python code execution resource for agents."""
    
    def __init__(
        self,
        timeout: float = 5.0,
        max_output_size: int = 10 * 1024,  # 10KB
        allowed_modules: list[str] | None = None,
        session_id: str | None = None,
        resource_id: str = "code-execution",
        **kwargs,
    ):
        """
        Initialize code execution resource.
        
        Args:
            timeout: Maximum execution time in seconds
            max_output_size: Maximum output size in bytes
            allowed_modules: Additional modules to allow (beyond defaults)
            session_id: Optional session ID for namespace isolation
            resource_id: Resource identifier
        """
        super().__init__(resource_type="code-execution", **kwargs)
        # ... initialization ...
    
    @tool_use
    def execute(self, code: str) -> str:
        """
        Execute Python code in a secure sandbox.
        
        Args:
            code: Python code to execute
            
        Returns:
            stdout output from code execution, or error message
        """
        # ... implementation ...
    
    @tool_use
    def reset(self) -> str:
        """
        Reset the execution namespace, clearing all variables.
        
        Returns:
            Confirmation message
        """
        # ... implementation ...
```

### Usage Example

```python
from dana.common.resource import CodeExecutionResource
from dana.core.agent import STARAgent

# Create agent with code execution capability
agent = STARAgent()
agent.with_resources(CodeExecutionResource())

# Agent can now execute code
response = agent.run("Calculate the factorial of 10 using Python code")
# Agent will call CodeExecutionResource.execute() internally
```

## Security Model

### Soft Sandbox (MVP)

The initial implementation uses a soft sandbox approach similar to `PythonSandbox`:

1. **Restricted Builtins**: Only safe builtins are available
   - Allowed: `print`, `len`, `range`, `str`, `int`, `float`, `list`, `dict`, `set`, etc.
   - Blocked: `eval`, `exec`, `open`, `__import__`, `compile`, `input`, `breakpoint`

2. **Whitelisted Modules**: Only safe modules can be imported
   - Default: `math`, `statistics`, `json`, `re`, `collections`, `itertools`, `functools`, `datetime`, `random`, `string`
   - Configurable via `allowed_modules` parameter

3. **Namespace Isolation**: Code runs in a controlled namespace
   - Variables persist across calls within a session
   - No access to global Python environment
   - No access to host file system or network

4. **Output Limits**: Truncate output to prevent resource exhaustion

5. **Timeout**: Kill execution after timeout to prevent infinite loops

### Hard Sandbox (Future Enhancement)

For stronger security, a process-based sandbox can be added:

1. **Process Isolation**: Code runs in a separate subprocess
2. **Resource Limits**: Enforce CPU, memory, and time limits via OS mechanisms
3. **Network Restrictions**: Block network access at OS level
4. **Filesystem Restrictions**: Read-only or temp-only filesystem access
5. **Container Support**: Optional Docker container execution

## Success Metrics

1. **Correctness**: Code executes correctly for valid Python code (95%+ success rate)
2. **Security**: Zero sandbox escapes in adversarial testing
3. **Performance**: Average execution time < 1 second for typical tasks
4. **Usability**: Agents successfully use resource in 90%+ of appropriate scenarios
5. **Error Handling**: Clear error messages in 100% of failure cases

## Scope

### In MVP

- ✅ Soft sandbox execution using PythonSandbox
- ✅ Restricted builtins and whitelisted modules
- ✅ Timeout and output size limits
- ✅ Stateful execution (namespace persistence)
- ✅ Basic error handling
- ✅ `execute()` and `reset()` methods
- ✅ Integration with STARAgent via `with_resources()`

### Out of MVP (Future)

- ❌ Process-based isolation
- ❌ Memory and CPU limits (requires process isolation)
- ❌ Network restrictions at OS level
- ❌ Container-based execution
- ❌ Support for other languages (JavaScript, etc.)
- ❌ Code validation/linting before execution
- ❌ Execution history/audit logging
- ❌ Resource usage metrics and monitoring
- ❌ Concurrent execution support

## Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Sandbox escape | High | Low | Restricted builtins, whitelisted modules, extensive testing |
| Infinite loops | Medium | Medium | Timeout enforcement, iteration limits |
| Resource exhaustion | Medium | Low | Output size limits, timeout limits |
| Malicious code execution | High | Low | Security restrictions, process isolation (future) |
| Poor error messages | Low | Medium | Comprehensive error handling, clear messaging |
| Performance overhead | Low | Low | Efficient sandbox implementation, minimal overhead |

## Demo

When Code Execution Resource MVP is complete, we can demonstrate:

```python
from dana.common.resource import CodeExecutionResource
from dana.core.agent import STARAgent

# Create agent with code execution
agent = STARAgent()
agent.with_resources(CodeExecutionResource(timeout=5.0))

# Agent executes code for calculations
response = agent.run("""
Calculate the standard deviation of these numbers: [23, 45, 67, 89, 12, 34, 56, 78, 90, 11]
Use Python code to do the calculation.
""")
# Agent calls CodeExecutionResource.execute() with:
# code = "import statistics; print(statistics.stdev([23, 45, 67, 89, 12, 34, 56, 78, 90, 11]))"
# Returns: "26.1234567890..."

# Agent executes code for data transformation
response = agent.run("""
I have a list of temperatures in Celsius: [0, 25, 37, 100]
Convert them to Fahrenheit using the formula: F = (C * 9/5) + 32
""")
# Agent calls CodeExecutionResource.execute() with conversion code
# Returns converted temperatures

# Stateful execution
response = agent.run("Store the number 42 in a variable called 'answer'")
response = agent.run("Multiply 'answer' by 2 and print the result")
# Second call uses the variable from the first call
```

**Demo narrative**: "Watch the agent execute Python code safely to perform calculations, transformations, and analysis. The code runs in a secure sandbox with no access to your file system or network."

## Integration Points

### With STARAgent

```python
agent = STARAgent()
agent.with_resources(CodeExecutionResource())
# Agent can now call execute() and reset() as tools
```

### With Other Resources

CodeExecutionResource can work alongside other resources:

```python
agent = STARAgent()
agent.with_resources(
    RLMResource(file="data.md"),  # For querying large documents
    CodeExecutionResource(),        # For executing code
)
```

### With Workflows

Code execution can be part of workflows:

```python
# Workflow: Analyze data
# 1. Query data using RLMResource
# 2. Process results using CodeExecutionResource
# 3. Format output
```

## Testing Strategy

### Unit Tests

- Test code execution with various Python constructs
- Test security restrictions (attempts to use blocked builtins/modules)
- Test timeout handling
- Test output truncation
- Test stateful execution
- Test error handling

### Integration Tests

- Test with STARAgent integration
- Test concurrent execution (if supported)
- Test resource limits

### Security Tests

- Adversarial testing: attempts to escape sandbox
- Test blocked operations (file access, network, subprocess)
- Test resource exhaustion attacks
- Test infinite loop handling

## References

- Implementation spec: [code-execution-ralph.md](./code-execution-ralph.md) (to be created)
- Existing PythonSandbox: `dana/core/agent/components/python_sandbox.py`
- Existing RLMResource: `dana/common/resource/rlm_resource.py`
- Base Resource: `dana/core/resource/base_resource.py`

<promise>TASK COMPLETE</promise>