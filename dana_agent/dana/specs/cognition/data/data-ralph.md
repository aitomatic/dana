# Data Access - Implementation Spec

**Status: ✅ COMPLETE**

## Goal
Implement RLM-based access to external data sources for Dana agents. Enables querying large files (500K+ tokens) by having the LLM write Python code to explore them programmatically.

## Background
RLM (Recursive Language Model) treats large sources as external environments that the LLM interacts with via code, rather than stuffing everything into the context window.

## Demo

Run: `examples/cognition/data_rlm/query_large_codebase.py`

### Without RLM (The Problem)

```python
# WITHOUT RLM: Trying to query a 500K token codebase
from dana.common.llm import LLM

codebase = open("huge_codebase.txt").read()  # 500K tokens

llm = LLM()
response = llm.chat([
    {"role": "system", "content": "Answer questions about this codebase."},
    {"role": "user", "content": f"Codebase:\n{codebase}\n\nWhat functions handle auth?"}
])
# ❌ ERROR: Context length exceeded (500K > 128K limit)
# ❌ Even if it fit, you're paying for 500K input tokens every query
# ❌ No way to search, slice, or explore programmatically
```

### With RLM (The Solution)

```python
# WITH RLM: LLM writes Python to explore large documents
from dana.common.resource import RLMResource

data = RLMResource(file="codebase.md")
data.load_file("huge_codebase.txt")  # 500K+ tokens - stays external!

# Query it - LLM writes Python to search, not stuffing context
answer = data.query("What functions handle authentication?")
# ✅ Works with ANY size document
# ✅ LLM writes: re.findall(r'def.*auth', context) to search
# ✅ Only the ANSWER enters context, not the whole document
# ✅ Typically finds answer in 3-5 iterations

print(answer)
# → "Authentication is handled by login(), verify_token(),
#    and refresh_session() in src/auth/handlers.py..."
```

### What You'll See

The LLM iteratively writes Python code to explore:
```
Iteration 1: print(context[:3000])           # Peek at structure
Iteration 2: re.findall(r'def.*auth', ctx)   # Search for patterns
Iteration 3: context[45000:48000]            # Extract relevant section
Iteration 4: FINAL("Authentication is...")   # Return answer
```

## MVP Requirements

### 1. PythonSandbox (`dana_agent/dana/core/agent/components/python_sandbox.py`)

Safe Python execution environment for RLM pattern.

```python
class PythonSandbox:
    """Execute Python code with a context variable and llm_query function."""

    def __init__(self, llm_query_fn: Callable[[str, str], str] | None = None):
        self.namespace = {}  # Persists across executions
        self.llm_query_fn = llm_query_fn

    def execute(self, code: str, context: str) -> str:
        """
        Execute code with `context` variable available.
        Returns stdout (truncated to 10KB).

        Available in namespace:
        - context: str (the document text)
        - llm_query(prompt, text): sub-LLM call for semantic tasks
        - Safe modules: re, json, math, collections, itertools, functools
        """
```

Requirements:
- [x] Execute arbitrary Python code safely
- [x] Inject `context` variable with document text
- [x] Provide `llm_query(prompt, text)` function if llm_query_fn provided
- [x] Capture stdout, truncate to 10KB
- [x] Persist namespace variables across executions
- [x] Block dangerous operations (no os.system, subprocess, open for write, eval, exec)
- [x] Allow safe modules: re, json, math, collections, itertools, functools

### 2. RLMResource (`dana_agent/dana/common/resource/rlm_resource.py`)

Unified resource for MVP with query, append, load operations.

```python
class RLMResource(BaseResource):
    """RLM-backed resource for querying and writing to large context files."""

    def __init__(
        self,
        file: str = "context.md",
        llm_provider: str = "anthropic",
        llm_model: str = "claude-sonnet-4-20250514"
    ):
        ...

    @tool
    def query(self, question: str) -> str:
        """
        Query the context using RLM pattern.
        LLM writes Python code to search/analyze the context.
        Returns answer extracted via FINAL(answer) or FINAL_VAR(var_name).
        """

    @tool
    def append(self, content: str, category: str = "note") -> str:
        """Append content to file with timestamp."""

    @tool
    def load_file(self, path: str) -> str:
        """Load and append file contents to context."""
```

Requirements:
- [x] Initialize with file path, create if doesn't exist
- [x] `query()` implements RLM loop:
  - Send system prompt instructing LLM to write Python
  - Execute code in PythonSandbox
  - Feed output back to LLM
  - Repeat until FINAL(answer) or FINAL_VAR(var) detected
  - Max 20 iterations
- [x] `append()` adds timestamped entry to file
- [x] `load_file()` reads file and appends to context
- [x] Use dana.common.llm.LLM for LLM calls

### 3. System Prompt for RLM Query

```
You are an RLM agent with access to a Python REPL containing a large document.

Environment:
- `context`: str - The full document (may be very large, don't print it all)
- `llm_query(prompt, text)`: Query sub-LLM for semantic tasks (summarize, extract, etc.)
- Modules: re, json, math, collections, itertools

Strategies:
1. Peek: `print(context[:3000])` to see structure
2. Search: `re.findall(pattern, context)` to find sections
3. Slice: `context[start:end]` to extract portions
4. Sub-query: `result = llm_query("summarize", chunk)` for semantic work
5. Accumulate: Store results in variables (they persist)

Output Python code. When done, output ONE of:
- FINAL(your_answer_string)
- FINAL_VAR(variable_name)
```

### 4. Example (`examples/cognition/data_rlm/`)

- `query_large_codebase.py` - Demo querying a large codebase
- `sample_codebase.md` - Sample large document (500K+ simulated)

## Files Implemented

- `dana_agent/dana/core/agent/components/python_sandbox.py` ✅
- `dana_agent/dana/common/resource/rlm_resource.py` ✅
- `examples/cognition/data_rlm/` ✅

## Tests Required

Create `dana_agent/tests/unit/test_python_sandbox.py`:
- [x] test_basic_execution - print works
- [x] test_context_variable - context is accessible
- [x] test_context_slicing - can slice context
- [x] test_safe_modules_available - re, json, math work
- [x] test_namespace_persistence - variables persist across calls
- [x] test_llm_query_function - llm_query works when provided
- [x] test_output_truncation - long output truncated to 10KB
- [x] test_error_handling - errors captured in output
- [x] test_dangerous_builtins_blocked - eval, exec, open blocked
- [x] test_reset - reset clears namespace

Create `dana_agent/tests/unit/test_rlm_resource.py`:
- [x] test_init_creates_file - creates file if missing
- [x] test_append - adds timestamped content
- [x] test_load_file - ingests file contents
- [x] test_query_basic - returns answer for simple query

Run tests with: `cd dana_agent && uv run pytest tests/unit/test_python_sandbox.py tests/unit/test_rlm_resource.py -v`

## Success Criteria

1. All tests pass
2. PythonSandbox executes code with context variable
3. RLMResource.query() uses RLM pattern (LLM writes Python)
4. RLMResource.append() adds timestamped content
5. RLMResource.load_file() ingests files
6. Example runs and demonstrates querying a large document

## Before Marking Complete

- [x] Review code for KISS/YAGNI compliance
- [x] Simplify any overly complex implementations
- [x] Remove unnecessary abstractions
- [x] Ensure code is readable and maintainable

## When Complete

**You MUST run tests before marking complete:**
```bash
cd dana_agent && uv run pytest tests/unit/test_python_sandbox.py tests/unit/test_rlm_resource.py -v
```

Only if ALL tests pass, output exactly:
<promise>DATA ACCESS COMPLETE</promise>

## STARAgent Integration Status

### Current Integration
- ✅ RLMResource can be attached to STARAgent via `with_resources()`
- ✅ Agents can invoke `query()`, `append()`, `load_file()` as tools
- ✅ LTMemory uses RLMResource internally for large memory queries
- ✅ ContextBuilder supports RLMResource as queryable source
- ✅ PromptEngineer uses ContextBuilder for context assembly

## References

- PRD: [data-prd.md](./data-prd.md)
- Parent: [cognition overview](../overview.md)
