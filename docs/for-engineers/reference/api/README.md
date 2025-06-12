# OpenDXA API Reference

Complete reference documentation for OpenDXA framework components and the Dana programming language.

## 🚀 Quick Start

### Dana Language (Recommended Entry Point)
```python
# Import Dana - the main programming interface
import opendxa.dana as dana

# Execute Dana code
result = dana.eval('''
# AI-powered data analysis
data = [1, 4, 7, 2, 9, 3, 8, 5]
analysis = reason(f"Analyze this dataset: {data}")
log(f"Analysis: {analysis}")
analysis
''')

if result.success:
    print(f"Result: {result.result}")
    print(f"Output: {result.output}")
```

### OpenDXA Framework Components
```python
# Import OpenDXA common utilities
from opendxa.common import DXA_LOGGER, LLMResource, ConfigLoader

# Configure logging
DXA_LOGGER.configure(level=DXA_LOGGER.INFO, console=True)

# Load configuration
config = ConfigLoader().get_default_config()

# Create resources
llm = LLMResource()
```

## 📖 API Documentation

### Core Platform APIs

| Document | Description | Key Components |
|----------|-------------|----------------|
| **[Dana Sandbox](dana-sandbox.md)** | Main Dana execution API | `DanaSandbox`, `ExecutionResult`, `dana.run()`, `dana.eval()` |
| **[OpenDXA Common](opendxa-common.md)** | Shared framework utilities | Resources, mixins, configuration, logging |

### Dana Language Reference

| Document | Description | Key Topics |
|----------|-------------|------------|
| **[Core Functions](core-functions.md)** | Essential Dana functions | `reason()`, `log()`, `print()`, `log_level()` |
| **[Built-in Functions](built-in-functions.md)** | Pythonic built-in functions | `len()`, `sum()`, `max()`, `min()`, `abs()`, `round()` |
| **[Type System](type-system.md)** | Type hints and type checking | Variable types, function signatures, validation |
| **[Scoping System](scoping.md)** | Variable scopes and security | `private:`, `public:`, `system:`, `local:` |

### Advanced Features

| Document | Description | Key Topics |
|----------|-------------|------------|
| **[POET Decorators](poet-decorators.md)** | Function enhancement decorators | `@poet()` for Python, `@poet` for Dana, runtime `poet()` |
| **[Function Calling](function-calling.md)** | Function calls and imports | Dana→Dana, Dana→Python, Python→Dana |
| **[Sandbox Security](sandbox-security.md)** | Security model and restrictions | Sandboxing, context isolation, safety |

## Quick Start

### Basic Dana Program with Type Hints
```dana
# Variable type annotations
user_data: dict = {"name": "Alice", "age": 25}
temperature: float = 98.6
is_active: bool = true

# Function with typed parameters and return type
def analyze_user_data(data: dict, threshold: float) -> dict:
 # Use core functions with proper types
 log(f"Analyzing data for user: {data['name']}", "info")

 # AI reasoning with type hints
 analysis: str = reason(f"Analyze user data: {data}")

 # Return structured result
 return {
 "user": data["name"],
 "analysis": analysis,
 "temperature_ok": temperature < threshold,
 "status": "complete"
 }

# Call function with type safety
result: dict = analyze_user_data(user_data, 100.0)
print("Analysis result:", result)
```

## 📖 Function Reference Quick Lookup

### Core Functions
- `reason(prompt: str, options: dict = {}) -> str` - LLM-powered reasoning
- **`print(*args: any) -> None`** - Print output with space separation
- `log(message: str, level: str = "info") -> None` - Log messages
- `log_level(level: str) -> None` - Set global log level

### POET Decorators
- **`@poet(domain="...", timeout=30.0, retries=3)`** - Python function enhancement
- **`@poet(...)`** - Dana function enhancement
- **`poet(func_name, args, **config)`** - Runtime function enhancement

### Built-in Functions
- `len(obj: any) -> int` - Get length of collections
- `sum(iterable: list) -> any` - Sum numeric values
- **`max(*args: any) -> any`** - Find maximum value
- **`min(*args: any) -> any`** - Find minimum value
- `abs(x: any) -> any` - Absolute value
- `round(x: float, digits: int = 0) -> any` - Round numbers

### Type System
- Basic Types: `int`, `float`, `str`, `bool`, `list`, `dict`, `tuple`, `set`, `None`, `any`
- Function Signatures: `def func(param: type) -> return_type:`
- Variable Annotations: `variable: type = value`

### Scoping
- `private:` - Private scope (function-local, secure)
- `public:` - Public scope (shared across contexts)
- `system:` - System scope (runtime configuration)
- `local:` - Local scope (default for function parameters)

## Search by Use Case

### Function Enhancement and Reliability
- [POET Decorators: Python enhancement](poet-decorators.md#python-poet-decorator) - `@poet()` for automatic optimization
- [POET Decorators: Dana enhancement](poet-decorators.md#dana-poet-decorator) - `@poet` for domain intelligence
- [POET Decorators: Runtime enhancement](poet-decorators.md#runtime-poet-function-dana) - `poet()` for dynamic enhancement

### AI and Reasoning
- [Core Functions: `reason()`](core-functions.md#reason) - LLM integration and AI reasoning
- [OpenDXA Common: LLMResource](opendxa-common.md#llmresource) - Direct LLM resource access
- [Type System: AI function signatures](type-system.md#ai-functions) - Type safety for AI operations

### Data Processing
- [Built-in Functions: Collections](built-in-functions.md#collection-functions) - `len()`, `sum()`, `max()`, `min()`
- [Type System: Data types](type-system.md#data-types) - `list`, `dict`, `tuple`, `set`
- [Dana Sandbox: Batch Processing](dana-sandbox.md#batch-processing) - Process multiple files

### Logging and Debugging
- [Core Functions: Logging](core-functions.md#logging-functions) - `log()`, `log_level()`
- [OpenDXA Common: DXALogger](opendxa-common.md#dxalogger) - Advanced logging features
- [Dana Sandbox: Debug Mode](dana-sandbox.md#debug-mode) - Execution debugging

### Security and Isolation
- [Scoping System](scoping.md) - Variable scope security model
- [Sandbox Security](sandbox-security.md) - Runtime security and isolation
- [Dana Sandbox: Security Considerations](dana-sandbox.md#security-considerations) - Safe code execution

### Integration and Extension
- [Function Calling](function-calling.md) - Dana↔Python integration
- [OpenDXA Common: Mixins](opendxa-common.md#mixins) - Reusable functionality
- [OpenDXA Common: Tool Integration](opendxa-common.md#tool-integration) - AI tool development

## 🔧 Development Workflow

### 1. Basic Dana Development
```python
import opendxa.dana as dana

# Development workflow
sandbox = dana.DanaSandbox(debug=True)

# Iterative development
code_v1 = "x = 10\nresult = x * 2"
result1 = sandbox.eval(code_v1)

# Build on previous results
code_v2 = "y = result + 5\nfinal = y"
result2 = sandbox.eval(code_v2)

print(f"Final result: {result2.result}")
```

### 2. Application Development
```python
from opendxa.common import Loggable, LLMResource
import opendxa.dana as dana

class DataAnalyzer(Loggable):
    def __init__(self):
        super().__init__()
        self.sandbox = dana.DanaSandbox()
        self.llm = LLMResource()
    
    def analyze_dataset(self, data: list):
        self.info(f"Analyzing dataset with {len(data)} items")
        
        # Use Dana for structured analysis
        dana_code = f'''
        dataset = {data}
        statistics = {{
            "mean": sum(dataset) / len(dataset),
            "max": max(dataset),
            "min": min(dataset),
            "size": len(dataset)
        }}
        
        # AI-powered insights
        insight = reason(f"Provide insights for dataset statistics: {{statistics}}")
        
        {{
            "statistics": statistics,
            "ai_insight": insight
        }}
        '''
        
        result = self.sandbox.eval(dana_code)
        
        if result.success:
            self.info("Analysis completed successfully")
            return result.result
        else:
            self.error(f"Analysis failed: {result.error}")
            return None

# Usage
analyzer = DataAnalyzer()
analysis = analyzer.analyze_dataset([1, 5, 3, 8, 2, 9, 4, 7])
```

### 3. Production Integration
```python
from fastapi import FastAPI, HTTPException
from opendxa.common import DXA_LOGGER, OpenDXAError
import opendxa.dana as dana

app = FastAPI()

# Configure production logging
DXA_LOGGER.configure(level=DXA_LOGGER.INFO, console=True)

# Global Dana sandbox for request processing
dana_sandbox = dana.DanaSandbox()

@app.post("/process")
async def process_data(data: dict):
    """Production endpoint using Dana for data processing."""
    try:
        DXA_LOGGER.info(f"Processing request with {len(data)} keys")
        
        # Use Dana for processing logic
        dana_code = f'''
        input_data = {data}
        
        # Process data with AI reasoning
        analysis = reason(f"Process and analyze: {{input_data}}")
        
        # Log processing
        log(f"Processed data with keys: {{list(input_data.keys())}}")
        
        {{
            "processed_data": input_data,
            "analysis": analysis,
            "status": "completed"
        }}
        '''
        
        result = dana_sandbox.eval(dana_code)
        
        if result.success:
            DXA_LOGGER.info("Request processed successfully")
            return result.result
        else:
            DXA_LOGGER.error(f"Dana processing failed: {result.error}")
            raise HTTPException(status_code=500, detail="Processing failed")
            
    except OpenDXAError as e:
        DXA_LOGGER.error(f"OpenDXA error: {e}")
        raise HTTPException(status_code=500, detail="Service error")
```

## 📋 API Implementation Status

| Feature | Status | Documentation |
|---------|--------|---------------|
| Core Functions | ✅ Complete | [core-functions.md](core-functions.md) |
| POET Decorators | ✅ Complete | [poet-decorators.md](poet-decorators.md) |
| Built-in Functions | ✅ Complete | [built-in-functions.md](built-in-functions.md) |
| Type System | ✅ Complete | [type-system.md](type-system.md) |
| Scoping System | ✅ Complete | [scoping.md](scoping.md) |
| Function Calling | ✅ Complete | [function-calling.md](function-calling.md) |
| Sandbox Security | ✅ Complete | [sandbox-security.md](sandbox-security.md) |

## 🤝 Contributing

Found an error or want to improve the API documentation? See our [contribution guidelines](../../../for-contributors/README.md).

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>