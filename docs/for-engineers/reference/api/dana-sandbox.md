# Dana Sandbox API Reference

The Dana Sandbox is the primary public API for executing Dana code safely. It provides a clean, simple interface for running Dana files and evaluating code expressions.

## Quick Start

```python
# Import the Dana module
import opendxa.dana as dana

# Method 1: Convenience functions (recommended for simple use)
result = dana.run("my_program.na")
result = dana.eval("x = 10\ny = 20\nx + y")

# Method 2: DanaSandbox instance (recommended for advanced use)
sandbox = dana.DanaSandbox(debug=True)
result = sandbox.run("my_program.na")
result = sandbox.eval("x = 10\ny = 20\nx + y")
```

## Classes

### DanaSandbox

The main class for executing Dana code in a secure sandbox environment.

#### Constructor

```python
DanaSandbox(debug: bool = False, context: Optional[SandboxContext] = None)
```

**Parameters:**
- `debug` (bool): Enable debug logging output
- `context` (Optional[SandboxContext]): Custom execution context (creates default if None)

**Example:**
```python
import opendxa.dana as dana

# Basic sandbox
sandbox = dana.DanaSandbox()

# Debug sandbox with logging
debug_sandbox = dana.DanaSandbox(debug=True)

# Custom context sandbox
from opendxa.dana.sandbox.sandbox_context import SandboxContext
custom_context = SandboxContext()
custom_context.set("public:api_key", "secret-key")
sandbox = dana.DanaSandbox(context=custom_context)
```

#### Instance Methods

##### run(file_path)

Execute a Dana file from disk.

```python
run(file_path: Union[str, Path]) -> ExecutionResult
```

**Parameters:**
- `file_path` (str | Path): Path to the `.na` file to execute

**Returns:**
- `ExecutionResult`: Result object with success status and execution details

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `ValueError`: If the file doesn't have `.na` extension

**Example:**
```python
import opendxa.dana as dana

sandbox = dana.DanaSandbox()

# Execute a Dana file
result = sandbox.run("examples/basic.na")

if result.success:
    print(f"Program output: {result.output}")
    print(f"Final result: {result.result}")
else:
    print(f"Error: {result.error}")
```

##### eval(source_code, filename=None)

Evaluate Dana source code directly.

```python
eval(source_code: str, filename: Optional[str] = None) -> ExecutionResult
```

**Parameters:**
- `source_code` (str): Dana code to execute
- `filename` (Optional[str]): Optional filename for error reporting

**Returns:**
- `ExecutionResult`: Result object with success status and execution details

**Example:**
```python
import opendxa.dana as dana

sandbox = dana.DanaSandbox()

# Evaluate Dana code
result = sandbox.eval('''
# Simple calculation
x = 10
y = 20
result = x * y
log(f"Calculation: {x} * {y} = {result}")
result
''')

if result.success:
    print(f"Result: {result.result}")  # Output: 200
    print(f"Log output: {result.output}")
```

#### Class Methods

##### quick_run(file_path, debug=False, context=None)

Quick file execution without creating a sandbox instance.

```python
@classmethod
quick_run(
    cls, 
    file_path: Union[str, Path], 
    debug: bool = False, 
    context: Optional[SandboxContext] = None
) -> ExecutionResult
```

**Parameters:**
- `file_path` (str | Path): Path to the `.na` file to execute
- `debug` (bool): Enable debug logging
- `context` (Optional[SandboxContext]): Custom execution context

**Returns:**
- `ExecutionResult`: Result object with success status and execution details

**Example:**
```python
import opendxa.dana as dana

# Quick file execution
result = dana.DanaSandbox.quick_run("my_program.na", debug=True)
print(f"Success: {result.success}, Result: {result.result}")
```

##### quick_eval(source_code, filename=None, debug=False, context=None)

Quick code evaluation without creating a sandbox instance.

```python
@classmethod
quick_eval(
    cls,
    source_code: str,
    filename: Optional[str] = None,
    debug: bool = False,
    context: Optional[SandboxContext] = None
) -> ExecutionResult
```

**Parameters:**
- `source_code` (str): Dana code to execute
- `filename` (Optional[str]): Optional filename for error reporting
- `debug` (bool): Enable debug logging
- `context` (Optional[SandboxContext]): Custom execution context

**Returns:**
- `ExecutionResult`: Result object with success status and execution details

**Example:**
```python
import opendxa.dana as dana

# Quick code evaluation
result = dana.DanaSandbox.quick_eval("x = 42\nx * 2")
print(f"Result: {result.result}")  # Output: 84
```

### ExecutionResult

Result object returned by all Dana execution methods.

#### Attributes

```python
@dataclass
class ExecutionResult:
    success: bool                              # Whether execution succeeded
    result: Any = None                         # Final result value
    final_context: Optional[SandboxContext] = None  # Final execution context
    execution_time: float = 0.0               # Execution time in seconds
    error: Optional[Exception] = None         # Error if execution failed
    output: str = ""                          # Captured output from log() and print()
```

#### Methods

##### __str__()

Human-readable execution summary.

```python
def __str__(self) -> str
```

**Returns:**
- `str`: Summary of execution result

**Example:**
```python
import opendxa.dana as dana

result = dana.eval("x = 10\nx + 5")
print(str(result))  # Output: "Success: 15"

result = dana.eval("invalid syntax")
print(str(result))  # Output: "Error: [error details]"
```

## Convenience Functions

### dana.run(file_path, debug=False, context=None)

Convenience function for quick file execution.

```python
run = DanaSandbox.quick_run
```

**Example:**
```python
import opendxa.dana as dana

# These are equivalent:
result1 = dana.run("my_program.na")
result2 = dana.DanaSandbox.quick_run("my_program.na")
```

### dana.eval(source_code, filename=None, debug=False, context=None)

Convenience function for quick code evaluation.

```python
eval = DanaSandbox.quick_eval
```

**Example:**
```python
import opendxa.dana as dana

# These are equivalent:
result1 = dana.eval("2 + 2")
result2 = dana.DanaSandbox.quick_eval("2 + 2")
```

## Usage Patterns

### Basic Script Execution

```python
import opendxa.dana as dana

# Execute a Dana script
result = dana.run("scripts/data_analysis.na")

if result.success:
    print("Analysis complete!")
    print(f"Results: {result.result}")
    # Access final variable states
    user_data = result.final_context.get("public:user_data")
    print(f"Processed data: {user_data}")
else:
    print(f"Script failed: {result.error}")
```

### Interactive Code Evaluation

```python
import opendxa.dana as dana

# Create a persistent sandbox for multiple evaluations
sandbox = dana.DanaSandbox(debug=True)

# Set up initial data
setup_result = sandbox.eval('''
public:data = {"users": ["Alice", "Bob", "Charlie"], "scores": [95, 87, 92]}
private:api_key = "secret-key"
''')

# Perform analysis
analysis_result = sandbox.eval('''
# Analyze user scores
total_users = len(public:data["users"])
avg_score = sum(public:data["scores"]) / total_users

log(f"Analyzed {total_users} users")
log(f"Average score: {avg_score}")

analysis = reason(f"Analyze these user scores: {public:data}")
analysis
''')

if analysis_result.success:
    print(f"Analysis: {analysis_result.result}")
    print(f"Log output:\n{analysis_result.output}")
```

### Error Handling

```python
import opendxa.dana as dana

# Handle different types of errors
def safe_execute(code: str) -> None:
    result = dana.eval(code)
    
    if result.success:
        print(f"✓ Success: {result.result}")
    else:
        error = result.error
        
        # Handle specific error types
        if isinstance(error, FileNotFoundError):
            print("✗ File not found")
        elif isinstance(error, SyntaxError):
            print(f"✗ Syntax error: {error}")
        elif "NameError" in str(error):
            print("✗ Variable not defined")
        else:
            print(f"✗ Execution failed: {error}")

# Test different scenarios
safe_execute("x = 10\ny = 20\nx + y")  # Success
safe_execute("undefined_variable + 5")   # NameError
safe_execute("x = 10\nx +")             # Syntax error
```

### Working with Context

```python
import opendxa.dana as dana
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create custom context with pre-loaded data
context = SandboxContext()
context.set("public:config", {"api_url": "https://api.example.com", "timeout": 30})
context.set("private:credentials", {"token": "auth-token"})

# Use context in execution
sandbox = dana.DanaSandbox(context=context)

result = sandbox.eval('''
# Access pre-loaded configuration
api_url = public:config["api_url"]
timeout = public:config["timeout"]
token = private:credentials["token"]

log(f"Connecting to {api_url} with timeout {timeout}s")

# Simulate API call logic
connection_status = "connected"
connection_status
''')

print(f"Connection status: {result.result}")
```

### Batch Processing

```python
import opendxa.dana as dana
from pathlib import Path

def process_dana_files(directory: str) -> dict:
    """Process all .na files in a directory."""
    results = {}
    
    for file_path in Path(directory).glob("*.na"):
        print(f"Processing {file_path.name}...")
        
        result = dana.run(str(file_path))
        results[file_path.name] = {
            "success": result.success,
            "result": result.result,
            "error": str(result.error) if result.error else None
        }
    
    return results

# Process all Dana files in a directory
batch_results = process_dana_files("scripts/")

# Generate summary
successful = sum(1 for r in batch_results.values() if r["success"])
total = len(batch_results)
print(f"Processed {successful}/{total} files successfully")
```

## Security Considerations

### Sandbox Isolation

The Dana Sandbox provides security isolation for executing untrusted code:

```python
import opendxa.dana as dana

# Dana code runs in a secure sandbox
untrusted_code = '''
# This code cannot access the host system
private:data = "safe data"
result = len(private:data)
result
'''

result = dana.eval(untrusted_code)
# Safe to execute - sandbox prevents system access
```

### Context Security

Variables are isolated by scope:

```python
import opendxa.dana as dana

# Sensitive data in private scope
result = dana.eval('''
private:secret = "sensitive-data"
public:safe_data = "public-data"

# private: scope is isolated and secure
# public: scope can be shared between contexts
len(private:secret)
''')

# Access public data safely
public_data = result.final_context.get("public:safe_data")
# Cannot access private:secret from outside the sandbox
```

## Performance Tips

### Reuse Sandbox Instances

```python
import opendxa.dana as dana

# Efficient: Reuse sandbox for multiple operations
sandbox = dana.DanaSandbox()

for i in range(100):
    result = sandbox.eval(f"x = {i}\nx * 2")
    # Sandbox context is preserved between calls
```

### Minimize Context Creation

```python
import opendxa.dana as dana

# Efficient: Share context for related operations
sandbox = dana.DanaSandbox()

# Setup once
sandbox.eval("public:data = [1, 2, 3, 4, 5]")

# Multiple operations on same data
result1 = sandbox.eval("sum(public:data)")
result2 = sandbox.eval("max(public:data)")
result3 = sandbox.eval("len(public:data)")
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
import opendxa.dana as dana

app = FastAPI()

@app.post("/execute")
async def execute_dana_code(code: str):
    """Execute Dana code via REST API."""
    result = dana.eval(code)
    
    if result.success:
        return {
            "success": True,
            "result": result.result,
            "output": result.output
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Execution failed: {result.error}"
        )

@app.post("/analyze")
async def analyze_data(data: dict):
    """Analyze data using Dana reasoning."""
    dana_code = f'''
    public:input_data = {data}
    analysis = reason("Analyze this data: " + str(public:input_data))
    analysis
    '''
    
    result = dana.eval(dana_code)
    
    if result.success:
        return {"analysis": result.result}
    else:
        raise HTTPException(
            status_code=500,
            detail="Analysis failed"
        )
```

### Jupyter Notebook Integration

```python
# In a Jupyter notebook cell
import opendxa.dana as dana

# Create a persistent sandbox for the notebook session
%%python
notebook_sandbox = dana.DanaSandbox(debug=True)

# Dana code execution in notebook
%%python
result = notebook_sandbox.eval('''
# Data analysis in Dana
public:dataset = [1, 4, 7, 2, 9, 3, 8, 5, 6]
mean_value = sum(public:dataset) / len(public:dataset)

# AI-powered analysis
insight = reason(f"What insights can you provide about this dataset: {public:dataset}?")

log(f"Dataset mean: {mean_value}")
log(f"AI insight: {insight}")

{
    "mean": mean_value,
    "insight": insight,
    "dataset_size": len(public:dataset)
}
''')

print(f"Analysis complete: {result.result}")
print(f"Output:\n{result.output}")
```

## Troubleshooting

### Common Issues

**File Not Found Error:**
```python
# ❌ Incorrect
result = dana.run("nonexistent.na")

# ✅ Correct
from pathlib import Path
if Path("my_program.na").exists():
    result = dana.run("my_program.na")
else:
    print("File not found")
```

**Variable Scope Issues:**
```python
# ❌ Incorrect - variables lost between evaluations
result1 = dana.eval("x = 10")
result2 = dana.eval("y = x + 5")  # Error: x not defined

# ✅ Correct - use persistent sandbox
sandbox = dana.DanaSandbox()
result1 = sandbox.eval("x = 10")
result2 = sandbox.eval("y = x + 5")  # Works: x persists in context
```

**Syntax Errors:**
```python
# ❌ Incorrect
result = dana.eval("x = 10\ny = x +")  # Syntax error

# ✅ Correct - check result
result = dana.eval("x = 10\ny = x + 5")
if not result.success:
    print(f"Error: {result.error}")
```

### Debug Mode

Enable debug mode for detailed execution information:

```python
import opendxa.dana as dana

# Enable debug logging
sandbox = dana.DanaSandbox(debug=True)

result = sandbox.eval('''
x = 10
log("Processing data...")
y = x * 2
log(f"Result: {y}")
y
''')

# Debug output shows detailed execution flow
```

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 