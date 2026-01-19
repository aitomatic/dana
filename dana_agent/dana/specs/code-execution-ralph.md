# Code Execution Resource - Implementation Spec

**Status: ⚠️ IN PROGRESS**

## Goal

Implement a secure, sandboxed Python code execution resource for agents that supports stateful execution, enforces safety limits, and integrates as a tool via `execute()` and `reset()`.

## Demo

### Without Code Execution Resource (The Problem)
Agents cannot run custom Python logic, forcing manual calculations or external scripts for analysis, transformations, and validation.

### With Code Execution Resource (The Solution)
Agents call `CodeExecutionResource.execute()` to run Python safely, capture output, and reuse state across calls, with clear errors and resource limits.

### What You'll See
- Returned stdout from valid code execution
- Clear error messages for syntax/runtime/timeout failures
- Stateful variables across calls until `reset()`

## MVP Requirements

- [ ] Implement `CodeExecutionResource` with `execute()` and `reset()` tool methods per spec
- [ ] Use existing `PythonSandbox` for in-process execution with namespace isolation
- [ ] Enforce timeout (default 5s) and max output size (default 10KB)
- [ ] Block dangerous builtins: `eval`, `exec`, `open`, `__import__`, `compile`, `input`, `breakpoint`
- [ ] Whitelist safe modules: `math`, `statistics`, `json`, `re`, `collections`, `itertools`, `functools`, `datetime`, `random`, `string`
- [ ] Support single-line and multi-line code blocks
- [ ] Return stdout on success; return error message on failure
- [ ] Preserve namespace across `execute()` calls
- [ ] Implement `reset()` to clear namespace and return confirmation
- [ ] Allow `allowed_modules` to extend the whitelist
- [ ] Integrate with `BaseResource` and tool registry (`@tool_use`)

Expected interface:
```python
class CodeExecutionResource(BaseResource):
    @tool_use
    def execute(self, code: str) -> str:
        ...

    @tool_use
    def reset(self) -> str:
        ...
```

## Files Implemented

- `dana/common/resource/code_execution_resource.py` ❌
- `dana/core/agent/components/python_sandbox.py` ❌
- `dana/core/resource/base_resource.py` ❌
- `dana/common/resource/__init__.py` ❌
- `dana/core/agent/star_agent.py` ❌
- `tests/unit/test_code_execution_resource.py` ❌
- `tests/live/test_code_execution_resource_live.py` ❌

## Tests Required

### Unit Tests
- [ ] Executes simple expression and returns stdout
- [ ] Executes multi-line code and preserves variables across calls
- [ ] Blocks `open()` and returns a clear error
- [ ] Blocks `__import__` and non-whitelisted module import
- [ ] Allows whitelisted module import (e.g., `statistics`)
- [ ] Respects timeout on infinite loop and returns timeout error
- [ ] Truncates output over max size
- [ ] `reset()` clears namespace and confirms reset

### End-to-End Test (Live)
- [ ] **Live test**: Agent's LLM invokes `CodeExecutionResource.execute()` and gets correct result
  - Create STARAgent with CodeExecutionResource attached
  - Send message: "Calculate 2 + 2 using Python code"
  - Agent's LLM should recognize and call `execute()` tool with code `print(2 + 2)`
  - Resource executes code and returns "4"
  - Agent receives result and includes "4" in final response
  - Verify response contains correct answer

Command to run tests:
```bash
# Unit tests
pytest tests/unit/test_code_execution_resource.py

# End-to-end live test (requires API keys)
pytest tests/live/test_code_execution_resource_live.py --live
```

## Success Criteria

1. `execute()` returns correct stdout for valid code in < 5s.
2. Dangerous builtins and non-whitelisted modules are blocked with clear errors.
3. Namespace persists across `execute()` calls and is cleared by `reset()`.
4. Output is truncated at max size without crashing.
5. **End-to-end**: Agent's LLM successfully invokes `execute()` tool, code executes, and agent receives correct result in response.

## Before Marking Complete

- [ ] All tests pass
- [ ] Code follows existing patterns
- [ ] No unnecessary complexity (KISS)
- [ ] No over-engineering (YAGNI)
- [ ] Code is documented where non-obvious

## When Complete

Run these commands to verify:
```bash
# Unit tests (must pass)
pytest tests/unit/test_code_execution_resource.py

# End-to-end live test (must pass with real LLM)
pytest tests/live/test_code_execution_resource_live.py --live
```

Only if ALL tests pass, write this line to the ralph.md file:
<promise>TASK COMPLETE</promise>

## References

- PRD: [code-execution-prd.md](./code-execution-prd.md)
